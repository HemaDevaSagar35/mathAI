import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.book import Book
from app.models.plan import StudyPlan
from app.models.tidbit import Tidbit
from app.schemas.tidbit import TidbitRead

router = APIRouter(tags=["plans"])


@router.post("/books/{book_id}/plan/generate")
async def generate_plan(book_id: uuid.UUID, db: Session = Depends(get_db)):
    book = db.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    existing = db.query(StudyPlan).filter(StudyPlan.book_id == book_id).first()
    if existing:
        tidbits = (
            db.query(Tidbit)
            .filter(Tidbit.study_plan_id == existing.id)
            .order_by(Tidbit.order_index)
            .all()
        )
        return {
            "plan_id": str(existing.id),
            "status": existing.status,
            "tidbit_count": len(tidbits),
            "message": "Plan already exists",
        }

    from app.services.planning.tidbit_planner import TidbitPlanner

    planner = TidbitPlanner()
    plan = await planner.generate_plan(db, book_id)

    tidbit_count = (
        db.query(Tidbit).filter(Tidbit.study_plan_id == plan.id).count()
    )

    return {
        "plan_id": str(plan.id),
        "status": plan.status,
        "tidbit_count": tidbit_count,
    }


@router.get("/books/{book_id}/plan")
def get_plan(book_id: uuid.UUID, db: Session = Depends(get_db)):
    plan = db.query(StudyPlan).filter(StudyPlan.book_id == book_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="No plan found. POST to generate one.")

    tidbits = (
        db.query(Tidbit)
        .filter(Tidbit.study_plan_id == plan.id)
        .order_by(Tidbit.order_index)
        .all()
    )

    return {
        "plan_id": str(plan.id),
        "book_id": str(plan.book_id),
        "status": plan.status,
        "created_at": plan.created_at.isoformat() if plan.created_at else None,
        "tidbits": [TidbitRead.model_validate(t).model_dump(mode="json") for t in tidbits],
    }
