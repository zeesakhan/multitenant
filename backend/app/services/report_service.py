from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.models.policy import Policy
from app.models.application import Application
from app.models.payment import Payment
from app.models.claim import Claim
from app.constants.enums import PolicyStatus, ApplicationStatus, PaymentStatus, ClaimStatus
from datetime import datetime, timezone, timedelta


def _month_label(column, dialect_name: str):
    """Return a DB-agnostic year-month expression ('YYYY-MM')."""
    if dialect_name == "postgresql":
        return func.to_char(column, "YYYY-MM")
    return func.strftime("%Y-%m", column)


class ReportService:
    def __init__(self, db: Session):
        self.db = db

    @property
    def _dialect(self) -> str:
        bind = self.db.get_bind()
        return bind.dialect.name if bind else "sqlite"

    def summary(self, tenant_id: str) -> dict:
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        active_policies = self.db.query(Policy).filter(
            and_(Policy.tenant_id == tenant_id, Policy.status == PolicyStatus.ACTIVE)
        ).count()

        expiring_soon = self.db.query(Policy).filter(
            and_(
                Policy.tenant_id == tenant_id,
                Policy.status == PolicyStatus.ACTIVE,
                Policy.expiry_date <= now + timedelta(days=30),
            )
        ).count()

        pending_apps = self.db.query(Application).filter(
            and_(Application.tenant_id == tenant_id,
                 Application.status == ApplicationStatus.SUBMITTED)
        ).count()

        open_claims = self.db.query(Claim).filter(
            and_(Claim.tenant_id == tenant_id,
                 Claim.status.in_([ClaimStatus.SUBMITTED, ClaimStatus.UNDER_REVIEW]))
        ).count()

        monthly_premium = float(
            self.db.query(func.sum(Policy.total_premium))
            .filter(and_(Policy.tenant_id == tenant_id, Policy.status == PolicyStatus.ACTIVE))
            .scalar() or 0
        )

        month_collected = float(
            self.db.query(func.sum(Payment.amount))
            .filter(and_(
                Payment.tenant_id == tenant_id,
                Payment.status == PaymentStatus.SUCCESS,
                Payment.paid_at >= month_start,
            )).scalar() or 0
        )

        claims_paid_month = float(
            self.db.query(func.sum(Claim.approved_amount))
            .filter(and_(
                Claim.tenant_id == tenant_id,
                Claim.status == ClaimStatus.PAID,
                Claim.paid_at >= month_start,
            )).scalar() or 0
        )

        return {
            "active_policies": active_policies,
            "expiring_soon_30d": expiring_soon,
            "pending_applications": pending_apps,
            "open_claims": open_claims,
            "monthly_premium_due": monthly_premium,
            "collected_this_month": month_collected,
            "claims_paid_this_month": claims_paid_month,
        }

    def applications_by_month(self, tenant_id: str, months: int = 6) -> list:
        cutoff = datetime.now(timezone.utc) - timedelta(days=30 * months)
        month_expr = _month_label(Application.created_at, self._dialect).label("month")
        rows = (
            self.db.query(month_expr, Application.status, func.count(Application.id).label("count"))
            .filter(and_(Application.tenant_id == tenant_id, Application.created_at >= cutoff))
            .group_by(month_expr, Application.status)
            .order_by(month_expr)
            .all()
        )
        result: dict = {}
        for row in rows:
            m = row.month
            if m not in result:
                result[m] = {"month": m, "total": 0}
            result[m][row.status] = row.count
            result[m]["total"] += row.count
        return list(result.values())

    def premium_by_month(self, tenant_id: str, months: int = 6) -> list:
        cutoff = datetime.now(timezone.utc) - timedelta(days=30 * months)
        month_expr = _month_label(Payment.paid_at, self._dialect).label("month")
        rows = (
            self.db.query(
                month_expr,
                func.sum(Payment.amount).label("collected"),
                func.count(Payment.id).label("payments"),
            )
            .filter(and_(
                Payment.tenant_id == tenant_id,
                Payment.status == PaymentStatus.SUCCESS,
                Payment.paid_at >= cutoff,
            ))
            .group_by(month_expr)
            .order_by(month_expr)
            .all()
        )
        return [{"month": r.month, "collected": float(r.collected), "payments": r.payments} for r in rows]

    def claims_by_month(self, tenant_id: str, months: int = 6) -> list:
        cutoff = datetime.now(timezone.utc) - timedelta(days=30 * months)
        month_expr = _month_label(Claim.created_at, self._dialect).label("month")
        rows = (
            self.db.query(
                month_expr,
                Claim.status,
                func.count(Claim.id).label("count"),
                func.sum(Claim.claimed_amount).label("total_claimed"),
            )
            .filter(and_(Claim.tenant_id == tenant_id, Claim.created_at >= cutoff))
            .group_by(month_expr, Claim.status)
            .order_by(month_expr)
            .all()
        )
        result: dict = {}
        for row in rows:
            m = row.month
            if m not in result:
                result[m] = {"month": m, "total": 0, "total_claimed": 0.0}
            result[m][row.status] = row.count
            result[m]["total"] += row.count
            result[m]["total_claimed"] += float(row.total_claimed or 0)
        return list(result.values())
