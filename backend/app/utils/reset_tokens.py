import secrets
import time
from threading import Lock
from typing import Dict, Optional, Tuple

_EXPIRY_SECONDS = 3600
_tokens: Dict[str, Tuple[str, float]] = {}  # token -> (user_id, exp)
_lock = Lock()


def create(user_id: str) -> str:
    """Generate a one-time password-reset token, cancelling any prior token for this user."""
    token = secrets.token_urlsafe(32)
    exp = time.time() + _EXPIRY_SECONDS
    with _lock:
        for k, (uid, _) in list(_tokens.items()):
            if uid == user_id:
                del _tokens[k]
        _tokens[token] = (user_id, exp)
    return token


def consume(token: str) -> Optional[str]:
    """Return the user_id if the token is valid, otherwise None. Always deletes the token."""
    with _lock:
        entry = _tokens.pop(token, None)
    if not entry:
        return None
    user_id, exp = entry
    return user_id if time.time() <= exp else None
