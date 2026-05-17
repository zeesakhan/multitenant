import time
from threading import Lock
from typing import Dict

_denylist: Dict[str, float] = {}  # token -> exp timestamp
_lock = Lock()


def deny(token: str, exp: float) -> None:
    """Add a token to the denylist until it expires."""
    now = time.time()
    with _lock:
        _denylist[token] = exp
        # Prune expired entries to prevent unbounded growth
        for k in list(_denylist):
            if _denylist[k] < now:
                del _denylist[k]


def is_denied(token: str) -> bool:
    return token in _denylist
