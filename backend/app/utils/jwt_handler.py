"""
Minimal HS256 JWT implementation using Python stdlib only.
Avoids external cryptography dependencies that may conflict with system packages.
"""
import base64
import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    pad = 4 - len(s) % 4
    if pad != 4:
        s += "=" * pad
    return base64.urlsafe_b64decode(s)


def encode(payload: dict, secret: str, algorithm: str = "HS256") -> str:
    header = _b64url_encode(json.dumps({"alg": algorithm, "typ": "JWT"}, separators=(",", ":")).encode())
    body = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header}.{body}"
    sig = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(sig)}"


def decode(token: str, secret: str, algorithms: list = None, options: dict = None) -> dict:
    options = options or {}
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
    except ValueError:
        raise JWTDecodeError("Malformed token")

    signing_input = f"{header_b64}.{payload_b64}"
    expected_sig = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    actual_sig = _b64url_decode(sig_b64)

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise JWTDecodeError("Invalid signature")

    payload = json.loads(_b64url_decode(payload_b64))

    if not options.get("verify_exp", True):
        return payload

    exp = payload.get("exp")
    if exp and datetime.now(timezone.utc).timestamp() > exp:
        raise JWTExpiredError("Token has expired")

    return payload


class JWTDecodeError(Exception):
    pass


class JWTExpiredError(JWTDecodeError):
    pass
