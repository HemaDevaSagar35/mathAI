from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserCreate(BaseModel):
    email: str | None = None
    display_name: str = "Default User"
    preferences_json: dict | None = None


class UserRead(BaseModel):
    id: UUID
    email: str | None
    display_name: str
    preferences_json: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}
