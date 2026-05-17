from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.v1.dependencies import get_db, get_current_user, require_permissions, get_pagination
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate, UserRoleAssign, RoleCreate, RoleUpdate
from app.schemas.base import PaginationParams
from app.constants.permissions import (
    USER_CREATE, USER_READ, USER_UPDATE, USER_DELETE, USER_ROLE_ASSIGN,
    ROLE_CREATE, ROLE_READ, ROLE_UPDATE,
)
from app.utils.formatters import api_response, paginated_response

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=dict)
def list_users(
    pagination: PaginationParams = Depends(get_pagination),
    db: Session = Depends(get_db),
    current_user=Depends(require_permissions([USER_READ])),
):
    svc = UserService(db)
    users, total = svc.list_users(current_user.tenant_id, skip=pagination.offset, limit=pagination.per_page)
    data = [{"id": u.id, "email": u.email, "first_name": u.first_name, "last_name": u.last_name, "user_type": u.user_type, "status": u.status} for u in users]
    return paginated_response(data, total, pagination.page, pagination.per_page)


@router.post("", response_model=dict)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permissions([USER_CREATE])),
):
    svc = UserService(db)
    user = svc.create(current_user.tenant_id, payload)
    return api_response(data={"id": user.id, "email": user.email}, message="User created successfully.")


@router.get("/{user_id}", response_model=dict)
def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_permissions([USER_READ])),
):
    svc = UserService(db)
    user = svc.get_by_id(current_user.tenant_id, user_id)
    return api_response(data={
        "id": user.id, "email": user.email, "first_name": user.first_name,
        "last_name": user.last_name, "user_type": user.user_type, "status": user.status,
        "roles": [{"id": r.id, "name": r.name} for r in user.roles],
    })


@router.put("/{user_id}", response_model=dict)
def update_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_permissions([USER_UPDATE])),
):
    svc = UserService(db)
    user = svc.update(current_user.tenant_id, user_id, payload)
    return api_response(data={"id": user.id, "email": user.email, "status": user.status}, message="User updated.")


@router.delete("/{user_id}", response_model=dict)
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(require_permissions([USER_DELETE])),
):
    svc = UserService(db)
    svc.deactivate(current_user.tenant_id, user_id)
    return api_response(message="User deactivated.")


@router.post("/{user_id}/roles", response_model=dict)
def assign_roles(
    user_id: str,
    payload: UserRoleAssign,
    db: Session = Depends(get_db),
    current_user=Depends(require_permissions([USER_ROLE_ASSIGN])),
):
    svc = UserService(db)
    user = svc.assign_roles(current_user.tenant_id, user_id, payload)
    return api_response(data={"id": user.id, "roles": [{"id": r.id, "name": r.name} for r in user.roles]}, message="Roles assigned.")


# Roles sub-resource
roles_router = APIRouter(prefix="/roles", tags=["Roles"])


@roles_router.get("", response_model=dict)
def list_roles(db: Session = Depends(get_db), current_user=Depends(require_permissions([ROLE_READ]))):
    svc = UserService(db)
    roles = svc.list_roles(current_user.tenant_id)
    return api_response(data=[{"id": r.id, "name": r.name, "is_system_role": r.is_system_role} for r in roles])


@roles_router.post("", response_model=dict)
def create_role(payload: RoleCreate, db: Session = Depends(get_db), current_user=Depends(require_permissions([ROLE_CREATE]))):
    svc = UserService(db)
    role = svc.create_role(current_user.tenant_id, payload.name, payload.description, payload.permission_ids)
    return api_response(data={"id": role.id, "name": role.name}, message="Role created.")


@roles_router.get("/{role_id}", response_model=dict)
def get_role(role_id: str, db: Session = Depends(get_db), current_user=Depends(require_permissions([ROLE_READ]))):
    svc = UserService(db)
    role = svc.get_role(current_user.tenant_id, role_id)
    return api_response(data={"id": role.id, "name": role.name, "permissions": [{"code": p.code} for p in role.permissions]})
