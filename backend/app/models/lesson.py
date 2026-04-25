import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TidbitLesson(Base):
    __tablename__ = "tidbit_lessons"
    __table_args__ = (Index("idx_tidbit_lessons_tidbit_id", "tidbit_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tidbit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tidbits.id", ondelete="CASCADE"))
    lesson_json: Mapped[dict] = mapped_column(JSONB)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
