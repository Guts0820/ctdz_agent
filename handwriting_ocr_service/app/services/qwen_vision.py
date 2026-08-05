import base64

import requests

from app.config import Settings
from app.models import EngineResult


class QwenVisionEngine:
    """Optional OpenAI-compatible Qwen vision fallback."""

    def __init__(self, settings: Settings) -> None:
        if not settings.qwen_is_configured:
            raise ValueError("Qwen vision fallback is not fully configured.")
        self._api_key = settings.qwen_api_key
        self._base_url = settings.qwen_base_url.rstrip("/")
        self._model = settings.qwen_model
        self._timeout_seconds = settings.qwen_timeout_seconds
        self._fallback_confidence = settings.qwen_fallback_confidence

    def recognize(self, image_bytes: bytes, content_type: str) -> EngineResult:
        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        response = requests.post(
            f"{self._base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是手写作业文字识别器。只转录图片中可见的文字、算式和公式；不判断正误、不补全缺失内容。",
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{encoded_image}"}},
                            {"type": "text", "text": "请将识别结果直接输出为 Markdown。对不确定内容标注为 [不确定]。"},
                        ],
                    },
                ],
            },
            timeout=self._timeout_seconds,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "\n".join(item.get("text", "") for item in content if isinstance(item, dict))
        return EngineResult(
            text=str(content).strip(),
            confidence=self._fallback_confidence,
            engine="qwen_vision",
        )
