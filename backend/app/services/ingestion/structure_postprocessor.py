"""StructurePostprocessor — turn per-page extractions into DB rows.

Walks a list of `PageExtraction`s (from `PageExtractor`) page by page,
maintaining a stack of currently-open sections. Each `structure_event`
pushes/pops the stack and creates a `BookSection` row.

Section boundaries within a page are resolved by matching each
`structure_event` to the corresponding `heading` block in the page's
block stream (boundary refinement — see `_split_page_by_events`).
Blocks before the matched heading are attributed to the previously
open section and extend its `page_end`; blocks from the matched heading
onward are attributed to the newly opened section. This prevents a
section that ends partway through a page from spilling the rest of
that page's content into the next section.

`figure` blocks have their bbox cropped from the rendered page image
(via an injected `crop_figure` callable) and stored as `BookFigure`
rows pointing to a PNG saved on disk.

Backward compatibility: every chunk we produce also gets a `clean_text`
rendering of its blocks so existing services that read `clean_text`
continue to work without modification.
"""
from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from sqlalchemy.orm import Session

from app.models.book import Book, BookChunk
from app.models.figure import BookFigure
from app.models.section import BookSection
from app.schemas.page_extraction import (
    Block,
    HeadingBlock,
    PageExtraction,
    StructureEvent,
    page_kind_is_chunkable,
)
from app.services.ingestion.token_counter import count_tokens

logger = logging.getLogger(__name__)


# Block kinds that are atomic (never merged with neighbors during chunking,
# unless they're tiny relative to the budget). Theorem and proof are kept
# adjacent where possible since splitting them across chunks loses context.
_ATOMIC_BLOCK_KINDS = {"definition", "theorem", "proof", "example", "equation"}

# Block kinds whose contents should not be turned into BookChunk text at all
# (figures and tables are referenced via BookFigure / future BookTable rows).
_SKIP_FOR_TEXT_KINDS = {"figure", "table"}


@dataclass
class _OpenSection:
    """Working state for a section currently on the stack."""

    row: BookSection
    level: int


@dataclass
class StructureProcessResult:
    """Summary of what was created during post-processing."""

    sections_created: int = 0
    chunks_created: int = 0
    figures_created: int = 0
    pages_processed: int = 0
    pages_skipped_unchunkable: int = 0
    low_confidence_pages: list[int] = field(default_factory=list)


