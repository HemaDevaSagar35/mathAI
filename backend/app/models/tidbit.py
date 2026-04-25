import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Tidbit(Base):
    __tablename__ = "tidbits"
    __table_args__ = (
        Index("idx_tidbits_plan_id", "study_plan_id"),
        Index("idx_tidbits_order", "study_plan_id", "order_index"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    study_plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("study_plans.id", ondelete="CASCADE"))
    book_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"))
    order_index: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(500))
    concept_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id"), nullable=True)
    learning_goal: Mapped[str] = mapped_column(Text)
    source_chunk_ids: Mapped[list] = mapped_column(JSONB, default=list)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=15)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    is_original_plan: Mapped[bool] = mapped_column(Boolean, default=True)
    inserted_after_tidbit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    tidbit_type: Mapped[str] = mapped_column(String(50), default="original")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
