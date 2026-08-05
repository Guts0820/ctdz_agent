import json
import logging
import time
from functools import wraps
from typing import Callable, Any, Dict
from uuid import uuid4

from backend.config import SERVICE_HEALTH_TIMEOUT_SECONDS


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


logger = logging.getLogger("ctdz_backend")


def request_context() -> Dict[str, str]:
    return {"request_id": uuid4().hex}


def log_event(event: str, **fields: Any) -> None:
    payload = {"event": event, **fields}
    logger.info(json.dumps(payload, ensure_ascii=False, default=str))


def timed(event_name: str):
    def decorator(func: Callable[..., Any]):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                log_event(f"{event_name}.success", elapsed_ms=elapsed_ms)
                return result
            except Exception as exc:
                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                log_event(f"{event_name}.error", elapsed_ms=elapsed_ms, error=str(exc))
                raise
        return wrapper
    return decorator
