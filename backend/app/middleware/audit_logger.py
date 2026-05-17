from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import uuid

AUDIT_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SKIP_PATHS = {"/health", "/health/db", "/docs", "/openapi.json", "/redoc"}


class AuditLoggerMiddleware(BaseHTTPMiddleware):
    """Logs metadata for every mutating API request. Full entity diffing is done in services."""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method not in AUDIT_METHODS:
            return await call_next(request)
        if any(request.url.path.startswith(p) for p in SKIP_PATHS):
            return await call_next(request)

        request.state.audit_request_id = str(uuid.uuid4())
        request.state.client_ip = request.client.host if request.client else None
        request.state.user_agent = request.headers.get("User-Agent")

        response = await call_next(request)
        return response
