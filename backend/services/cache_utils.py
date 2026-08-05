import json
from functools import lru_cache
from typing import Any, Optional

from backend.config import REDIS_TTL_SECONDS, REDIS_URL


@lru_cache(maxsize=1)
def _redis_client() -> Any:
    if not REDIS_URL:
        return None
    try:
        import redis
    except ImportError:
        return None
    return redis.Redis.from_url(REDIS_URL, decode_responses=True)


def cache_enabled() -> bool:
    return _redis_client() is not None


def cache_get(key: str) -> Optional[Any]:
    client = _redis_client()
    if client is None:
        return None
    value = client.get(key)
    if value is None:
        return None
    try:
        return json.loads(value)
    except Exception:
        return value


def cache_set(key: str, value: Any, ttl: int = REDIS_TTL_SECONDS) -> None:
    client = _redis_client()
    if client is None:
        return
    client.setex(key, ttl, json.dumps(value, ensure_ascii=False))
