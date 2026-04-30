import uuid

from sqlalchemy.orm import Session

from app.models.memory import LearningMemoryEvent


class MemoryEventWriter:
    def log_event(
        self,
        db: Session,
        user_id: uuid.UUID,
        event_type: str,
        book_id: uuid.UUID | None = None,
        tidbit_id: uuid.UUID | None = None,
        concept_id: uuid.UUID | None = None,
        payload: dict | None = None,
    ) -> LearningMemoryEvent:
        event = LearningMemoryEvent(
            user_id=user_id,
            event_type=event_type,
            book_id=book_id,
            tidbit_id=tidbit_id,
            concept_id=concept_id,
            payload_json=payload or {},
        )
        db.add(event)
        db.flush()
        return event
