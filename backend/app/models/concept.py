import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Concept(Base):
    __tablename__ = "concepts"
    __table_args__ = (
        Index("idx_concepts_book_id", "book_id"),
        Index("idx_concepts_normalized_name", "book_id", "normalized_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(300))
    normalized_name: Mapped[str] = mapped_column(String(300))
    concept_type: Mapped[str] = mapped_column(String(50))
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    importance: Mapped[str] = mapped_column(String(50), default="supporting")
    source_chunk_ids: Mapped[list] = mapped_column(JSONB, default=list)
    prerequisite_names: Mapped[list] = mapped_column(JSONB, default=list)
    common_confusions: Mapped[list] = mapped_column(JSONB, default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ConceptEdge(Base):
    __tablename__ = "concept_edges"
    __table_args__ = (
        Index("idx_concept_edges_book_id", "book_id"),
        Index("idx_concept_edges_source", "source_concept_id"),
        Index("idx_concept_edges_target", "target_concept_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"))
    source_concept_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"))
    target_concept_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id", ondelete="CASCADE"))
    edge_type: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
