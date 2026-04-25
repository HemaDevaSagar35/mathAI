import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AnswerAttempt(Base):
    __tablename__ = "answer_attempts"
    __table_args__ = (Index("idx_answer_attempts_user_tidbit", "user_id", "tidbit_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    tidbit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tidbits.id", ondelete="CASCADE"))
    question_id: Mapped[str] = mapped_column(String(50))
    input_mode: Mapped[str] = mapped_column(String(50), default="typed")
    audio_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    transcript_raw: Mapped[str | None] = mapped_column(Text, nullable=True)
    transcript_final: Mapped[str] = mapped_column(Text)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    feedback_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    misconception: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
