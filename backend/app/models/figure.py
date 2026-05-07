"""BookFigure — extracted figure / diagram crops from a book page.

Each row points at a cropped PNG saved on disk under
`uploads/{book_id}/figures/...`. The originating page image is preserved by
the ingestor under `uploads/{book_id}/pages/...` so figures can be re-cropped
later if needed.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BookFigure(Base):
    __tablename__ = "book_figures"
    __table_args__ = (
        Index("idx_book_figures_book_id", "book_id"),
        Index("idx_book_figures_section_id", "section_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE")
    )
    section_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("book_sections.id", ondelete="SET NULL"), nullable=True
    )
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("book_chunks.id", ondelete="SET NULL"), nullable=True
    )
    page: Mapped[int] = mapped_column(Integer)
    # Local path under uploads/, e.g. "uploads/<book_id>/figures/p47_f1.png"
    image_url: Mapped[str] = mapped_column(String(1000))
    caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Original bbox emitted by the LLM, in source-page image pixel coords
    # ([x, y, width, height], origin top-left).
    bbox_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
