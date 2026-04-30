import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.lesson import TidbitLesson
from app.models.proof import ProofLadder
from app.models.tidbit import Tidbit
from app.schemas.lesson import TidbitLessonRead as LessonRead
from app.schemas.proof import ProofLadderRead

router = APIRouter(tags=["lessons"])


@router.post("/tidbits/{tidbit_id}/lesson/generate", response_model=LessonRead)
async def generate_lesson(tidbit_id: uuid.UUID, db: Session = Depends(get_db)):
    tidbit = db.get(Tidbit, tidbit_id)
    if not tidbit:
        raise HTTPException(status_code=404, detail="Tidbit not found")

    existing = db.query(TidbitLesson).filter(TidbitLesson.tidbit_id == tidbit_id).first()
    if existing:
        return existing

    from app.services.lesson_generation.lesson_generator import LessonGenerator

    generator = LessonGenerator()
    lesson = await generator.generate_lesson(db, tidbit_id)
    return lesson


@router.get("/tidbits/{tidbit_id}/lesson", response_model=LessonRead)
def get_lesson(tidbit_id: uuid.UUID, db: Session = Depends(get_db)):
    lesson = db.query(TidbitLesson).filter(TidbitLesson.tidbit_id == tidbit_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found. POST to generate one.")
    return lesson


@router.post("/tidbits/{tidbit_id}/proof-ladder/generate", response_model=ProofLadderRead | None)
async def generate_proof_ladder(tidbit_id: uuid.UUID, db: Session = Depends(get_db)):
    tidbit = db.get(Tidbit, tidbit_id)
    if not tidbit:
        raise HTTPException(status_code=404, detail="Tidbit not found")

    existing = db.query(ProofLadder).filter(ProofLadder.tidbit_id == tidbit_id).first()
    if existing:
        return existing

    from app.services.proof_generation.proof_ladder_generator import ProofLadderGenerator

    generator = ProofLadderGenerator()
    ladder = await generator.generate(db, tidbit_id)
    if not ladder:
        return None
    return ladder


@router.get("/tidbits/{tidbit_id}/proof-ladder", response_model=ProofLadderRead | None)
def get_proof_ladder(tidbit_id: uuid.UUID, db: Session = Depends(get_db)):
    ladder = db.query(ProofLadder).filter(ProofLadder.tidbit_id == tidbit_id).first()
    return ladder
