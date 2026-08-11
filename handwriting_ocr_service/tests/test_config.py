from app.config import Settings
import pytest


def test_paddleocr_vl_gpu_is_the_default_device(monkeypatch) -> None:
    monkeypatch.delenv("PADDLEOCR_VL_DEVICE", raising=False)
    monkeypatch.delenv("PADDLEOCR_VL_PIPELINE_VERSION", raising=False)

    settings = Settings.from_env()

    assert settings.paddleocr_vl_device == "gpu"
    assert settings.paddleocr_vl_pipeline_version == "v1.6"


def test_rejects_an_unsupported_paddleocr_vl_pipeline_version(monkeypatch) -> None:
    monkeypatch.setenv("PADDLEOCR_VL_PIPELINE_VERSION", "v2")

    with pytest.raises(ValueError, match="PADDLEOCR_VL_PIPELINE_VERSION"):
        Settings.from_env()
