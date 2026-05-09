import logging
import uuid

from sqlalchemy.orm import Session

from app.llm.clients import get_llm_client
from app.models.book import BookChunk
from app.models.concept import Concept, ConceptEdge
from app.models.lesson import TidbitLesson
from app.models.plan import StudyPlan
from app.models.profile import BookProfile
from app.models.quiz import TidbitQuiz
from app.models.tidbit import Tidbit

logger = logging.getLogger(__name__)

ALL_STEPS = ["profile", "concepts", "graph", "plan", "first_lesson", "first_quiz"]


class PipelineOrchestrator:
    def __init__(self, provider: str | None = None, model: str | None = None):
        self.provider = provider
        self.model = model

    def _get_client(self, task: str):
        return get_llm_client(provider=self.provider, model=self.model, task=task)

    async def run(
        self,
        db: Session,
        book_id: uuid.UUID,
        steps: list[str] | None = None,
    ) -> dict:
        steps = steps or ALL_STEPS
        result: dict = {"book_id": str(book_id), "steps_run": [], "errors": []}

        chunk_count = db.query(BookChunk).filter(BookChunk.book_id == book_id).count()
        if chunk_count == 0:
            result["errors"].append("No chunks found. Upload a PDF first via POST /api/books/upload.")
            return result
        result["chunks"] = chunk_count

        if "profile" in steps:
            try:
                existing = db.query(BookProfile).filter(BookProfile.book_id == book_id).first()
                if not existing:
                    from app.services.profiling.book_profiler import BookProfiler
                    profiler = BookProfiler(llm=self._get_client("book_profiling"))
                    existing = await profiler.profile_book(db, book_id)
                result["profile"] = {
                    "subject": existing.detected_subject,
                    "level": existing.level,
                    "style": existing.style,
                }
                result["steps_run"].append("profile")
                logger.info("Pipeline: profiled → %s", existing.detected_subject)
            except Exception as e:
                result["errors"].append(f"profile: {e}")
                return result

        if "concepts" in steps:
            try:
                existing = db.query(Concept).filter(Concept.book_id == book_id).all()
                if not existing:
                    from app.services.concept_extraction.concept_extractor import ConceptExtractor
                    extractor = ConceptExtractor(llm=self._get_client("concept_extraction"))
                    existing = await extractor.extract_from_book(db, book_id)
                result["concepts"] = len(existing)
                result["steps_run"].append("concepts")
                logger.info("Pipeline: extracted %d concepts", len(existing))
            except Exception as e:
                result["errors"].append(f"concepts: {e}")
                return result

        if "graph" in steps:
            try:
                existing = db.query(ConceptEdge).filter(ConceptEdge.book_id == book_id).all()
                if not existing:
                    from app.services.graph.concept_graph_builder import ConceptGraphBuilder
                    builder = ConceptGraphBuilder(llm=self._get_client("concept_graph"))
                    existing = await builder.build_graph(db, book_id)
                result["edges"] = len(existing)
                result["steps_run"].append("graph")
                logger.info("Pipeline: %d graph edges", len(existing))
            except Exception as e:
                result["errors"].append(f"graph: {e}")
                return result

        if "plan" in steps:
            try:
                plan = db.query(StudyPlan).filter(StudyPlan.book_id == book_id).first()
                if not plan:
                    from app.services.planning.tidbit_planner import TidbitPlanner
                    planner = TidbitPlanner(llm=self._get_client("tidbit_planning"))
                    plan = await planner.generate_plan(db, book_id)
                tidbit_count = db.query(Tidbit).filter(Tidbit.study_plan_id == plan.id).count()
                result["plan_id"] = str(plan.id)
                result["tidbits"] = tidbit_count
                result["steps_run"].append("plan")
                logger.info("Pipeline: plan with %d tidbits", tidbit_count)
            except Exception as e:
                result["errors"].append(f"plan: {e}")
                return result

        if "first_lesson" in steps:
            try:
                plan = db.query(StudyPlan).filter(StudyPlan.book_id == book_id).first()
                if plan:
                    first_tidbit = (
                        db.query(Tidbit)
                        .filter(Tidbit.study_plan_id == plan.id)
                        .order_by(Tidbit.order_index)
                        .first()
                    )
                    if first_tidbit:
                        lesson = db.query(TidbitLesson).filter(TidbitLesson.tidbit_id == first_tidbit.id).first()
                        if not lesson:
                            from app.services.lesson_generation.lesson_generator import LessonGenerator
                            gen = LessonGenerator(llm=self._get_client("lesson_generation"))
                            lesson = await gen.generate_lesson(db, first_tidbit.id)
                        result["first_lesson_tidbit"] = first_tidbit.title
                        result["steps_run"].append("first_lesson")
                        logger.info("Pipeline: first lesson generated for '%s'", first_tidbit.title)
            except Exception as e:
                result["errors"].append(f"first_lesson: {e}")

        if "first_quiz" in steps:
            try:
                plan = db.query(StudyPlan).filter(StudyPlan.book_id == book_id).first()
                if plan:
                    first_tidbit = (
                        db.query(Tidbit)
                        .filter(Tidbit.study_plan_id == plan.id)
                        .order_by(Tidbit.order_index)
                        .first()
                    )
                    if first_tidbit:
                        quiz = db.query(TidbitQuiz).filter(TidbitQuiz.tidbit_id == first_tidbit.id).first()
                        if not quiz:
                            from app.services.quiz_generation.quiz_generator import QuizGenerator
                            gen = QuizGenerator(llm=self._get_client("quiz_generation"))
                            quiz = await gen.generate_quiz(db, first_tidbit.id)
                        q_count = len(quiz.quiz_json.get("questions", []))
                        result["first_quiz_questions"] = q_count
                        result["steps_run"].append("first_quiz")
                        logger.info("Pipeline: first quiz with %d questions", q_count)
            except Exception as e:
                result["errors"].append(f"first_quiz: {e}")

        return result
