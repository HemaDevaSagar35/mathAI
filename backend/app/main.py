from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.books import router as books_router
from app.api.routes.profiles import router as profiles_router
from app.api.routes.concepts import router as concepts_router
from app.api.routes.plans import router as plans_router
from app.api.routes.lessons import router as lessons_router
from app.api.routes.quizzes import router as quizzes_router
from app.api.routes.grading import router as grading_router
from app.api.routes.progress import router as progress_router
from app.core.errors import MathPathError, mathpath_error_handler
from app.core.logging import setup_logging
from app.core.network import print_local_ip


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    setup_logging()
    print_local_ip()
    yield


app = FastAPI(title="MathPath API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(MathPathError, mathpath_error_handler)

app.include_router(health_router, prefix="/api")
app.include_router(books_router, prefix="/api")
app.include_router(profiles_router, prefix="/api")
app.include_router(concepts_router, prefix="/api")
app.include_router(plans_router, prefix="/api")
app.include_router(lessons_router, prefix="/api")
app.include_router(quizzes_router, prefix="/api")
app.include_router(grading_router, prefix="/api")
app.include_router(progress_router, prefix="/api")
