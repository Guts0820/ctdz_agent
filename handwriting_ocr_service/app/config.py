import os
from dataclasses import dataclass


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    paddleocr_vl_device: str
    paddleocr_vl_pipeline_version: str
    confidence_threshold: float
    max_image_bytes: int
    qwen_fallback_enabled: bool
    qwen_api_key: str | None
    qwen_base_url: str | None
    qwen_model: str | None
    qwen_timeout_seconds: float
    qwen_fallback_confidence: float

    @classmethod
    def from_env(cls) -> "Settings":
        pipeline_version = os.getenv(
            "PADDLEOCR_VL_PIPELINE_VERSION", "v1.6"
        ).strip()
        if pipeline_version not in {"v1", "v1.5", "v1.6"}:
            raise ValueError(
                "PADDLEOCR_VL_PIPELINE_VERSION must be 'v1', 'v1.5', or 'v1.6'."
            )

        return cls(
            paddleocr_vl_device=os.getenv("PADDLEOCR_VL_DEVICE", "gpu").strip().lower(),
            paddleocr_vl_pipeline_version=pipeline_version,
            confidence_threshold=float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "0.80")),
            max_image_bytes=int(os.getenv("MAX_IMAGE_BYTES", str(10 * 1024 * 1024))),
            qwen_fallback_enabled=_as_bool(os.getenv("QWEN_VISION_FALLBACK_ENABLED")),
            qwen_api_key=os.getenv("QWEN_API_KEY"),
            qwen_base_url=os.getenv("QWEN_BASE_URL"),
            qwen_model=os.getenv("QWEN_MODEL"),
            qwen_timeout_seconds=float(os.getenv("QWEN_TIMEOUT_SECONDS", "30")),
            qwen_fallback_confidence=float(os.getenv("QWEN_FALLBACK_CONFIDENCE", "0.85")),
        )

    @property
    def qwen_is_configured(self) -> bool:
        return bool(
            self.qwen_fallback_enabled
            and self.qwen_api_key
            and self.qwen_base_url
            and self.qwen_model
        )
