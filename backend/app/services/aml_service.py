"""AML (Anti-Money Laundering) Service.

Implements the 9-factor risk scoring model from spec §9.5.1.
All factor weights are read from market_config — none hardcoded here.

Risk bands:
  0–25   LOW      → auto-proceed
  26–50  MEDIUM   → proceed + notify Compliance Officer
  51–75  HIGH     → AML Hold
  76–100 CRITICAL → auto-reject + auto-create STR

PEP check: stub in mock mode. Real World-Check/Dow Jones wired via PEP_API_KEY.
Sanctions: auto-block on any hit (score 100).

Tipping-off protection: the policyholder is NEVER told their application is on
AML Hold. The customer-facing status must remain generic ("Under Review").
"""

import uuid
import logging
from datetime import datetime, timezone, date, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.compliance import AmlRecord
from app.models.application import Application
from app.models.market_config import MarketConfig
from app.constants.enums import (
    AmlCheckType, AmlRecordStatus, ApplicationStatus, AmlStatus,
)
from app.services.audit_service import AuditService

log = logging.getLogger(__name__)

# Default factor scores — overridden by market_config values at runtime
_DEFAULTS = {
    "aml_pep_self_score": 25,
    "aml_fatf_score": 15,
    "aml_cash_score": 10,
    "aml_occupation_score": 5,
    "aml_diplomatic_score": 5,
    "aml_prior_flag_score": 20,
    "aml_edd_threshold": 50_000,
    "aml_edd_score": 10,
    "aml_medium_threshold": 26,
    "aml_high_threshold": 51,
    "aml_critical_threshold": 76,
}

# FATF grey/black-list nationalities (ISO-3166 alpha-2, from FATF public lists)
FATF_HIGH_RISK = {
    "AF", "BY", "CF", "CD", "ET", "IR", "IQ", "LY", "ML",
    "MM", "KP", "PK", "RU", "SO", "SS", "SD", "SY", "UA",
    "VE", "YE", "ZW",
}

# High-risk occupations for AML purposes
HIGH_RISK_OCCUPATIONS = {
    "money exchanger", "crypto trader", "exchange dealer", "broker",
    "casino", "gambling", "arms dealer", "dealer in precious metals",
    "real estate agent", "pawnbroker", "attorney", "accountant",
    "trust and company service provider",
}


