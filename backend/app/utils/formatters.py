from datetime import datetime, timezone
from typing import Any, Optional
import random
import string


def api_response(data: Any = None, message: str = None, success: bool = True) -> dict:
    resp = {"success": success, "timestamp": datetime.now(timezone.utc).isoformat()}
    if data is not None:
        resp["data"] = data
    if message:
        resp["message"] = message
    return resp


def paginated_response(data: list, total: int, page: int, per_page: int) -> dict:
    total_pages = (total + per_page - 1) // per_page if per_page > 0 else 0
    return {
        "success": True,
        "data": data,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def error_response(errors: list[dict], status_code: int = 400) -> dict:
    return {
        "success": False,
        "errors": errors,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def format_currency(amount: float, currency: str = "USD") -> str:
    return f"{currency} {amount:,.2f}"


def generate_reference_number(prefix: str, tenant_code: Optional[str] = None, sequence: Optional[int] = None) -> str:
    """Generate a human-readable reference like QT-ACME-000001 or QT-20260517-A3F2"""
    if tenant_code and sequence is not None:
        return f"{prefix}-{tenant_code.upper()}-{sequence:06d}"
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    rand_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{date_part}-{rand_part}"
