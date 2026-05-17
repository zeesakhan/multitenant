from typing import Optional
from app.cache.redis_client import cache_get, cache_set, cache_delete
from config import get_settings

settings = get_settings()
CONFIG_TTL = 1800  # 30 minutes


def get_tenant_config_cache(tenant_id: str) -> Optional[dict]:
    return cache_get(f"config:{tenant_id}")


def set_tenant_config_cache(tenant_id: str, config: dict) -> None:
    cache_set(f"config:{tenant_id}", config, ttl=CONFIG_TTL)


def invalidate_tenant_config(tenant_id: str) -> None:
    cache_delete(f"config:{tenant_id}")
    cache_delete(f"brand:{tenant_id}")
