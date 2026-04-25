from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ProofLadderRead(BaseModel):
    id: UUID
    tidbit_id: UUID
    theorem_statement: str
    proof_ladder_json: dict
    created_at: datetime

    model_config = {"from_attributes": True}