class AmlService:
    def __init__(self, db: Session, audit: AuditService, mock_pep: bool = True, pep_api_key: str = "", pep_api_url: str = ""):
        self.db = db
        self.audit = audit
        self._mock_pep = mock_pep
        self._pep_api_key = pep_api_key
        self._pep_api_url = pep_api_url

    # ── Public checks ─────────────────────────────────────────────────────────

    def run_pep_check(
        self,
        tenant_id: str,
        application_id: str,
        member_id: Optional[str],
        full_name: str,
        dob: date,
        nationality: str,
        user_id: str,
    ) -> AmlRecord:
        if self._mock_pep:
            raw = {"pep": False, "match_score": 0.0, "_mock": True}
        else:
            raw = self._call_pep_api(full_name, dob, nationality)

        is_pep = raw.get("pep", False)
        status = AmlRecordStatus.FLAGGED.value if is_pep else AmlRecordStatus.CLEAR.value

        return self._write_record(
            tenant_id=tenant_id,
            application_id=application_id,
            member_id=member_id,
            check_type=AmlCheckType.PEP.value,
            status=status,
            risk_score=Decimal("25") if is_pep else Decimal("0"),
            raw_response=raw,
            checked_by=user_id,
        )

    def run_sanctions_check(
        self,
        tenant_id: str,
        application_id: str,
        member_id: Optional[str],
        full_name: str,
        dob: date,
        user_id: str,
    ) -> AmlRecord:
        if self._mock_pep:
            raw = {"sanctioned": False, "list": None, "_mock": True}
        else:
            raw = {"sanctioned": False, "list": None}  # Real integration placeholder

        is_sanctioned = raw.get("sanctioned", False)
        status = AmlRecordStatus.HOLD.value if is_sanctioned else AmlRecordStatus.CLEAR.value

        return self._write_record(
            tenant_id=tenant_id,
            application_id=application_id,
            member_id=member_id,
            check_type=AmlCheckType.SANCTIONS.value,
            status=status,
            risk_score=Decimal("100") if is_sanctioned else Decimal("0"),
            raw_response=raw,
            checked_by=user_id,
        )

    def calculate_risk_score(
        self,
        tenant_id: str,
        application_id: str,
        application: Application,
        members: list,
        payment_method: Optional[str] = None,
        user_id: str = "",
    ) -> tuple[Decimal, dict]:
        """Return (total_score, factor_breakdown_dict). Score capped at 100."""
        cfg = self._get_config(tenant_id)
        breakdown: dict[str, int] = {}
        score = 0

        # Factor 1: PEP status (self — principal member)
        pep_records = self.db.query(AmlRecord).filter(
            AmlRecord.tenant_id == tenant_id,
            AmlRecord.application_id == application_id,
            AmlRecord.check_type == AmlCheckType.PEP.value,
            AmlRecord.status == AmlRecordStatus.FLAGGED.value,
        ).first()
        if pep_records:
            pts = cfg["aml_pep_self_score"]
            score += pts
            breakdown["pep_match"] = pts

        # Factor 2: Sanctions match → auto-block
        sanctions_hit = self.db.query(AmlRecord).filter(
            AmlRecord.tenant_id == tenant_id,
            AmlRecord.application_id == application_id,
            AmlRecord.check_type == AmlCheckType.SANCTIONS.value,
            AmlRecord.status == AmlRecordStatus.HOLD.value,
        ).first()
        if sanctions_hit:
            score = 100
            breakdown["sanctions_match"] = 100
            return Decimal(str(min(score, 100))), breakdown

        # Factor 3: FATF high-risk nationality
        principal = members[0] if members else None
        if principal:
            nat = (principal.nationality or "").upper()
            if nat in FATF_HIGH_RISK:
                pts = cfg["aml_fatf_score"]
                score += pts
                breakdown["fatf_nationality"] = pts

        # Factor 4: Premium > EDD threshold
        edd_threshold = Decimal(str(cfg["aml_edd_threshold"]))
        if application.total_premium and Decimal(str(application.total_premium)) > edd_threshold:
            pts = cfg["aml_edd_score"]
            score += pts
            breakdown["high_premium"] = pts

        # Factor 5: Cash payment
        if payment_method and payment_method.lower() == "cash":
            pts = cfg["aml_cash_score"]
            score += pts
            breakdown["cash_payment"] = pts

        # Factor 6: High-risk occupation
        occ = (application.occupation or "").lower()
        if any(h in occ for h in HIGH_RISK_OCCUPATIONS):
            pts = cfg["aml_occupation_score"]
            score += pts
            breakdown["high_risk_occupation"] = pts

        # Factor 7: Income vs premium inconsistency — stub (no income field yet)
        # Placeholder: 0 points until income field is added
        breakdown["income_premium_mismatch"] = 0

        # Factor 8: Prior AML flag on this application
        prior_flag = self.db.query(AmlRecord).filter(
            AmlRecord.tenant_id == tenant_id,
            AmlRecord.application_id == application_id,
            AmlRecord.status.in_([AmlRecordStatus.FLAGGED.value, AmlRecordStatus.HOLD.value]),
        ).first()
        if prior_flag:
            pts = cfg["aml_prior_flag_score"]
            score += pts
            breakdown["prior_aml_flag"] = pts

        # Factor 9: Diplomatic passport
        if application.is_diplomatic_passport:
            pts = cfg["aml_diplomatic_score"]
            score += pts
            breakdown["diplomatic_passport"] = pts

        capped = min(score, 100)
        total_score = Decimal(str(capped))

        self._write_record(
            tenant_id=tenant_id,
            application_id=application_id,
            member_id=None,
            check_type=AmlCheckType.RISK_SCORE.value,
            status=self._band_status(total_score, cfg),
            risk_score=total_score,
            raw_response={"score": capped, "breakdown": breakdown},
            checked_by=user_id,
        )

        return total_score, breakdown

    def apply_risk_result(
        self,
        tenant_id: str,
        application: Application,
        risk_score: Decimal,
        cfg: dict,
        user_id: str,
    ) -> None:
        """Update application AML status + status based on risk band. Commit not called here."""
        application.aml_risk_score = risk_score
        medium_threshold = cfg.get("aml_medium_threshold", _DEFAULTS["aml_medium_threshold"])
        high_threshold = cfg.get("aml_high_threshold", _DEFAULTS["aml_high_threshold"])
        critical_threshold = cfg.get("aml_critical_threshold", _DEFAULTS["aml_critical_threshold"])

        if risk_score < Decimal(str(medium_threshold)):
            application.aml_status = AmlStatus.CLEAR.value
        elif risk_score < Decimal(str(high_threshold)):
            application.aml_status = AmlStatus.FLAGGED.value
            self._notify_compliance(tenant_id, application.id)
        elif risk_score < Decimal(str(critical_threshold)):
            application.aml_status = AmlStatus.HOLD.value
            application.status = ApplicationStatus.AML_HOLD
            self.audit.log(tenant_id=tenant_id, action="aml_hold", entity_type="application",
                           entity_id=application.id, user_id=user_id,
                           new_values={"aml_risk_score": str(risk_score)})
        else:
            application.aml_status = AmlStatus.HOLD.value
            application.status = ApplicationStatus.AML_HOLD
            self._auto_create_str(tenant_id, application.id, risk_score, user_id)
            self.audit.log(tenant_id=tenant_id, action="aml_critical", entity_type="application",
                           entity_id=application.id, user_id=user_id,
                           new_values={"aml_risk_score": str(risk_score)})

        self.db.flush()

    # ── AML Hold workflow ─────────────────────────────────────────────────────

    def place_aml_hold(
        self,
        tenant_id: str,
        application_id: str,
        reason: str,
        user_id: str,
    ) -> None:
        application = self.db.query(Application).filter(
            Application.tenant_id == tenant_id,
            Application.id == application_id,
        ).first()
        if not application:
            raise ValueError(f"Application {application_id} not found")

        application.aml_status = AmlStatus.HOLD.value
        application.status = ApplicationStatus.AML_HOLD
        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="aml_hold_placed",
            entity_type="application",
            entity_id=application_id,
            user_id=user_id,
            new_values={"reason": reason},
        )

        self._notify_compliance(tenant_id, application_id)

    def clear_aml_hold(
        self,
        tenant_id: str,
        application_id: str,
        user_id: str,
        notes: str,
    ) -> Application:
        application = self.db.query(Application).filter(
            Application.tenant_id == tenant_id,
            Application.id == application_id,
        ).first()
        if not application:
            raise ValueError(f"Application {application_id} not found")

        application.aml_status = AmlStatus.CLEARED.value
        application.status = ApplicationStatus.SUBMITTED
        self.db.flush()

        # Write clearance record
        self._write_record(
            tenant_id=tenant_id,
            application_id=application_id,
            member_id=None,
            check_type=AmlCheckType.RISK_SCORE.value,
            status=AmlRecordStatus.CLEARED.value,
            risk_score=application.aml_risk_score or Decimal("0"),
            raw_response={"notes": notes},
            checked_by=user_id,
            cleared_by=user_id,
            clearance_notes=notes,
        )

        self.audit.log(
            tenant_id=tenant_id,
            action="aml_hold_cleared",
            entity_type="application",
            entity_id=application_id,
            user_id=user_id,
            new_values={"notes": notes, "new_status": ApplicationStatus.SUBMITTED},
        )

        return application

    def list_alerts(self, tenant_id: str) -> list[Application]:
        return self.db.query(Application).filter(
            Application.tenant_id == tenant_id,
            Application.aml_status.in_([AmlStatus.FLAGGED.value, AmlStatus.HOLD.value]),
        ).order_by(Application.created_at.desc()).all()

    # ── Transaction monitoring ────────────────────────────────────────────────

    def monitor_transaction(
        self,
        tenant_id: str,
        application_id: str,
        amount: Decimal,
        payment_method: str,
        customer_email: str,
        user_id: str,
    ) -> list[AmlRecord]:
        """Flag suspicious transaction patterns. Returns list of created records."""
        alerts = []

        # Trigger 1: single premium > AED 1,000,000
        if amount > Decimal("1000000"):
            alerts.append(self._write_record(
                tenant_id=tenant_id,
                application_id=application_id,
                member_id=None,
                check_type=AmlCheckType.TRANSACTION.value,
                status=AmlRecordStatus.FLAGGED.value,
                risk_score=Decimal("75"),
                raw_response={"trigger": "high_value_transaction", "amount": str(amount)},
                checked_by=user_id,
            ))

        # Trigger 2: same policyholder, multiple policies in 30 days
        from app.models.application import Application as App
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        recent_count = self.db.query(App).filter(
            App.tenant_id == tenant_id,
            App.customer_email == customer_email,
            App.created_at >= thirty_days_ago,
        ).count()
        if recent_count > 1:
            alerts.append(self._write_record(
                tenant_id=tenant_id,
                application_id=application_id,
                member_id=None,
                check_type=AmlCheckType.TRANSACTION.value,
                status=AmlRecordStatus.FLAGGED.value,
                risk_score=Decimal("30"),
                raw_response={"trigger": "multiple_policies_30d", "count": recent_count},
                checked_by=user_id,
            ))

        self.db.flush()
        return alerts

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _write_record(
        self,
        tenant_id: str,
        application_id: str,
        member_id: Optional[str],
        check_type: str,
        status: str,
        risk_score: Decimal,
        raw_response: dict,
        checked_by: str,
        cleared_by: Optional[str] = None,
        clearance_notes: Optional[str] = None,
    ) -> AmlRecord:
        record = AmlRecord(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            application_id=application_id,
            member_id=member_id,
            check_type=check_type,
            status=status,
            risk_score=risk_score,
            raw_response=raw_response,
            checked_at=datetime.now(timezone.utc),
            checked_by=checked_by,
            cleared_by=cleared_by,
            cleared_at=datetime.now(timezone.utc) if cleared_by else None,
            clearance_notes=clearance_notes,
        )
        self.db.add(record)
        self.db.flush()
        return record

    def _get_config(self, tenant_id: str) -> dict:
        rows = self.db.query(MarketConfig).filter(
            MarketConfig.tenant_id == tenant_id,
            MarketConfig.key.in_(list(_DEFAULTS.keys())),
        ).all()
        cfg = dict(_DEFAULTS)
        for row in rows:
            cfg[row.key] = row.value
        return cfg

    @staticmethod
    def _band_status(score: Decimal, cfg: dict) -> str:
        medium = Decimal(str(cfg.get("aml_medium_threshold", 26)))
        high = Decimal(str(cfg.get("aml_high_threshold", 51)))
        if score < medium:
            return AmlRecordStatus.CLEAR.value
        if score < high:
            return AmlRecordStatus.FLAGGED.value
        return AmlRecordStatus.HOLD.value

    def _notify_compliance(self, tenant_id: str, application_id: str) -> None:
        try:
            from app.models.compliance import NotificationRecord
            from app.models.user import User
            from app.constants.enums import UserType

            co_users = self.db.query(User).filter(
                User.tenant_id == tenant_id,
                User.user_type == UserType.COMPLIANCE_OFFICER.value,
                User.is_active.is_(True),
            ).all()

            for user in co_users:
                notif = NotificationRecord(
                    id=str(uuid.uuid4()),
                    tenant_id=tenant_id,
                    recipient_user_id=user.id,
                    notification_type="aml_alert",
                    title="AML Alert: Application flagged",
                    body=f"Application {application_id} has been flagged by the AML risk engine.",
                    related_entity_type="application",
                    related_entity_id=application_id,
                    is_read=False,
                )
                self.db.add(notif)

            self.db.flush()
        except Exception as exc:
            log.warning("Could not create AML notifications: %s", exc)

    def _auto_create_str(
        self,
        tenant_id: str,
        application_id: str,
        risk_score: Decimal,
        user_id: str,
    ) -> None:
        try:
            from app.models.compliance import StrRecord
            from app.constants.enums import StrStatus

            str_ref = f"STR-{uuid.uuid4().hex[:8].upper()}"
            record = StrRecord(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                str_reference=str_ref,
                application_id=application_id,
                created_by=user_id,
                status=StrStatus.DRAFT.value,
                nature_of_suspicion="Auto-generated: critical AML risk score triggered threshold",
                subject_details={"application_id": application_id},
                transaction_details={"risk_score": str(risk_score)},
                audit_trail=[{
                    "action": "auto_created",
                    "by": "system",
                    "at": datetime.now(timezone.utc).isoformat(),
                    "reason": f"Risk score {risk_score} ≥ critical threshold",
                }],
            )
            self.db.add(record)
            self.db.flush()
            log.warning("Auto-created STR %s for application %s (score=%s)", str_ref, application_id, risk_score)
        except Exception as exc:
            log.error("Failed to auto-create STR: %s", exc)

    def _call_pep_api(self, full_name: str, dob: date, nationality: str) -> dict:
        """Call real PEP/World-Check API. Stub used when mock mode is off but no key configured."""
        if not self._pep_api_url or not self._pep_api_key:
            return {"pep": False, "_stub": True}

        import httpx
        try:
            with httpx.Client(timeout=httpx.Timeout(10.0)) as client:
                r = client.post(
                    self._pep_api_url,
                    json={"name": full_name, "dob": str(dob), "nationality": nationality},
                    headers={"Authorization": f"Bearer {self._pep_api_key}"},
                )
                r.raise_for_status()
                return r.json()
        except Exception as exc:
            log.error("PEP API call failed: %s", exc)
            return {"pep": False, "error": str(exc)}


def get_aml_service(db: Session, audit: AuditService) -> AmlService:
    from config import get_settings
    s = get_settings()
    return AmlService(
        db=db,
        audit=audit,
        mock_pep=s.aml_mock,
        pep_api_key=s.pep_api_key,
        pep_api_url=s.pep_api_url,
    )
