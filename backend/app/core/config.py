from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "MathPath"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = "postgresql://mathpath:mathpath@localhost:5432/mathpath"

    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    LLM_TASK_ROUTING: dict = {}

    MASTERY_CONTINUE_THRESHOLD: float = 0.7
    MASTERY_REVIEW_THRESHOLD: float = 0.4

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
