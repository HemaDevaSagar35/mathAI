# B01 — Project Skeleton

> **Objective:** Stand up a working FastAPI backend with Postgres, Alembic migrations, config management, structured logging, and a health endpoint.

**Depends on:** Nothing (first milestone)

---

## Tasks

### 1. Initialize the project directory

```text
mathpath/
  backend/
    app/
      __init__.py
      main.py
      core/
        __init__.py
        config.py
        logging.py
        errors.py
      api/
        __init__.py
        routes/
          __init__.py
          health.py
      db/
        __init__.py
        session.py
        base.py
    scripts/
    tests/
      __init__.py
    alembic/
      env.py
      versions/
    alembic.ini
    requirements.txt
    .env.example
```

### 2. Create `requirements.txt`

```text
fastapi>=0.111
uvicorn[standard]>=0.30
sqlalchemy>=2.0
alembic>=1.13
psycopg2-binary>=2.9
python-dotenv>=1.0
pydantic>=2.7
pydantic-settings>=2.3
python-multipart>=0.0.9
```

### 3. Config management — `app/core/config.py`

Use `pydantic-settings` to load environment variables:

```python
class Settings(BaseSettings):
    APP_NAME: str = "MathPath"
    DEBUG: bool = False
    DATABASE_URL: str  # postgres://...
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

### 4. Structured logging — `app/core/logging.py`

Configure Python `logging` with JSON or structured format. Expose a `get_logger(name)` helper.

### 5. Custom error classes — `app/core/errors.py`

```python
class MathPathError(Exception): ...
class NotFoundError(MathPathError): ...
class ProcessingError(MathPathError): ...
```

Register FastAPI exception handlers in `main.py`.

### 6. Database session — `app/db/session.py`

Use **synchronous** SQLAlchemy for MVP (simpler debugging, no async session pitfalls). Async can be added later if needed.

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

Register `get_db` as a FastAPI dependency in routes via `db: Session = Depends(get_db)`.

### 7. Declarative base — `app/db/base.py`

```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

### 8. Alembic setup

```bash
alembic init alembic
```

Wire `alembic/env.py` to import `Base.metadata` and read `DATABASE_URL` from settings.

### 9. Health endpoint — `app/api/routes/health.py`

```python
@router.get("/health")
async def health():
    return {"status": "ok"}
```

### 10. CORS middleware

The React Native mobile app will call the API from a different origin. Add CORS in `main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 11. Application entry — `app/main.py`

```python
app = FastAPI(title="MathPath API", version="0.1.0")
app.add_middleware(CORSMiddleware, ...)
app.include_router(health_router, prefix="/api")
```

Use `/api` prefix on all routes so the mobile app has a clean namespace.

### 12. `.env.example`

```text
DATABASE_URL=postgresql://mathpath:mathpath@localhost:5432/mathpath
LOG_LEVEL=INFO
DEBUG=true

# LLM providers (set at least one)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=
```

---

## Acceptance Criteria

- [ ] `uvicorn app.main:app --reload` starts without error.
- [ ] `GET /health` returns `{"status": "ok"}`.
- [ ] Database connection succeeds (test by calling `engine.connect()`).
- [ ] `alembic revision --autogenerate -m "init"` creates a migration.
- [ ] `alembic upgrade head` runs cleanly.

---

## Agent Prompt

```text
Create a FastAPI backend project at mathpath/backend/ with:
- app/main.py as the FastAPI entrypoint with CORS middleware (allow all origins for dev) and /api prefix
- app/core/config.py using pydantic-settings for DATABASE_URL, LOG_LEVEL, DEBUG, LLM_PROVIDER, LLM_MODEL, OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY
- app/core/logging.py with structured logging helper
- app/core/errors.py with MathPathError, NotFoundError, ProcessingError and FastAPI exception handlers
- app/db/session.py with synchronous SQLAlchemy engine, SessionLocal, and get_db() dependency
- app/db/base.py with DeclarativeBase
- app/api/routes/health.py with GET /api/health returning {"status": "ok"}
- Alembic wired to the same DATABASE_URL and Base metadata
- requirements.txt with pinned minimum versions (include python-multipart)
- .env.example with all LLM API keys
Keep code modular. Use type hints everywhere.
```
