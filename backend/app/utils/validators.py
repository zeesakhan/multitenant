import re
import uuid
from datetime import date


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
PHONE_REGEX = re.compile(r"^\+?[1-9]\d{6,14}$")


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email.strip()))


def is_valid_phone(phone: str) -> bool:
    return bool(PHONE_REGEX.match(phone.strip()))


def is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False


def is_valid_age(dob: date, min_age: int = 0, max_age: int = 150) -> bool:
    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return min_age <= age <= max_age


def calculate_age(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def sanitize_string(value: str, max_length: int = 255) -> str:
    return value.strip()[:max_length]


def is_valid_hex_color(value: str) -> bool:
    return bool(re.match(r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$", value))
