from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class BookRead(BaseModel):
    id: UUID
    title: str
    source_type: str
    status: str
    file_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BookChunkRead(BaseModel):
    id: UUID
    book_id: UUID
    chunk_index: int
    chapter_title: str | None
    section_title: str | None
    page_start: int | None
    page_end: int | None
    clean_text: str
    token_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class ProcessRequest(BaseModel):
    steps: list[str] | None = None
    provider: str | None = None
    model: str | None = None
