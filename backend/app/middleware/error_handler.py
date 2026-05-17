from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from datetime import datetime, timezone
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _error_body(errors: list, status_code: int = 400) -> dict:
    return {
        "success": False,
        "errors": errors,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=_error_body([{"code": "HTTP_ERROR", "message": exc.detail}]),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err["loc"] if loc != "body")
        errors.append({"code": "VALIDATION_ERROR", "message": err["msg"], "field": field or None})
    return JSONResponse(status_code=422, content=_error_body(errors, 422))


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("Unhandled exception", exc_info=exc, path=request.url.path)
    return JSONResponse(
        status_code=500,
        content=_error_body([{"code": "INTERNAL_ERROR", "message": "An internal error occurred. Please try again later."}]),
    )
