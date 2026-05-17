import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List

_windows: Dict[str, List[float]] = defaultdict(list)
_lock = Lock()


def check_rate_limit(key: str, max_requests: int, window_seconds: int = 60) -> bool:
    """Sliding-window rate limiter. Returns True if the request is allowed."""
    now = time.monotonic()
    cutoff = now - window_seconds
    with _lock:
        window = _windows[key]
        while window and window[0] < cutoff:
            window.pop(0)
        if len(window) >= max_requests:
            return False
        window.append(now)
        return True
