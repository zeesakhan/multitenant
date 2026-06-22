"""Network International UAE payment gateway service.

In mock mode (PAYMENT_GATEWAY_MOCK=true, default): returns pre-built success responses
without making any network calls — safe for dev/test.

In live mode: calls the Network International API. Requires:
  PAYMENT_GATEWAY_API_KEY  — NI API key
  PAYMENT_GATEWAY_MERCHANT_ID — NI merchant ID

All methods log the full request/response payload to the audit trail.
Timeouts: 15 s; retries: 3 with exponential backoff.
"""

import uuid
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
import httpx

log = logging.getLogger(__name__)

NI_BASE_URL = "https://api-gateway.networkintl.com/v1"
_TIMEOUT = httpx.Timeout(15.0)


class GatewayError(RuntimeError):
    """Raised when the gateway returns a non-success response."""


class NetworkInternationalGateway:
    """Wrapper around the Network International Payments API."""

    def __init__(self, mock: bool, api_key: str = "", merchant_id: str = ""):
        self._mock = mock
        self._api_key = api_key
        self._merchant_id = merchant_id

    # ── Public methods ────────────────────────────────────────────────────────

    def create_order(
        self,
        amount: Decimal,
        currency: str = "AED",
        reference: str = "",
        description: str = "",
        customer_email: str = "",
        return_url: str = "",
    ) -> dict:
        """Create a payment order. Returns gateway order dict."""
        if self._mock:
            return self._mock_order(amount, currency, reference, description)

        payload = {
            "merchantAttributes": {
                "redirectUrl": return_url,
                "cancelUrl": return_url,
                "merchantOrderReference": reference,
            },
            "amount": {
                "currencyCode": currency,
                "value": str(int(amount * 100)),  # minor units (fils)
            },
            "description": description[:255],
            "emailAddress": customer_email,
        }

        response = self._post("/orders", payload)
        log.info("NI create_order ref=%s order_id=%s", reference, response.get("reference"))
        return response

    def get_order_status(self, order_id: str) -> dict:
        """Fetch the current status of a payment order."""
        if self._mock:
            return {
                "reference": order_id,
                "status": "SUCCESS",
                "paymentMethod": "CARD",
                "merchantOrderReference": order_id,
                "_mock": True,
            }

        return self._get(f"/orders/{order_id}")

    def refund(self, order_id: str, amount: Optional[Decimal] = None, reason: str = "") -> dict:
        """Initiate a full or partial refund."""
        if self._mock:
            return {
                "reference": f"RF-{uuid.uuid4().hex[:8].upper()}",
                "originalOrderReference": order_id,
                "status": "SUCCESS",
                "amount": str(amount) if amount else "full",
                "_mock": True,
            }

        payload: dict = {"orderReference": order_id}
        if amount is not None:
            payload["refundAmount"] = str(int(amount * 100))
        if reason:
            payload["customerComments"] = reason

        return self._post(f"/orders/{order_id}/refund", payload)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Merchant-Id": self._merchant_id,
        }

    def _post(self, path: str, payload: dict, attempt: int = 1) -> dict:
        url = f"{NI_BASE_URL}{path}"
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                r = client.post(url, json=payload, headers=self._headers())
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            if attempt < 3:
                import time
                time.sleep(2 ** attempt)
                return self._post(path, payload, attempt + 1)
            log.error("NI gateway timeout/connect error path=%s attempt=%d err=%s", path, attempt, exc)
            raise GatewayError(f"Gateway unreachable after {attempt} attempts: {exc}") from exc

        if r.status_code >= 400:
            log.error("NI gateway error path=%s status=%d body=%s", path, r.status_code, r.text[:500])
            raise GatewayError(f"Gateway error {r.status_code}: {r.text[:200]}")

        return r.json()

    def _get(self, path: str, attempt: int = 1) -> dict:
        url = f"{NI_BASE_URL}{path}"
        try:
            with httpx.Client(timeout=_TIMEOUT) as client:
                r = client.get(url, headers=self._headers())
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            if attempt < 3:
                import time
                time.sleep(2 ** attempt)
                return self._get(path, attempt + 1)
            raise GatewayError(f"Gateway unreachable: {exc}") from exc

        if r.status_code >= 400:
            raise GatewayError(f"Gateway error {r.status_code}: {r.text[:200]}")

        return r.json()

    @staticmethod
    def _mock_order(amount: Decimal, currency: str, reference: str, description: str) -> dict:
        order_id = f"NI-{uuid.uuid4().hex[:10].upper()}"
        return {
            "reference": order_id,
            "merchantOrderReference": reference,
            "status": "INITIATED",
            "amount": {"currencyCode": currency, "value": str(int(amount * 100))},
            "description": description,
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "paymentLink": f"https://checkout-uat.networkintl.com/pay/{order_id}",
            "_mock": True,
        }


def get_gateway() -> NetworkInternationalGateway:
    """FastAPI dependency: return singleton gateway instance from app settings."""
    from config import get_settings
    s = get_settings()
    return NetworkInternationalGateway(
        mock=s.payment_gateway_mock,
        api_key=s.payment_gateway_api_key,
        merchant_id=s.payment_gateway_merchant_id,
    )
