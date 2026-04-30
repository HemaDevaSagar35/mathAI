import json
import uuid

from sqlalchemy.orm import Session

from app.llm.clients import BaseLLMClient, get_llm_client
from app.llm.prompts.loader import load_prompt
from app.models.concept import Concept
from app.models.grading import AnswerAttempt
from app.models.quiz import TidbitQuiz
from app.models.tidbit import Tidbit


class AnswerGrader:
    def __init__(self, llm: BaseLLMClient | None = None):
        self.llm = llm or get_llm_client(task="answer_grading")

    async def grade_answer(
        self,
        db: Session,
        tidbit_id: uuid.UUID,
        question_id: str,
        transcript_final: str,
        user_id: uuid.UUID | None = None,
    ) -> AnswerAttempt:
        tidbit = db.get(Tidbit, tidbit_id)
        if not tidbit:
            raise ValueError(f"Tidbit {tidbit_id} not found")

        quiz = db.query(TidbitQuiz).filter(TidbitQuiz.tidbit_id == tidbit_id).first()
        if not quiz:
            raise ValueError(f"No quiz for tidbit {tidbit_id}. Generate a quiz first.")

        question = self._find_question(quiz, question_id)
        if not question:
            raise ValueError(f"Question {question_id} not found in quiz")

        concept = db.get(Concept, tidbit.concept_id) if tidbit.concept_id else None

        prompt = load_prompt(
            "answer_grading",
            question_text=question.get("question", ""),
            expected_answer=question.get("expected_answer", ""),
            rubric_json=json.dumps(question.get("rubric", []), indent=2),
            transcript=transcript_final,
            concept_name=concept.name if concept else tidbit.title,
            learning_goal=tidbit.learning_goal,
        )

        grading = await self.llm.generate_json(prompt, task="answer_grading")

        score = max(0.0, min(1.0, float(grading.get("score", 0.0))))

        attempt = AnswerAttempt(
            user_id=user_id or uuid.UUID("00000000-0000-0000-0000-000000000001"),
            tidbit_id=tidbit_id,
            question_id=question_id,
            input_mode="typed",
            transcript_final=transcript_final,
            score=score,
            feedback_json=grading,
            misconception=grading.get("misconception_detected"),
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt

    @staticmethod
    def _find_question(quiz: TidbitQuiz, question_id: str) -> dict | None:
        questions = quiz.quiz_json.get("questions", [])
        for q in questions:
            if q.get("id") == question_id:
                return q
        return None
