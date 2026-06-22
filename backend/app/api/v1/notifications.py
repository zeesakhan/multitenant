"""In-portal notification bell API.

Frontend polls GET /notifications every 60 s.
Notifications are created by backend services (AML, govt checks, workflow transitions).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_db, get_current_user, require_permissions
from app.schemas.base import APIResponse
from app.models.tenant import Tenant
from app.models.compliance import NotificationRecord
from app.constants.permissions import NOTIFICATION_READ

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=APIResponse)
def list_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(NOTIFICATION_READ)),
):
    """Return the current user's notifications (max 50, newest first)."""
    query = db.query(NotificationRecord).filter(
        NotificationRecord.tenant_id == tenant.id,
        NotificationRecord.recipient_user_id == current_user.id,
    )
    if unread_only:
        query = query.filter(NotificationRecord.is_read.is_(False))

    records = query.order_by(NotificationRecord.created_at.desc()).limit(50).all()
    unread_count = db.query(NotificationRecord).filter(
        NotificationRecord.tenant_id == tenant.id,
        NotificationRecord.recipient_user_id == current_user.id,
        NotificationRecord.is_read.is_(False),
    ).count()

    data = [
        {
            "id": r.id,
            "notification_type": r.notification_type,
            "title": r.title,
            "body": r.body,
            "related_entity_type": r.related_entity_type,
            "related_entity_id": r.related_entity_id,
            "is_read": r.is_read,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]

    return APIResponse(data={"notifications": data, "unread_count": unread_count})


@router.post("/{notification_id}/read", response_model=APIResponse)
def mark_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(NOTIFICATION_READ)),
):
    """Mark a notification as read."""
    record = db.query(NotificationRecord).filter(
        NotificationRecord.tenant_id == tenant.id,
        NotificationRecord.id == notification_id,
        NotificationRecord.recipient_user_id == current_user.id,
    ).first()

    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    record.is_read = True
    db.commit()
    return APIResponse(data={"id": notification_id, "is_read": True})


@router.post("/read-all", response_model=APIResponse)
def mark_all_read(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    tenant: Tenant = Depends(require_permissions(NOTIFICATION_READ)),
):
    """Mark all of the current user's notifications as read."""
    updated = db.query(NotificationRecord).filter(
        NotificationRecord.tenant_id == tenant.id,
        NotificationRecord.recipient_user_id == current_user.id,
        NotificationRecord.is_read.is_(False),
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()
    return APIResponse(data={"marked_read": updated})
