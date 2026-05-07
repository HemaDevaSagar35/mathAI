"""BookSection — chapter / section / subsection tree for a book.

Populated by the vision-based ingestion pipeline (B14 v2). Each row represents
a structural unit of the book, with `parent_id` pointing at its containing
unit (chapter contains sections, sections contain subsections). `level` tracks
the depth (1 = chapter, 2 = section, 3 = subsection, etc.).

Existing chunks (from the legacy text-only path) have `section_id = NULL` and
keep working unchanged. New ingestions populate `section_id` and group chunks
under their containing section.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BookSection(Base):
    __tablename__ = "book_sections"
    __table_args__ = (
        Index("idx_book_sections_book_id", "book_id"),
        Index("idx_book_sections_parent_id", "parent_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE")
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("book_sections.id", ondelete="CASCADE"), nullable=True
    )
    # 1 = chapter, 2 = section, 3 = subsection, ...
    level: Mapped[int] = mapped_column(Integer)
    # Position among siblings sharing the same parent_id. Stable ordering
    # within a parent; not globally unique.
    order_index: Mapped[int] = mapped_column(Integer)
    # Structural classification (matches StructureEvent.kind from the schema):
    # chapter | section | subsection | appendix | references | index | preface | frontmatter
    kind: Mapped[str] = mapped_column(String(50), default="section")
    # Printed label like "3", "3.2", "A.1", or null if unnumbered.
    number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    title: Mapped[str] = mapped_column(String(500))
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
