import json
import time
from functools import lru_cache
from typing import Any, Dict, Optional

from openai import OpenAI
from openai import APIConnectionError, APITimeoutError, RateLimitError, APIError

from backend.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_SYSTEM_PROMPT, LLM_TIMEOUT_SECONDS, get_int


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    return OpenAI(
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL or None,
    )


def llm_enabled() -> bool:
    return bool(LLM_API_KEY and LLM_BASE_URL and LLM_MODEL)


def get_llm_retry_count() -> int:
    return max(get_int("LLM_RETRY_COUNT", 2), 0)


def get_default_model() -> str:
    if not LLM_MODEL:
        raise ValueError("LLM_MODEL is not configured")
    return LLM_MODEL


def get_default_system_prompt() -> str:
    return LLM_SYSTEM_PROMPT or "你是一个数学判题助手。"


def call_llm(system_prompt: str, user_prompt: str, model: Optional[str] = None) -> str:
    last_error: Optional[Exception] = None
    retry_count = get_llm_retry_count()
    for attempt in range(retry_count + 1):
        try:
            completion = _client().chat.completions.create(
                model=model or get_default_model(),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                timeout=LLM_TIMEOUT_SECONDS,
            )
            return completion.choices[0].message.content or ""
        except (APITimeoutError, APIConnectionError, RateLimitError, APIError, ValueError) as exc:
            last_error = exc
            if attempt < retry_count:
                time.sleep(min(0.5 * (attempt + 1), 2.0))
                continue
            break
    if last_error:
        raise last_error
    return ""


def call_llm_json(system_prompt: str, user_prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
    raw = call_llm(system_prompt, user_prompt, model=model).strip()
    if raw.startswith("```json"):
        raw = raw[7:]
    if raw.startswith("```"):
        raw = raw[3:]
    if raw.endswith("```"):
        raw = raw[:-3]
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("LLM response is not a JSON object")
    return parsed
