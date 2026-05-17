from typing import Optional
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.utils.jwt_handler import decode, JWTDecodeError
from config import get_settings

settings = get_settings()

EXEMPT_PATHS = {"/health", "/health/db", "/api/v1/auth/login", "/api/v1/auth/refresh", "/docs", "/openapi.json", "/redoc"}
EXEMPT_PREFIXES = ("/api/v1/auth/tenant/",)


class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if path in EXEMPT_PATHS or any(path.startswith(p) for p in EXEMPT_PREFIXES):
            return await call_next(request)

        tenant_id = self._extract_tenant_id(request)
        request.state.tenant_id = tenant_id
        return await call_next(request)

    def _extract_tenant_id(self, request: Request) -> Optional[str]:
        if tid := request.headers.get("X-Tenant-ID"):
            return tid

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
            try:
                payload = decode(token, settings.secret_key, options={"verify_exp": False})
                return payload.get("tenant_id")
            except JWTDecodeError:
                pass

        return None
