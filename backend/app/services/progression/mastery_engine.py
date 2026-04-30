import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.concept import Concept
from app.models.grading import AnswerAttempt
from app.models.progress import ConceptMastery, UserTidbitProgress
from app.models.tidbit import Tidbit
from app.services.memory.memory_event_writer import MemoryEventWriter
from app.services.progression.next_item_selector import NextItemSelector

DEFAULT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class MasteryEngine:
    def __init__(self):
        self.memory = MemoryEventWriter()
        self.selector = NextItemSelector()

    def update_after_grading(
        self,
        db: Session,
        user_id: uuid.UUID,
        tidbit_id: uuid.UUID,
        grading_result: dict,
    ) -> dict:
        """Update progress and mastery after a single question is graded."""
        tidbit = db.get(Tidbit, tidbit_id)
        if not tidbit:
            raise ValueError(f"Tidbit {tidbit_id} not found")

        # Ensure UserTidbitProgress exists and is started
        progress = (
            db.query(UserTidbitProgress)
            .filter(
                UserTidbitProgress.user_id == user_id,
                UserTidbitProgress.tidbit_id == tidbit_id,
            )
            .first()
        )
        if not progress:
            progress = UserTidbitProgress(
                user_id=user_id,
                tidbit_id=tidbit_id,
                status="started",
                started_at=datetime.now(timezone.utc),
            )
            db.add(progress)
            db.flush()
        elif progress.status == "locked":
            progress.status = "started"
            progress.started_at = datetime.now(timezone.utc)

        # Update concept mastery from grading mastery_updates
        mastery_changes = []
        for update in grading_result.get("mastery_updates", []):
            concept_name = update.get("concept", "")
            delta = float(update.get("delta", 0))
            if not concept_name or delta == 0:
                continue

            concept = (
                db.query(Concept)
                .filter(Concept.book_id == tidbit.book_id, Concept.normalized_name == concept_name.strip().lower())
                .first()
            )
            if not concept:
                continue

            mastery = (
                db.query(ConceptMastery)
                .filter(ConceptMastery.user_id == user_id, ConceptMastery.concept_id == concept.id)
                .first()
            )
            if not mastery:
                mastery = ConceptMastery(
                    user_id=user_id,
                    concept_id=concept.id,
                    mastery_score=0.5,
                    confidence=0.0,
                )
                db.add(mastery)
                db.flush()

            mastery.mastery_score = max(0.0, min(1.0, mastery.mastery_score + delta))
            mastery.confidence = min(1.0, mastery.confidence + 0.05)
            mastery.last_seen_at = datetime.now(timezone.utc)
            mastery_changes.append({"concept": concept_name, "new_score": mastery.mastery_score})

        # Log memory event
        self.memory.log_event(
            db,
            user_id=user_id,
            event_type="quiz_answered",
            book_id=tidbit.book_id,
            tidbit_id=tidbit_id,
            concept_id=tidbit.concept_id,
            payload={"score": grading_result.get("score", 0), "mastery_changes": mastery_changes},
        )

        db.commit()
        return {
            "tidbit_status": progress.status,
            "mastery_updates": mastery_changes,
            "next_action": grading_result.get("next_action", {"type": "continue", "reason": ""}),
        }

    def complete_tidbit(
        self,
        db: Session,
        user_id: uuid.UUID,
        tidbit_id: uuid.UUID,
    ) -> dict:
        """Called when all quiz questions for a tidbit are answered."""
        tidbit = db.get(Tidbit, tidbit_id)
        if not tidbit:
            raise ValueError(f"Tidbit {tidbit_id} not found")

        # Compute average quiz score
        attempts = (
            db.query(AnswerAttempt)
            .filter(AnswerAttempt.user_id == user_id, AnswerAttempt.tidbit_id == tidbit_id)
            .all()
        )
        avg_score = sum(a.score for a in attempts) / len(attempts) if attempts else 0.0

        # Update progress
        progress = (
            db.query(UserTidbitProgress)
            .filter(UserTidbitProgress.user_id == user_id, UserTidbitProgress.tidbit_id == tidbit_id)
            .first()
        )
        if not progress:
            progress = UserTidbitProgress(
                user_id=user_id, tidbit_id=tidbit_id, status="completed"
            )
            db.add(progress)
        else:
            progress.status = "completed"

        progress.completed_at = datetime.now(timezone.utc)
        progress.quiz_score = avg_score

        # Determine action based on score thresholds
        concept = db.get(Concept, tidbit.concept_id) if tidbit.concept_id else None
        action = "continue"
        next_tidbit = None

        if avg_score < settings.MASTERY_REVIEW_THRESHOLD:
            inserted = self.selector.insert_remedial_tidbit(db, tidbit, concept)
            action = "remedial"
            next_tidbit = inserted
        elif avg_score < settings.MASTERY_CONTINUE_THRESHOLD:
            inserted = self.selector.insert_review_tidbit(db, tidbit, concept)
            action = "review"
            next_tidbit = inserted
        else:
            next_tidbit = self.selector.get_next_tidbit(db, user_id, tidbit.study_plan_id)

        # Log completion event
        self.memory.log_event(
            db,
            user_id=user_id,
            event_type="lesson_completed",
            book_id=tidbit.book_id,
            tidbit_id=tidbit_id,
            concept_id=tidbit.concept_id,
            payload={"quiz_score": avg_score, "action": action},
        )

        db.commit()
        return {
            "quiz_score": avg_score,
            "action": action,
            "next_tidbit_id": str(next_tidbit.id) if next_tidbit else None,
        }
