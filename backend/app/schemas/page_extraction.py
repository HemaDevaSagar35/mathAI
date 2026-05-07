"""Pydantic schemas for vision-based per-page extraction (B14 v2).

Mirrors the JSON contract produced by the page_extract.md prompt. Used to
validate LLM output before it is persisted as BookSection / BookChunk /
BookFigure rows.
"""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PageKind = Literal[
    "frontmatter",
    "toc",
    "preface",
    "body",
    "exercises",
    "appendix",
    "references",
    "index",
    "back_matter",
]

StructureEventKind = Literal[
    "chapter_start",
    "section_start",
    "subsection_start",
    "appendix_start",
    "references_start",
    "index_start",
]

BlockKind = Literal[
    "heading",
    "paragraph",
    "definition",
    "theorem",
    "proof",
    "example",
    "remark",
    "equation",
    "figure",
    "table",
    "list",
    "exercise",
]

TheoremSubkind = Literal["theorem", "lemma", "corollary", "proposition"]


class StructureEvent(BaseModel):
    """A structural transition (chapter/section start) observed on a page."""

    model_config = ConfigDict(extra="ignore")

    kind: StructureEventKind
    level: int = Field(ge=1, le=4)
    number: str | None = None
    title: str


# --- Block variants ----------------------------------------------------------
# Each block has a discriminating `kind` plus kind-specific fields. We model
# them as a flat union with `extra="ignore"` and per-validator field rules so
# the LLM has wiggle room on unrecognized fields without breaking ingestion.


class _BaseBlock(BaseModel):
    model_config = ConfigDict(extra="ignore")
    kind: BlockKind


class HeadingBlock(_BaseBlock):
    kind: Literal["heading"] = "heading"
    level: int = Field(ge=1, le=6)
    text: str


class ParagraphBlock(_BaseBlock):
    kind: Literal["paragraph"] = "paragraph"
    markdown: str


class DefinitionBlock(_BaseBlock):
    kind: Literal["definition"] = "definition"
    label: str | None = None
    markdown: str


class TheoremBlock(_BaseBlock):
    kind: Literal["theorem"] = "theorem"
    subkind: TheoremSubkind = "theorem"
    label: str | None = None
    markdown: str


class ProofBlock(_BaseBlock):
    kind: Literal["proof"] = "proof"
    markdown: str


class ExampleBlock(_BaseBlock):
    kind: Literal["example"] = "example"
    label: str | None = None
    markdown: str


class RemarkBlock(_BaseBlock):
    kind: Literal["remark"] = "remark"
    markdown: str


class EquationBlock(_BaseBlock):
    kind: Literal["equation"] = "equation"
    label: str | None = None
    latex: str


BBox = Annotated[list[float], Field(min_length=4, max_length=4)]


class FigureBlock(_BaseBlock):
    kind: Literal["figure"] = "figure"
    caption: str | None = None
    bbox: BBox  # [x, y, width, height] in image pixel coords (origin top-left)


class TableBlock(_BaseBlock):
    kind: Literal["table"] = "table"
    caption: str | None = None
    bbox: BBox
    markdown: str | None = None


class ListBlock(_BaseBlock):
    kind: Literal["list"] = "list"
    ordered: bool = False
    items: list[str] = Field(default_factory=list)


class ExerciseBlock(_BaseBlock):
    kind: Literal["exercise"] = "exercise"
    number: str | None = None
    markdown: str


Block = (
    HeadingBlock
    | ParagraphBlock
    | DefinitionBlock
    | TheoremBlock
    | ProofBlock
    | ExampleBlock
    | RemarkBlock
    | EquationBlock
    | FigureBlock
    | TableBlock
    | ListBlock
    | ExerciseBlock
)

_BLOCK_BY_KIND: dict[str, type[_BaseBlock]] = {
    "heading": HeadingBlock,
    "paragraph": ParagraphBlock,
    "definition": DefinitionBlock,
    "theorem": TheoremBlock,
    "proof": ProofBlock,
    "example": ExampleBlock,
    "remark": RemarkBlock,
    "equation": EquationBlock,
    "figure": FigureBlock,
    "table": TableBlock,
    "list": ListBlock,
    "exercise": ExerciseBlock,
}


def parse_block(raw: dict) -> Block | None:
    """Best-effort parse of a single block dict.

    Returns None when the block kind is unknown or required fields are missing,
    so the post-processor can drop the block with a warning rather than fail
    the whole batch on one malformed entry.
    """
    kind = raw.get("kind")
    cls = _BLOCK_BY_KIND.get(kind) if isinstance(kind, str) else None
    if cls is None:
        return None
    try:
        return cls.model_validate(raw)
    except Exception:
        return None


class PageExtraction(BaseModel):
    """LLM-extracted structure and content for a single page."""

    model_config = ConfigDict(extra="ignore")

    page: int = Field(ge=1)
    page_kind: PageKind = "body"
    structure_events: list[StructureEvent] = Field(default_factory=list)
    blocks: list[Block] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    notes: str | None = None

    @field_validator("blocks", mode="before")
    @classmethod
    def _parse_blocks(cls, value):
        if not isinstance(value, list):
            return []
        out: list[Block] = []
        for item in value:
            if isinstance(item, _BaseBlock):
                out.append(item)
                continue
            if not isinstance(item, dict):
                continue
            parsed = parse_block(item)
            if parsed is not None:
                out.append(parsed)
        return out


class PageBatchExtraction(BaseModel):
    """Top-level wrapper returned by the page-extraction LLM call."""

    model_config = ConfigDict(extra="ignore")

    pages: list[PageExtraction] = Field(default_factory=list)


# --- Helpers -----------------------------------------------------------------


def section_path_after(
    current_path: list[str],
    events: list[StructureEvent],
) -> list[str]:
    """Apply structure events to a section path.

    The path is a stack indexed by level (level 1 at index 0). When we see a
    chapter_start (level 1), we replace everything from index 0 onward. A
    section_start (level 2) replaces from index 1 onward. And so on. This
    keeps the path consistent across pages in a batch.
    """
    path = list(current_path)
    for ev in events:
        depth = ev.level - 1
        if depth < 0:
            continue
        title = ev.title.strip()
        if ev.number:
            title = f"{ev.number} {title}".strip()
        path = path[:depth] + [title]
    return path


def page_kind_is_chunkable(kind: PageKind) -> bool:
    """Whether a page's blocks should be chunked into BookChunk rows."""
    return kind in {"body", "preface", "appendix", "exercises"}
