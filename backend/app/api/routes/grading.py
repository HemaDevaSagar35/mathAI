import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.tidbit import Tidbit
from app.schemas.grading import GradeRequest

router = APIRouter(tags=["grading"])


@router.post("/tidbits/{tidbit_id}/quiz/grade")
async def grade_transcript(
    tidbit_id: uuid.UUID,
    data: GradeRequest,
    db: Session = Depends(get_db),
):
    tidbit = db.get(Tidbit, tidbit_id)
    if not tidbit:
        raise HTTPException(status_code=404, detail="Tidbit not found")

    from app.services.grading.answer_grader import AnswerGrader

    grader = AnswerGrader()
    attempt = await grader.grade_answer(
        db,
        tidbit_id=tidbit_id,
        question_id=data.question_id,
        transcript_final=data.transcript_final,
    )

    return {
        "attempt_id": str(attempt.id),
        "grading": attempt.feedback_json,
    }
