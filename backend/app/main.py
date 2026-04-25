from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.books import router as books_router
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
