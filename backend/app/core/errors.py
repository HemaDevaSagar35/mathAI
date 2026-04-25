from fastapi import Request
from fastapi.responses import JSONResponse


class MathPathError(Exception):
    def __init__(self, message: str = "An error occurred", status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundError(MathPathError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, status_code=404)


class ProcessingError(MathPathError):
    def __init__(self, message: str = "Processing failed"):
        super().__init__(message=message, status_code=422)


class LLMError(MathPathError):
    def __init__(self, message: str = "LLM call failed"):
        super().__init__(message=message, status_code=502)


async def mathpath_error_handler(_request: Request, exc: MathPathError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message},
    )
