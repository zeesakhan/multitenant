from sqlalchemy.orm import Session
from app.models.audit import AuditLog
from app.constants.enums import AuditAction
from typing import Optional, Any
import uuid


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        tenant_id: str,
        action: AuditAction,
        entity_type: str,
        entity_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        old_values: Optional[dict] = None,
        new_values: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> AuditLog:
        entry = AuditLog(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            user_id=user_id,
            user_email=user_email,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            old_values=old_values,
            new_values=new_values,
            ip_address=ip_address,
            user_agent=user_agent,
            description=description,
            metadata=metadata,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def log_create(self, tenant_id: str, entity_type: str, entity_id: str, new_values: dict, **kwargs) -> AuditLog:
        return self.log(tenant_id, AuditAction.CREATE, entity_type, entity_id, new_values=new_values, **kwargs)

    def log_update(self, tenant_id: str, entity_type: str, entity_id: str, old_values: dict, new_values: dict, **kwargs) -> AuditLog:
        return self.log(tenant_id, AuditAction.UPDATE, entity_type, entity_id, old_values=old_values, new_values=new_values, **kwargs)

    def log_delete(self, tenant_id: str, entity_type: str, entity_id: str, old_values: dict, **kwargs) -> AuditLog:
        return self.log(tenant_id, AuditAction.DELETE, entity_type, entity_id, old_values=old_values, **kwargs)

    def log_login(self, tenant_id: str, user_id: str, user_email: str, **kwargs) -> AuditLog:
        return self.log(tenant_id, AuditAction.LOGIN, "User", user_id, user_id=user_id, user_email=user_email, **kwargs)
