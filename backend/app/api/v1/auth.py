from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_db, get_current_user
from app.services.user_service import UserService
from app.services.tenant_service import TenantService
from app.schemas.auth import LoginRequest, TokenRefreshRequest
from app.utils.formatters import api_response
from app.utils.jwt_handler import decode, JWTDecodeError, JWTExpiredError
from app.utils.rate_limit import check_rate_limit
from config import get_settings

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/tenant/{code}", response_model=dict)
def resolve_tenant(code: str, db: Session = Depends(get_db)):
    """Public endpoint: resolve tenant code → tenant_id for the login form."""
    tenant = TenantService(db).get_by_code(code.upper())
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found.")
    return api_response(data={"id": tenant.id, "name": tenant.name, "code": tenant.code})


@router.post("/login", response_model=dict)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    client_ip = request.client.host if request.client else "unknown"
    if not check_rate_limit(f"login:{client_ip}", settings.login_rate_limit):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )
    tenant_id = getattr(request.state, "tenant_id", None) or request.headers.get("X-Tenant-ID")
    if not tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant context required. Provide X-Tenant-ID header.")
    user = UserService(db).authenticate(tenant_id, payload.email, payload.password)
    tokens = UserService(db).generate_tokens(user)
    return api_response(data=tokens, message="Login successful.")


@router.post("/refresh", response_model=dict)
def refresh_token(payload: TokenRefreshRequest, db: Session = Depends(get_db)):
    try:
        decoded = decode(payload.refresh_token, settings.secret_key)
        if decoded.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")
        from app.models.user import User
        user = db.query(User).filter(User.id == decoded["sub"]).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found.")
        tokens = UserService(db).generate_tokens(user)
        return api_response(data=tokens, message="Token refreshed.")
    except (JWTDecodeError, JWTExpiredError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token.")


@router.post("/logout", response_model=dict)
def logout(current_user=Depends(get_current_user)):
    return api_response(message="Logged out successfully.")


@router.get("/me", response_model=dict)
def me(current_user=Depends(get_current_user)):
    return api_response(data={
        "id": current_user.id,
        "tenant_id": current_user.tenant_id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "user_type": current_user.user_type,
        "permissions": list(current_user.get_permission_codes()),
    })
