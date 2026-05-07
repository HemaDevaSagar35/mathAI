from pydantic_settings import BaseSettings, SettingsConfigDict


# Every task name a service may pass to get_llm_client(task=...).
# Adding a new task? Add it here and to the settings fields below, and
# document it in .env.example.
LLM_TASKS: tuple[str, ...] = (
    "page_extraction",
    "book_profiling",
    "concept_extraction",
    "concept_dedup",
    "concept_graph",
    "tidbit_planning",
    "lesson_generation",
    "proof_ladder",
    "quiz_generation",
    "answer_grading",
)


class Settings(BaseSettings):
    APP_NAME: str = "MathPath"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "postgresql://mathpath:mathpath@localhost:5432/mathpath"

    # ===== LLM provider API keys =====
    # Set the keys for any providers you reference in LLM_ALL_* or per-task
    # config below. At least one is required.
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    # ===== LLM_ALL — global override =====
    # If BOTH are set, this provider+model pair is used for every task.
    # Per-task settings below are ignored when ALL is configured.
    LLM_ALL_PROVIDER: str | None = None
    LLM_ALL_MODEL: str | None = None

    # ===== Per-task LLM configuration =====
    # When LLM_ALL_* is not configured, every task you actually call must have
    # its own provider+model pair. A missing pair on a called task raises an
    # explicit error from get_llm_client() telling you exactly what to set.
    LLM_PAGE_EXTRACTION_PROVIDER: str | None = None
    LLM_PAGE_EXTRACTION_MODEL: str | None = None

    LLM_BOOK_PROFILING_PROVIDER: str | None = None
    LLM_BOOK_PROFILING_MODEL: str | None = None

    LLM_CONCEPT_EXTRACTION_PROVIDER: str | None = None
    LLM_CONCEPT_EXTRACTION_MODEL: str | None = None

    LLM_CONCEPT_DEDUP_PROVIDER: str | None = None
    LLM_CONCEPT_DEDUP_MODEL: str | None = None

    LLM_CONCEPT_GRAPH_PROVIDER: str | None = None
    LLM_CONCEPT_GRAPH_MODEL: str | None = None

    LLM_TIDBIT_PLANNING_PROVIDER: str | None = None
    LLM_TIDBIT_PLANNING_MODEL: str | None = None

    LLM_LESSON_GENERATION_PROVIDER: str | None = None
    LLM_LESSON_GENERATION_MODEL: str | None = None

    LLM_PROOF_LADDER_PROVIDER: str | None = None
    LLM_PROOF_LADDER_MODEL: str | None = None

    LLM_QUIZ_GENERATION_PROVIDER: str | None = None
    LLM_QUIZ_GENERATION_MODEL: str | None = None

    LLM_ANSWER_GRADING_PROVIDER: str | None = None
    LLM_ANSWER_GRADING_MODEL: str | None = None

    # ===== Vision-first PDF ingestion (B14v2) =====
    # When false, /api/books/upload uses the legacy text-extraction PDF path.
    # When true, the upload route runs the multimodal page extractor.
    VISION_INGESTION_ENABLED: bool = False
    VISION_RENDER_DPI: int = 150
    VISION_FIGURE_DPI: int = 200
    VISION_BATCH_SIZE: int = 5

    # ===== Mastery thresholds =====
    MASTERY_CONTINUE_THRESHOLD: float = 0.7
    MASTERY_REVIEW_THRESHOLD: float = 0.4

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
