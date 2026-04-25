import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BookProfile(Base):
    __tablename__ = "book_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    book_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("books.id", ondelete="CASCADE"), unique=True)
    profile_json: Mapped[dict] = mapped_column(JSONB)
    detected_subject: Mapped[str] = mapped_column(String(200))
    level: Mapped[str] = mapped_column(String(50))
    style: Mapped[str] = mapped_column(String(100))
    proof_density: Mapped[str] = mapped_column(String(50))
    computation_density: Mapped[str] = mapped_column(String(50))
    diagram_dependency: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
