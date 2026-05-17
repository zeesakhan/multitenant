from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.policy import Policy
from app.models.application import Application
from app.models.payment import Payment
from app.models.user import User
from app.constants.enums import PolicyStatus, ApplicationStatus, PaymentStatus


class DashboardService:
    def __init__(self, db: Session):
        self.db = db

    def get_stats(self, tenant_id: str) -> dict:
        # Policies
        total_policies = self.db.query(Policy).filter(Policy.tenant_id == tenant_id).count()
        active_policies = self.db.query(Policy).filter(
            and_(Policy.tenant_id == tenant_id, Policy.status == PolicyStatus.ACTIVE)
        ).count()

        monthly_premium = float(
            self.db.query(func.sum(Policy.total_premium))
            .filter(and_(Policy.tenant_id == tenant_id, Policy.status == PolicyStatus.ACTIVE))
            .scalar() or 0
        )

        # Applications
        total_applications = self.db.query(Application).filter(Application.tenant_id == tenant_id).count()

        app_by_status_rows = (
            self.db.query(Application.status, func.count(Application.id))
            .filter(Application.tenant_id == tenant_id)
            .group_by(Application.status)
            .all()
        )
        applications_by_status = {row[0]: row[1] for row in app_by_status_rows}

        # Payments
        total_collected = float(
            self.db.query(func.sum(Payment.amount))
            .filter(and_(Payment.tenant_id == tenant_id, Payment.status == PaymentStatus.SUCCESS))
            .scalar() or 0
        )
        total_payments = self.db.query(Payment).filter(Payment.tenant_id == tenant_id).count()

        # Users
        total_users = self.db.query(User).filter(User.tenant_id == tenant_id).count()

        # Recent applications (last 5)
        recent_apps = (
            self.db.query(Application)
            .filter(Application.tenant_id == tenant_id)
            .order_by(Application.created_at.desc())
            .limit(5)
            .all()
        )

        # Recent payments (last 5)
        recent_payments = (
            self.db.query(Payment)
            .filter(Payment.tenant_id == tenant_id)
            .order_by(Payment.paid_at.desc())
            .limit(5)
            .all()
        )

        return {
            "policies": {
                "total": total_policies,
                "active": active_policies,
                "monthly_premium": monthly_premium,
            },
            "applications": {
                "total": total_applications,
                "by_status": applications_by_status,
            },
            "payments": {
                "total": total_payments,
                "total_collected": total_collected,
            },
            "users": {
                "total": total_users,
            },
            "recent_applications": [
                {
                    "id": a.id,
                    "application_number": a.application_number,
                    "customer_name": a.customer_name,
                    "status": a.status,
                    "created_at": a.created_at.isoformat(),
                }
                for a in recent_apps
            ],
            "recent_payments": [
                {
                    "id": p.id,
                    "payment_number": p.payment_number,
                    "policy_id": p.policy_id,
                    "amount": float(p.amount),
                    "method": p.method,
                    "paid_at": p.paid_at.isoformat(),
                }
                for p in recent_payments
            ],
        }
