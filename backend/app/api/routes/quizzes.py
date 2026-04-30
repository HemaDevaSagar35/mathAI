import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.quiz import TidbitQuiz
from app.models.tidbit import Tidbit
from app.schemas.quiz import TidbitQuizRead

router = APIRouter(tags=["quizzes"])


@router.post("/tidbits/{tidbit_id}/quiz/generate", response_model=TidbitQuizRead)
async def generate_quiz(tidbit_id: uuid.UUID, db: Session = Depends(get_db)):
    tidbit = db.get(Tidbit, tidbit_id)
    if not tidbit:
        raise HTTPException(status_code=404, detail="Tidbit not found")

    existing = db.query(TidbitQuiz).filter(TidbitQuiz.tidbit_id == tidbit_id).first()
    if existing:
        return existing

    from app.services.quiz_generation.quiz_generator import QuizGenerator

    generator = QuizGenerator()
    quiz = await generator.generate_quiz(db, tidbit_id)
    return quiz


@router.get("/tidbits/{tidbit_id}/quiz", response_model=TidbitQuizRead)
def get_quiz(tidbit_id: uuid.UUID, db: Session = Depends(get_db)):
    quiz = db.query(TidbitQuiz).filter(TidbitQuiz.tidbit_id == tidbit_id).first()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found. POST to generate one.")
    return quiz
