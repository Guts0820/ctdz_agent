from dataclasses import replace

import app.main as main


def test_builds_paddleocr_vl_as_the_primary_engine(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_vl_engine(*, device: str, pipeline_version: str) -> str:
        captured["device"] = device
        captured["pipeline_version"] = pipeline_version
        return "vl-engine"

    monkeypatch.setattr(main, "PaddleOCRVLEngine", fake_vl_engine)
    monkeypatch.setattr(main, "settings", replace(main.settings, ocr_engine="paddleocr_vl"))

    result = main._build_primary_engine()

    assert result == "vl-engine"
    assert captured == {"device": "cpu", "pipeline_version": "v1.6"}


def test_builds_legacy_paddleocr_when_rollback_is_selected(monkeypatch) -> None:
    monkeypatch.setattr(main, "PaddleOCREngine", lambda: "legacy-engine")
    monkeypatch.setattr(main, "settings", replace(main.settings, ocr_engine="paddleocr_legacy"))

    assert main._build_primary_engine() == "legacy-engine"
