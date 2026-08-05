import os
from pathlib import Path
from typing import Any, Dict, Optional


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _parse_env_file(env_path: Path) -> Dict[str, str]:
    if not env_path.exists():
        return {}

    data: Dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        data[key] = value
    return data


_ENV_PATH = _repo_root() / ".env"
_ENV_FILE_VALUES = _parse_env_file(_ENV_PATH)

for _key, _value in _ENV_FILE_VALUES.items():
    os.environ.setdefault(_key, _value)


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    return os.environ.get(name, default)


def get_int(name: str, default: int) -> int:
    value = get_env(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_float(name: str, default: float) -> float:
    value = get_env(name)
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def get_bool(name: str, default: bool = False) -> bool:
    value = get_env(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "y"}


DATABASE_PATH = get_env("DATABASE_PATH", "backend/database/example_db.db")
KNOWLEDGE_CSV_PATH = get_env("KNOWLEDGE_CSV_PATH", "backend/database/knowledge_points.csv")
API_GATEWAY_HOST = get_env("API_GATEWAY_HOST", "0.0.0.0")
API_GATEWAY_PORT = get_int("API_GATEWAY_PORT", 8000)
ANALYSIS_SERVICE_URL = get_env("ANALYSIS_SERVICE_URL", "http://127.0.0.1:8081")
ERROR_ANALYSIS_SERVICE_URL = get_env("ERROR_ANALYSIS_SERVICE_URL", "http://127.0.0.1:8082")
KNOWLEDGE_SERVICE_URL = get_env("KNOWLEDGE_SERVICE_URL", "http://127.0.0.1:8083")
TEACHING_SERVICE_URL = get_env("TEACHING_SERVICE_URL", "http://127.0.0.1:8084")
STATE_SERVICE_URL = get_env("STATE_SERVICE_URL", "http://127.0.0.1:8085")
KNOWLEDGE_GRAPH_URL = get_env("KNOWLEDGE_GRAPH_URL", "http://127.0.0.1:8007")
DEFAULT_GRADE = get_env("DEFAULT_GRADE", "三年级")
DEFAULT_TEXTBOOK_VERSION = get_env("DEFAULT_TEXTBOOK_VERSION", "人教版")
LLM_API_KEY = get_env("LLM_API_KEY", "")
LLM_BASE_URL = get_env("LLM_BASE_URL", "")
LLM_MODEL = get_env("LLM_MODEL", "")
LLM_SYSTEM_PROMPT = get_env("LLM_SYSTEM_PROMPT", "")
LLM_TIMEOUT_SECONDS = get_float("LLM_TIMEOUT_SECONDS", 60.0)
REDIS_URL = get_env("REDIS_URL", "")
REDIS_TTL_SECONDS = get_int("REDIS_TTL_SECONDS", 3600)
HTTP_TIMEOUT_SECONDS = get_float("HTTP_TIMEOUT_SECONDS", 10.0)
SERVICE_STARTUP_WAIT_SECONDS = get_float("SERVICE_STARTUP_WAIT_SECONDS", 3.0)
SERVICE_HEALTH_TIMEOUT_SECONDS = get_float("SERVICE_HEALTH_TIMEOUT_SECONDS", 3.0)


def service_urls() -> Dict[str, str]:
    return {
        "analysis": ANALYSIS_SERVICE_URL,
        "error_analysis": ERROR_ANALYSIS_SERVICE_URL,
        "knowledge": KNOWLEDGE_SERVICE_URL,
        "teaching": TEACHING_SERVICE_URL,
        "state": STATE_SERVICE_URL,
        "knowledge_graph": KNOWLEDGE_GRAPH_URL,
    }
