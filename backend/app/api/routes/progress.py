import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.book import Book
from app.models.memory import LearningMemoryEvent
from app.models.plan import StudyPlan
from app.models.progress import ConceptMastery, UserTidbitProgress
from app.models.tidbit import Tidbit

router = APIRouter(tags=["progress"])

DEFAULT_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@router.get("/progress")
def get_progress(
    user_id: uuid.UUID = Query(default=DEFAULT_USER_ID),
    db: Session = Depends(get_db),
):
    # Find active book (most recent plan)
    plan = (
        db.query(StudyPlan)
        .filter(StudyPlan.user_id == user_id, StudyPlan.status == "active")
        .order_by(StudyPlan.created_at.desc())
        .first()
    )
    if not plan:
        plan = db.query(StudyPlan).order_by(StudyPlan.created_at.desc()).first()

    active_book = None
    current_tidbit = None
    overall_progress = 0.0

    if plan:
        book = db.get(Book, plan.book_id)
        active_book = {"id": str(plan.book_id), "title": book.title} if book else None

        total = db.query(Tidbit).filter(Tidbit.study_plan_id == plan.id).count()
        completed = (
            db.query(UserTidbitProgress)
            .join(Tidbit, Tidbit.id == UserTidbitProgress.tidbit_id)
            .filter(
                Tidbit.study_plan_id == plan.id,
                UserTidbitProgress.user_id == user_id,
                UserTidbitProgress.status == "completed",
            )
            .count()
        )
        overall_progress = completed / total if total > 0 else 0.0

        # Current tidbit = first non-completed
        completed_ids = {
            p.tidbit_id
            for p in db.query(UserTidbitProgress)
            .filter(UserTidbitProgress.user_id == user_id, UserTidbitProgress.status == "completed")
            .all()
        }
        for t in (
            db.query(Tidbit)
            .filter(Tidbit.study_plan_id == plan.id)
            .order_by(Tidbit.order_index)
            .all()
        ):
            if t.id not in completed_ids:
                current_tidbit = {"id": str(t.id), "title": t.title, "order_index": t.order_index}
                break

    # Streak
    streak = _calculate_streak(db, user_id)

    # Weak concepts
    weak = (
        db.query(ConceptMastery)
        .filter(ConceptMastery.user_id == user_id, ConceptMastery.mastery_score < 0.5)
        .all()
    )
    weak_concepts = [
        {"concept_id": str(w.concept_id), "mastery_score": w.mastery_score}
        for w in weak
    ]

    # Recent activity
    events = (
        db.query(LearningMemoryEvent)
        .filter(LearningMemoryEvent.user_id == user_id)
        .order_by(LearningMemoryEvent.created_at.desc())
        .limit(10)
        .all()
    )
    recent_activity = [
        {"event_type": e.event_type, "created_at": e.created_at.isoformat() if e.created_at else None,
         "payload": e.payload_json}
        for e in events
    ]

    return {
        "active_book": active_book,
        "current_tidbit": current_tidbit,
        "streak": streak,
        "overall_progress": round(overall_progress, 3),
        "weak_concepts": weak_concepts,
        "recent_activity": recent_activity,
    }


@router.get("/progress/concepts")
def get_concept_mastery(
    user_id: uuid.UUID = Query(default=DEFAULT_USER_ID),
    db: Session = Depends(get_db),
):
    mastery = (
        db.query(ConceptMastery)
        .filter(ConceptMastery.user_id == user_id)
        .order_by(ConceptMastery.mastery_score.desc())
        .all()
    )
    return [
        {
            "concept_id": str(m.concept_id),
            "mastery_score": m.mastery_score,
            "confidence": m.confidence,
            "last_seen_at": m.last_seen_at.isoformat() if m.last_seen_at else None,
        }
        for m in mastery
    ]


@router.post("/tidbits/{tidbit_id}/complete")
def complete_tidbit(
    tidbit_id: uuid.UUID,
    user_id: uuid.UUID = Query(default=DEFAULT_USER_ID),
    db: Session = Depends(get_db),
):
    from app.services.progression.mastery_engine import MasteryEngine

    engine = MasteryEngine()
    result = engine.complete_tidbit(db, user_id, tidbit_id)
    return result


def _calculate_streak(db: Session, user_id: uuid.UUID) -> int:
    events = (
        db.query(LearningMemoryEvent)
        .filter(
            LearningMemoryEvent.user_id == user_id,
            LearningMemoryEvent.event_type == "lesson_completed",
        )
        .order_by(LearningMemoryEvent.created_at.desc())
        .all()
    )
    if not events:
        return 0

    dates = sorted({e.created_at.date() for e in events if e.created_at}, reverse=True)
    if not dates:
        return 0

    today = datetime.now(timezone.utc).date()
    if dates[0] < today - timedelta(days=1):
        return 0

    streak = 1
    for i in range(1, len(dates)):
        if dates[i - 1] - dates[i] == timedelta(days=1):
            streak += 1
        else:
            break
    return streak
