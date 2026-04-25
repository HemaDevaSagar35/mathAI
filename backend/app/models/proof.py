import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProofLadder(Base):
    __tablename__ = "proof_ladders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tidbit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tidbits.id", ondelete="CASCADE"))
    theorem_statement: Mapped[str] = mapped_column(Text)
    proof_ladder_json: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
