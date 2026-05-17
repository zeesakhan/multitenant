import redis
import json
from typing import Any, Optional
from config import get_settings

settings = get_settings()

_client: Optional[redis.Redis] = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


def cache_set(key: str, value: Any, ttl: int = None) -> None:
    r = get_redis()
    serialized = json.dumps(value) if not isinstance(value, str) else value
    if ttl:
        r.setex(key, ttl, serialized)
    else:
        r.set(key, serialized)


def cache_get(key: str) -> Optional[Any]:
    r = get_redis()
    val = r.get(key)
    if val is None:
        return None
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return val


def cache_delete(key: str) -> None:
    get_redis().delete(key)


def cache_delete_pattern(pattern: str) -> None:
    r = get_redis()
    keys = r.keys(pattern)
    if keys:
        r.delete(*keys)
