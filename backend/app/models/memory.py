import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LearningMemoryEvent(Base):
    __tablename__ = "learning_memory_events"
    __table_args__ = (Index("idx_lme_user_created", "user_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    event_type: Mapped[str] = mapped_column(String(50))
    book_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("books.id"), nullable=True)
    tidbit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tidbits.id"), nullable=True)
    concept_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("concepts.id"), nullable=True)
    payload_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    embedding_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
