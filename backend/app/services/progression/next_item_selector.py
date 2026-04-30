import uuid

from sqlalchemy.orm import Session

from app.models.concept import Concept
from app.models.progress import UserTidbitProgress
from app.models.tidbit import Tidbit


class NextItemSelector:
    def get_next_tidbit(
        self, db: Session, user_id: uuid.UUID, study_plan_id: uuid.UUID
    ) -> Tidbit | None:
        """Find next tidbit: pending review/remedial first, then next original."""
        all_tidbits = (
            db.query(Tidbit)
            .filter(Tidbit.study_plan_id == study_plan_id)
            .order_by(Tidbit.order_index)
            .all()
        )

        completed_ids = {
            p.tidbit_id
            for p in db.query(UserTidbitProgress)
            .filter(
                UserTidbitProgress.user_id == user_id,
                UserTidbitProgress.status == "completed",
            )
            .all()
        }

        # Prioritize non-original (review/remedial) tidbits that aren't completed
        for t in all_tidbits:
            if not t.is_original_plan and t.id not in completed_ids:
                return t

        # Then find next original tidbit
        for t in all_tidbits:
            if t.id not in completed_ids:
                return t

        return None

    def insert_review_tidbit(
        self,
        db: Session,
        after_tidbit: Tidbit,
        concept: Concept | None,
    ) -> Tidbit:
        concept_name = concept.name if concept else after_tidbit.title
        tidbit = Tidbit(
            study_plan_id=after_tidbit.study_plan_id,
            book_id=after_tidbit.book_id,
            order_index=after_tidbit.order_index,
            title=f"Review: {concept_name}",
            concept_id=after_tidbit.concept_id,
            learning_goal=f"Review and reinforce your understanding of {concept_name}",
            source_chunk_ids=after_tidbit.source_chunk_ids or [],
            estimated_minutes=10,
            difficulty=max(1, after_tidbit.difficulty - 1),
            is_original_plan=False,
            inserted_after_tidbit_id=after_tidbit.id,
            tidbit_type="review",
        )
        db.add(tidbit)
        db.flush()
        return tidbit

    def insert_remedial_tidbit(
        self,
        db: Session,
        after_tidbit: Tidbit,
        concept: Concept | None,
    ) -> Tidbit:
        concept_name = concept.name if concept else after_tidbit.title
        tidbit = Tidbit(
            study_plan_id=after_tidbit.study_plan_id,
            book_id=after_tidbit.book_id,
            order_index=after_tidbit.order_index,
            title=f"Remedial: {concept_name}",
            concept_id=after_tidbit.concept_id,
            learning_goal=f"Simplified introduction to {concept_name} with extra examples and step-by-step guidance",
            source_chunk_ids=after_tidbit.source_chunk_ids or [],
            estimated_minutes=15,
            difficulty=max(1, after_tidbit.difficulty - 2),
            is_original_plan=False,
            inserted_after_tidbit_id=after_tidbit.id,
            tidbit_type="remedial",
        )
        db.add(tidbit)
        db.flush()
        return tidbit
