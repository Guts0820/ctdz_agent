from app.config import Settings
import pytest


def test_pix2text_is_opt_in_until_its_models_are_cached(monkeypatch) -> None:
    monkeypatch.delenv("PIX2TEXT_ENABLED", raising=False)

    settings = Settings.from_env()

    assert settings.pix2text_enabled is False


def test_paddleocr_vl_16_cpu_is_the_default_primary_engine(monkeypatch) -> None:
    monkeypatch.delenv("OCR_ENGINE", raising=False)
    monkeypatch.delenv("PADDLEOCR_VL_DEVICE", raising=False)
    monkeypatch.delenv("PADDLEOCR_VL_PIPELINE_VERSION", raising=False)

    settings = Settings.from_env()

    assert settings.ocr_engine == "paddleocr_vl"
    assert settings.paddleocr_vl_device == "cpu"
    assert settings.paddleocr_vl_pipeline_version == "v1.6"


def test_rejects_an_unknown_primary_ocr_engine(monkeypatch) -> None:
    monkeypatch.setenv("OCR_ENGINE", "unknown")

    with pytest.raises(ValueError, match="OCR_ENGINE"):
        Settings.from_env()


def test_rejects_an_unsupported_paddleocr_vl_pipeline_version(monkeypatch) -> None:
    monkeypatch.setenv("PADDLEOCR_VL_PIPELINE_VERSION", "v2")

    with pytest.raises(ValueError, match="PADDLEOCR_VL_PIPELINE_VERSION"):
        Settings.from_env()
