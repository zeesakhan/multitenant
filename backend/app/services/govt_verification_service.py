"""UAE Government Verification Service.

Handles:
  - ICP (Identity & Citizenship): Emirates ID validation
  - DHA (Dubai Health Authority): member eligibility
  - OFAC, UN Sanctions, UAE Cabinet 74: sanctions list checks

In mock mode (GOVT_API_MOCK=true, default): returns pre-built responses
immediately — no network calls, no credentials needed.

In live mode: calls real APIs with 10 s timeout, 3 retries, exponential backoff.
Results cached in Redis for 90 days (successful only).
Failed checks are written as `pending` and flagged for manual review.

All calls write a GovtVerificationRecord for the audit trail.
"""

import uuid
import logging
from datetime import datetime, timezone, date
from typing import Optional
from sqlalchemy.orm import Session
import httpx

from app.models.compliance import GovtVerificationRecord
from app.constants.enums import GovtCheckType, GovtVerificationStatus
from app.services.audit_service import AuditService

log = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(10.0)
_CACHE_TTL_SECONDS = 90 * 24 * 3600  # 90 days


class VerificationResult:
    def __init__(self, status: str, matched: bool, raw: dict, record_id: str):
        self.status = status
        self.matched = matched
        self.raw = raw
        self.record_id = record_id

    @property
    def passed(self) -> bool:
        return self.status == GovtVerificationStatus.VERIFIED.value and not self.matched