class StructurePostprocessor:
    """Persist a stream of PageExtractions as BookSection / BookChunk / BookFigure rows."""

    def __init__(
        self,
        max_chunk_tokens: int = 800,
    ):
        self.max_chunk_tokens = max_chunk_tokens

    def process(
        self,
        db: Session,
        book_id: uuid.UUID,
        extractions: list[PageExtraction],
        crop_figure: Callable[[int, list[float]], bytes] | None = None,
        figures_dir: Path | None = None,
    ) -> StructureProcessResult:
        """Persist all rows for a book ingestion.

        Parameters
        ----------
        crop_figure
            Optional callable `(page_number, bbox) -> png_bytes`. When provided,
            figure blocks get their crops saved under `figures_dir`. When None,
            figure blocks still produce `BookFigure` rows with bbox metadata
            but no `image_url`.
        figures_dir
            Directory to write cropped figure PNGs into. Created if missing.
        """
        result = StructureProcessResult()
        section_stack: list[_OpenSection] = []
        sibling_counter: dict[uuid.UUID | None, int] = {}
        next_chunk_index = 0

        if figures_dir is not None:
            figures_dir.mkdir(parents=True, exist_ok=True)

        for page in extractions:
            result.pages_processed += 1
            if page.confidence < 0.5:
                result.low_confidence_pages.append(page.page)

            # Non-chunkable pages (frontmatter, TOC, references, ...) still
            # need their structure events recorded so any section starts
            # printed on them populate the section tree.
            if not page_kind_is_chunkable(page.page_kind):
                for event in page.structure_events:
                    section = self._open_section(
                        db=db,
                        book_id=book_id,
                        event=event,
                        page=page.page,
                        stack=section_stack,
                        sibling_counter=sibling_counter,
                    )
                    if section is not None:
                        result.sections_created += 1
                self._extend_section_page_end(section_stack, page.page)
                result.pages_skipped_unchunkable += 1
                continue

            # Chunkable page: split block stream at section boundaries, route
            # each slice to its proper section. Opens sections as a side effect.
            segments = self._split_page_by_events(
                db=db,
                book_id=book_id,
                page=page,
                stack=section_stack,
                sibling_counter=sibling_counter,
                result=result,
            )

            # Newly opened sections + ancestors get page_end bumped to this page.
            # (Sections popped during _split_page_by_events were already bumped
            # there if pre-heading blocks on this page belonged to them.)
            self._extend_section_page_end(section_stack, page.page)

            chunks_for_page: list[BookChunk] = []
            for section_row, blocks_slice in segments:
                if not blocks_slice:
                    continue
                chunks = self._chunks_from_blocks(
                    blocks=[b.model_dump() for b in blocks_slice],
                    book_id=book_id,
                    section=section_row,
                    page=page.page,
                    page_kind=page.page_kind,
                    confidence=page.confidence,
                    start_index=next_chunk_index,
                )
                for chunk in chunks:
                    db.add(chunk)
                if chunks:
                    db.flush()  # so figure rows below can FK chunk.id
                next_chunk_index += len(chunks)
                result.chunks_created += len(chunks)
                chunks_for_page.extend(chunks)

            if crop_figure is not None and figures_dir is not None:
                figs = self._save_figures(
                    db=db,
                    book_id=book_id,
                    page=page,
                    section=section_stack[-1].row if section_stack else None,
                    chunks=chunks_for_page,
                    crop_figure=crop_figure,
                    figures_dir=figures_dir,
                )
                result.figures_created += figs

        book = db.get(Book, book_id)
        if book:
            book.status = "ingested"

        db.commit()
        return result

    # --------------------------------------------------------------- boundary fix

    def _split_page_by_events(
        self,
        db: Session,
        book_id: uuid.UUID,
        page: PageExtraction,
        stack: list[_OpenSection],
        sibling_counter: dict[uuid.UUID | None, int],
        result: StructureProcessResult,
    ) -> list[tuple[BookSection | None, list[Block]]]:
        """Split a page's blocks at section-boundary headings.

        For each `structure_event` on the page, find the corresponding `heading`
        block in the page's block stream by normalized title match. The matched
        heading's index is the split point — blocks before it stay with the
        previously open section (and extend its `page_end` to this page); from
        the matched heading onward, blocks are attributed to the newly opened
        section. Events are processed in input order; once a heading is matched,
        the search for the next event starts after it.

        Side effects: opens new BookSection rows via `_open_section` (which
        also mutates `stack` and `sibling_counter`), and bumps the
        previously-deepest section's `page_end` when applicable.

        Returns a list of `(section, blocks_slice)` tuples in reading order,
        where `section` is None only when there is no chapter open yet (e.g.
        body content before the first chapter heading).
        """
        blocks: list[Block] = list(page.blocks)
        events: list[StructureEvent] = list(page.structure_events)

        # 1. Match each event to a heading-block index.
        matches: list[tuple[StructureEvent, int]] = []
        cursor = 0
        for ev in events:
            idx = _find_heading_index(blocks, ev, start=cursor)
            if idx is None:
                # The LLM said this section started on the page but no heading
                # block carries the title. Fall back to "from current cursor
                # onward" — same behavior as the legacy postprocessor for this
                # event, but still respects any earlier successful match.
                logger.warning(
                    "page %d: structure_event %r (%s) had no matching heading "
                    "block; falling back to cursor=%d",
                    page.page,
                    ev.title,
                    ev.kind,
                    cursor,
                )
                idx = cursor
            matches.append((ev, idx))
            cursor = idx + 1

        segments: list[tuple[BookSection | None, list[Block]]] = []

        if not matches:
            # No transitions on this page — every block belongs to whatever's
            # currently open at the top of the stack.
            if blocks:
                segments.append((stack[-1].row if stack else None, blocks))
            return segments

        # 2. Blocks before the first matched heading belong to the section
        #    currently on top of the stack (the section that's ending mid-page).
        first_idx = matches[0][1]
        if first_idx > 0:
            pre_section = stack[-1].row if stack else None
            if pre_section is not None:
                # Bump the closing section + its ancestors so their page_end
                # reflects that content on this page belongs to them.
                for entry in stack:
                    if entry.row.page_end is None or entry.row.page_end < page.page:
                        entry.row.page_end = page.page
            segments.append((pre_section, blocks[0:first_idx]))

        # 3. For each event, open the section, then take blocks from its
        #    heading index up to the next event's heading (or end of page).
        for i, (ev, idx) in enumerate(matches):
            section = self._open_section(
                db=db,
                book_id=book_id,
                event=ev,
                page=page.page,
                stack=stack,
                sibling_counter=sibling_counter,
            )
            if section is not None:
                result.sections_created += 1
            next_idx = matches[i + 1][1] if i + 1 < len(matches) else len(blocks)
            if idx < next_idx:
                segments.append((section, blocks[idx:next_idx]))

        return segments

    # ------------------------------------------------------------------ sections

    def _open_section(
        self,
        db: Session,
        book_id: uuid.UUID,
        event: StructureEvent,
        page: int,
        stack: list[_OpenSection],
        sibling_counter: dict[uuid.UUID | None, int],
    ) -> BookSection | None:
        """Open (or replace) a section at `event.level`, pop deeper levels off the stack."""
        level = event.level
        # Pop everything at the same or deeper level: a new chapter ends the
        # previous chapter and all its open sections.
        while stack and stack[-1].level >= level:
            stack.pop()

        parent_row = stack[-1].row if stack else None
        parent_id = parent_row.id if parent_row else None

        order_key = parent_id
        order_index = sibling_counter.get(order_key, 0)
        sibling_counter[order_key] = order_index + 1

        kind = self._kind_for_event(event)
        row = BookSection(
            book_id=book_id,
            parent_id=parent_id,
            level=level,
            order_index=order_index,
            kind=kind,
            number=event.number,
            title=event.title.strip(),
            page_start=page,
            page_end=page,
        )
        db.add(row)
        db.flush()  # need row.id to push onto the stack and FK from chunks

        stack.append(_OpenSection(row=row, level=level))
        return row

    @staticmethod
    def _kind_for_event(event: StructureEvent) -> str:
        mapping = {
            "chapter_start": "chapter",
            "section_start": "section",
            "subsection_start": "subsection",
            "appendix_start": "appendix",
            "references_start": "references",
            "index_start": "index",
        }
        return mapping.get(event.kind, "section")

    @staticmethod
    def _extend_section_page_end(stack: list[_OpenSection], page: int) -> None:
        for entry in stack:
            entry.row.page_end = page

    # ------------------------------------------------------------------ chunking

    def _chunks_from_blocks(
        self,
        blocks: list[dict],
        book_id: uuid.UUID,
        section: BookSection | None,
        page: int,
        page_kind: str,
        confidence: float,
        start_index: int,
    ) -> list[BookChunk]:
        """Group blocks into BookChunk rows respecting token budget + atomicity."""
        # First, pull out non-text blocks (figures/tables) — they don't contribute
        # to chunk text but we keep their position so figures can attach to the
        # surrounding chunk later.
        text_blocks = [b for b in blocks if b.get("kind") not in _SKIP_FOR_TEXT_KINDS]

        if not text_blocks:
            return []

        chunks: list[BookChunk] = []
        current_blocks: list[dict] = []
        current_text_parts: list[str] = []
        current_tokens = 0

        for blk in text_blocks:
            blk_text = self._render_block_text(blk)
            blk_tokens = count_tokens(blk_text) if blk_text else 0
            if not blk_text:
                continue

            atomic = blk.get("kind") in _ATOMIC_BLOCK_KINDS
            would_overflow = (
                current_blocks
                and current_tokens + blk_tokens > self.max_chunk_tokens
            )

            if would_overflow and not (atomic and current_tokens < self.max_chunk_tokens // 4):
                chunks.append(
                    self._build_chunk(
                        book_id=book_id,
                        section=section,
                        page=page,
                        page_kind=page_kind,
                        confidence=confidence,
                        chunk_index=start_index + len(chunks),
                        blocks=current_blocks,
                        text="\n\n".join(current_text_parts),
                    )
                )
                current_blocks = []
                current_text_parts = []
                current_tokens = 0

            current_blocks.append(blk)
            current_text_parts.append(blk_text)
            current_tokens += blk_tokens

        if current_blocks:
            chunks.append(
                self._build_chunk(
                    book_id=book_id,
                    section=section,
                    page=page,
                    page_kind=page_kind,
                    confidence=confidence,
                    chunk_index=start_index + len(chunks),
                    blocks=current_blocks,
                    text="\n\n".join(current_text_parts),
                )
            )

        return chunks

    @staticmethod
    def _build_chunk(
        book_id: uuid.UUID,
        section: BookSection | None,
        page: int,
        page_kind: str,
        confidence: float,
        chunk_index: int,
        blocks: list[dict],
        text: str,
    ) -> BookChunk:
        return BookChunk(
            book_id=book_id,
            chunk_index=chunk_index,
            chapter_title=_chapter_title_of(section),
            section_title=section.title if section else None,
            section_id=section.id if section else None,
            page_start=page,
            page_end=page,
            raw_text=text,
            clean_text=text,
            token_count=count_tokens(text),
            blocks=blocks,
            page_kind=page_kind,
            confidence=confidence,
        )

    @staticmethod
    def _render_block_text(blk: dict) -> str:
        """Render a typed block as plain markdown text for clean_text/raw_text."""
        kind = blk.get("kind")
        if kind == "heading":
            level = blk.get("level", 1)
            text = blk.get("text", "")
            return f"{'#' * max(1, min(6, level))} {text}".strip()
        if kind == "paragraph":
            return blk.get("markdown", "").strip()
        if kind == "definition":
            label = blk.get("label")
            body = blk.get("markdown", "").strip()
            return f"**{label}.** {body}" if label else f"**Definition.** {body}"
        if kind == "theorem":
            label = blk.get("label")
            subkind = blk.get("subkind", "theorem").capitalize()
            body = blk.get("markdown", "").strip()
            header = label or subkind
            return f"**{header}.** {body}"
        if kind == "proof":
            return f"*Proof.* {blk.get('markdown', '').strip()}"
        if kind == "example":
            label = blk.get("label") or "Example"
            return f"**{label}.** {blk.get('markdown', '').strip()}"
        if kind == "remark":
            return f"*Remark.* {blk.get('markdown', '').strip()}"
        if kind == "equation":
            label = blk.get("label")
            latex = blk.get("latex", "")
            tag = f" \\tag{{{label}}}" if label else ""
            return f"$$\n{latex}{tag}\n$$"
        if kind == "list":
            ordered = blk.get("ordered", False)
            items = blk.get("items", []) or []
            if ordered:
                return "\n".join(f"{i + 1}. {it}" for i, it in enumerate(items))
            return "\n".join(f"- {it}" for it in items)
        if kind == "exercise":
            num = blk.get("number")
            body = blk.get("markdown", "").strip()
            return f"**Exercise {num}.** {body}" if num else f"**Exercise.** {body}"
        return ""

    # ------------------------------------------------------------------ figures

    def _save_figures(
        self,
        db: Session,
        book_id: uuid.UUID,
        page: PageExtraction,
        section: BookSection | None,
        chunks: list[BookChunk],
        crop_figure: Callable[[int, list[float]], bytes],
        figures_dir: Path,
    ) -> int:
        """Crop each figure block on this page and persist BookFigure rows."""
        count = 0
        # Best-effort attach to the last chunk on the page so figures sit near
        # their surrounding text in queries.
        attach_chunk_id = chunks[-1].id if chunks else None

        for idx, blk in enumerate(page.blocks):
            if blk.kind != "figure":
                continue
            try:
                png = crop_figure(page.page, blk.bbox)
            except Exception as exc:
                logger.warning(
                    "figure crop failed page=%d bbox=%s: %s", page.page, blk.bbox, exc
                )
                continue

            filename = f"p{page.page:04d}_f{idx + 1}.png"
            path = figures_dir / filename
            path.write_bytes(png)

            row = BookFigure(
                book_id=book_id,
                section_id=section.id if section else None,
                chunk_id=attach_chunk_id,
                page=page.page,
                image_url=str(path),
                caption=blk.caption,
                bbox_json={"bbox": blk.bbox},
            )
            db.add(row)
            count += 1
        return count


# --- Heading <-> StructureEvent matching ------------------------------------

# Strip leading "Chapter N", "Section N.M", "Appendix A:", etc.
_TITLE_PREFIX_RE = re.compile(
    r"^(chapter|section|subsection|appendix|part)\s+[\w.\-]*[:.\-]?\s*",
    re.IGNORECASE,
)
# Strip leading numbering like "2.", "3.1.4", "2 ", "(IV)" before the title.
_LEADING_NUMBER_RE = re.compile(
    r"^[\(]?[\dIVXLCM]+(\.[\dIVXLCM]+)*[\.\:\)\-\s]+",
    re.IGNORECASE,
)


def _normalize_title(text: str) -> str:
    """Lowercase, strip leading numbering / prefixes, collapse punctuation+whitespace."""
    if not text:
        return ""
    s = text.lower().strip()
    s = _TITLE_PREFIX_RE.sub("", s)
    s = _LEADING_NUMBER_RE.sub("", s)
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _find_heading_index(
    blocks: list[Block], event: StructureEvent, start: int = 0
) -> int | None:
    """Find the index of a `heading` block (>= `start`) that matches `event`.

    Match strategy, in order:
      1. Exact match on normalized title text.
      2. One side's tokens are a subset of the other's (e.g. event title
         'Examples' vs heading text '2 Examples' — after normalization both
         reduce to 'examples', so this case usually falls under (1), but
         this catches things like 'KL Divergence' vs 'Kullback-Leibler
         Divergence' or appendix titles where the LLM dropped or added a word).

    Returns None when no heading block from `start` onward looks like this event.
    """
    # The `event.number` field (e.g. '2' for "2 Examples") is intentionally
    # ignored: _normalize_title strips leading numbering from the heading
    # text on the other side, so both reduce to the same normalized form.
    target = _normalize_title(event.title or "")
    if not target:
        return None

    target_tokens = set(target.split())

    # Pass 1: exact normalized equality.
    for i in range(start, len(blocks)):
        b = blocks[i]
        if not isinstance(b, HeadingBlock):
            continue
        if _normalize_title(b.text) == target:
            return i

    # Pass 2: token containment (each side has >= 2 tokens to avoid trivial matches).
    if len(target_tokens) >= 2:
        for i in range(start, len(blocks)):
            b = blocks[i]
            if not isinstance(b, HeadingBlock):
                continue
            other_tokens = set(_normalize_title(b.text).split())
            if not other_tokens:
                continue
            if target_tokens.issubset(other_tokens) or other_tokens.issubset(target_tokens):
                return i

    return None


def _chapter_title_of(section: BookSection | None) -> str | None:
    """Walk up the section tree to find the level-1 (chapter) title."""
    cur = section
    while cur is not None:
        if cur.level == 1:
            return cur.title
        # parent is loaded lazily; attribute access triggers a query if not loaded.
        # In our flow `section_stack` keeps the parent objects alive in-session.
        if cur.parent_id is None:
            break
        # Defer to relationship via session; cur.parent isn't mapped on the model
        # so we look it up by id. Cheap because parent is already in the session.
        # Use object_session to avoid passing db down here.
        from sqlalchemy.orm import object_session

        sess = object_session(cur)
        if sess is None:
            return cur.title  # best effort
        cur = sess.get(BookSection, cur.parent_id)
    return None


__all__ = ["StructurePostprocessor", "StructureProcessResult"]
