from datetime import datetime, date, timedelta, timezone
from typing import Optional


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def days_from_now(days: int) -> datetime:
    return utcnow() + timedelta(days=days)


def is_expired(dt: datetime) -> bool:
    return dt < utcnow()


def policy_expiry_date(start: date, months: int = 12) -> date:
    month = start.month - 1 + months
    year = start.year + month // 12
    month = month % 12 + 1
    day = min(start.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                           31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return date(year, month, day)


def format_date(d: Optional[date]) -> Optional[str]:
    return d.isoformat() if d else None


def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None