class GovtVerificationService:
    def __init__(self, db: Session, audit: AuditService, mock: bool = True,
                 icp_url: str = "", icp_key: str = "",
                 dha_url: str = "", dha_key: str = ""):
        self.db = db
        self.audit = audit
        self._mock = mock
        self._icp_url = icp_url
        self._icp_key = icp_key
        self._dha_url = dha_url
        self._dha_key = dha_key

    # ── ICP ───────────────────────────────────────────────────────────────────

    def verify_icp(
        self,
        tenant_id: str,
        application_id: str,
        member_id: Optional[str],
        emirates_id: str,
        full_name: str,
        dob: date,
        user_id: str,
    ) -> VerificationResult:
        cache_key = f"icp:{emirates_id}"
        cached = self._cache_get(cache_key)
        if cached:
            return self._record_and_return(
                tenant_id, application_id, member_id,
                GovtCheckType.ICP.value, cached, user_id,
            )

        request_payload = {
            "emirates_id": emirates_id,
            "full_name": full_name,
            "date_of_birth": str(dob),
        }

        if self._mock:
            response_payload = {
                "status": "verified",
                "matched": True,
                "name_match_score": 0.98,
                "emirates_id": emirates_id,
                "_mock": True,
            }
        else:
            response_payload = self._call_api(
                method="POST",
                url=f"{self._icp_url}/verify",
                headers={"Authorization": f"Bearer {self._icp_key}"},
                payload=request_payload,
                fallback={"status": "pending", "matched": False, "error": "API unavailable"},
            )

        status = (
            GovtVerificationStatus.VERIFIED.value
            if response_payload.get("status") == "verified"
            else GovtVerificationStatus.PENDING.value
        )

        if status == GovtVerificationStatus.VERIFIED.value:
            self._cache_set(cache_key, {"status": status, "matched": response_payload.get("matched", False), "raw": response_payload})

        return self._record_and_return(
            tenant_id, application_id, member_id,
            GovtCheckType.ICP.value,
            {"status": status, "matched": response_payload.get("matched", False), "raw": response_payload},
            user_id,
            request_payload=request_payload,
        )

    # ── DHA ───────────────────────────────────────────────────────────────────

    def check_dha(
        self,
        tenant_id: str,
        application_id: str,
        member_id: Optional[str],
        emirates_id: str,
        plan_data: dict,
        user_id: str,
    ) -> VerificationResult:
        cache_key = f"dha:{emirates_id}"
        cached = self._cache_get(cache_key)
        if cached:
            return self._record_and_return(
                tenant_id, application_id, member_id,
                GovtCheckType.DHA.value, cached, user_id,
            )

        request_payload = {"emirates_id": emirates_id, "plan": plan_data}

        if self._mock:
            response_payload = {"status": "verified", "eligible": True, "_mock": True}
        else:
            response_payload = self._call_api(
                method="POST",
                url=f"{self._dha_url}/eligibility",
                headers={"Authorization": f"Bearer {self._dha_key}"},
                payload=request_payload,
                fallback={"status": "pending", "eligible": False, "error": "API unavailable"},
            )

        status = (
            GovtVerificationStatus.VERIFIED.value
            if response_payload.get("status") == "verified"
            else GovtVerificationStatus.PENDING.value
        )

        return self._record_and_return(
            tenant_id, application_id, member_id,
            GovtCheckType.DHA.value,
            {"status": status, "matched": False, "raw": response_payload},
            user_id,
            request_payload=request_payload,
        )

    # ── Sanctions ─────────────────────────────────────────────────────────────

    def check_ofac(
        self,
        tenant_id: str,
        application_id: str,
        member_id: Optional[str],
        full_name: str,
        dob: date,
        nationality: str,
        user_id: str,
    ) -> VerificationResult:
        return self._run_sanctions_check(
            tenant_id, application_id, member_id,
            GovtCheckType.OFAC.value,
            {"full_name": full_name, "date_of_birth": str(dob), "nationality": nationality},
            user_id,
        )

    def check_un_sanctions(
        self,
        tenant_id: str,
        application_id: str,
        member_id: Optional[str],
        full_name: str,
        dob: date,
        user_id: str,
    ) -> VerificationResult:
        return self._run_sanctions_check(
            tenant_id, application_id, member_id,
            GovtCheckType.UN_SANCTIONS.value,
            {"full_name": full_name, "date_of_birth": str(dob)},
            user_id,
        )

    def check_uae_cabinet74(
        self,
        tenant_id: str,
        application_id: str,
        member_id: Optional[str],
        full_name: str,
        dob: date,
        user_id: str,
    ) -> VerificationResult:
        return self._run_sanctions_check(
            tenant_id, application_id, member_id,
            GovtCheckType.UAE_CABINET_74.value,
            {"full_name": full_name, "date_of_birth": str(dob)},
            user_id,
        )

    def run_all_sanctions(
        self,
        tenant_id: str,
        application_id: str,
        member_id: Optional[str],
        full_name: str,
        dob: date,
        nationality: str,
        user_id: str,
    ) -> list[VerificationResult]:
        return [
            self.check_ofac(tenant_id, application_id, member_id, full_name, dob, nationality, user_id),
            self.check_un_sanctions(tenant_id, application_id, member_id, full_name, dob, user_id),
            self.check_uae_cabinet74(tenant_id, application_id, member_id, full_name, dob, user_id),
        ]

    # ── Override ──────────────────────────────────────────────────────────────

    def override_check(
        self,
        tenant_id: str,
        record_id: str,
        user_id: str,
        justification: str,
    ) -> GovtVerificationRecord:
        record = self.db.query(GovtVerificationRecord).filter(
            GovtVerificationRecord.tenant_id == tenant_id,
            GovtVerificationRecord.id == record_id,
        ).first()
        if not record:
            raise ValueError(f"GovtVerificationRecord {record_id} not found")

        record.status = GovtVerificationStatus.OVERRIDDEN.value
        record.overridden_by = user_id
        record.override_justification = justification
        record.resolved_at = datetime.now(timezone.utc)
        self.db.flush()

        self.audit.log(
            tenant_id=tenant_id,
            action="override",
            entity_type="govt_verification_record",
            entity_id=record_id,
            user_id=user_id,
            new_values={"status": GovtVerificationStatus.OVERRIDDEN.value, "justification": justification},
        )

        return record

    def list_pending(self, tenant_id: str) -> list[GovtVerificationRecord]:
        return self.db.query(GovtVerificationRecord).filter(
            GovtVerificationRecord.tenant_id == tenant_id,
            GovtVerificationRecord.status.in_([
                GovtVerificationStatus.PENDING.value,
                GovtVerificationStatus.FAILED.value,
            ]),
        ).order_by(GovtVerificationRecord.created_at.desc()).all()

    # ── Internals ─────────────────────────────────────────────────────────────

    def _run_sanctions_check(
        self,
        tenant_id: str,
        application_id: str,
        member_id: Optional[str],
        check_type: str,
        request_payload: dict,
        user_id: str,
    ) -> VerificationResult:
        if self._mock:
            response_payload = {"status": "verified", "matched": False, "_mock": True}
        else:
            response_payload = self._call_api(
                method="POST",
                url=f"https://sanctions-api.example.com/{check_type}",
                headers={},
                payload=request_payload,
                fallback={"status": "pending", "matched": False, "error": "API unavailable"},
            )

        matched = response_payload.get("matched", False)
        status = (
            GovtVerificationStatus.MISMATCH.value if matched
            else GovtVerificationStatus.VERIFIED.value
            if response_payload.get("status") == "verified"
            else GovtVerificationStatus.PENDING.value
        )

        return self._record_and_return(
            tenant_id, application_id, member_id, check_type,
            {"status": status, "matched": matched, "raw": response_payload},
            user_id,
            request_payload=request_payload,
        )

    def _record_and_return(
        self,
        tenant_id: str,
        application_id: str,
        member_id: Optional[str],
        check_type: str,
        result: dict,
        user_id: str,
        request_payload: dict = None,
    ) -> VerificationResult:
        record = GovtVerificationRecord(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            application_id=application_id,
            member_id=member_id,
            check_type=check_type,
            status=result["status"],
            request_payload=request_payload or {},
            response_payload=result.get("raw", result),
            triggered_at=datetime.now(timezone.utc),
            resolved_at=datetime.now(timezone.utc) if result["status"] not in ("pending",) else None,
        )
        self.db.add(record)
        self.db.flush()

        return VerificationResult(
            status=result["status"],
            matched=result.get("matched", False),
            raw=result.get("raw", result),
            record_id=record.id,
        )

    def _cache_get(self, key: str) -> Optional[dict]:
        try:
            from app.cache.redis_client import get_redis
            import json
            r = get_redis()
            val = r.get(key)
            if val:
                return json.loads(val)
        except Exception:
            pass
        return None

    def _cache_set(self, key: str, value: dict) -> None:
        try:
            from app.cache.redis_client import get_redis
            import json
            r = get_redis()
            r.setex(key, _CACHE_TTL_SECONDS, json.dumps(value))
        except Exception:
            pass

    def _call_api(
        self,
        method: str,
        url: str,
        headers: dict,
        payload: dict,
        fallback: dict,
        attempt: int = 1,
    ) -> dict:
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                fn = client.post if method == "POST" else client.get
                r = fn(url, json=payload, headers=headers)
                r.raise_for_status()
                return r.json()
        except Exception as exc:
            if attempt < 3:
                import time
                time.sleep(2 ** attempt)
                return self._call_api(method, url, headers, payload, fallback, attempt + 1)
            log.error("GovtVerification API call failed url=%s err=%s", url, exc)
            return fallback


def get_govt_service(db: Session, audit: AuditService) -> GovtVerificationService:
    from config import get_settings
    s = get_settings()
    return GovtVerificationService(
        db=db,
        audit=audit,
        mock=s.govt_api_mock,
        icp_url=s.icp_api_url,
        icp_key=s.icp_api_key,
        dha_url=s.dha_api_url,
        dha_key=s.dha_api_key,
    )
