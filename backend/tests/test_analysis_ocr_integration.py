import sys
from pathlib import Path

import pytest
import requests
from fastapi import HTTPException


BACKEND_ROOT = Path(__file__).resolve().parents[1]
SERVICES_ROOT = BACKEND_ROOT / "services"
if str(SERVICES_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICES_ROOT))

from backend.services import analysis_service


class FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return self.payload


def test_call_ocr_service_sends_multipart_image(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(url, *, files, timeout):
        captured.update({"url": url, "files": files, "timeout": timeout})
        return FakeResponse({
            "markdown": "25 + 38 = 53",
            "confidence": 0.91,
            "engine": "paddleocr-vl-1.6",
            "fallback_used": False,
            "status": "success",
        })

    monkeypatch.setattr(analysis_service.requests, "post", fake_post)

    result = analysis_service.call_ocr_service(b"image-bytes", "image/png")

    assert captured["url"].endswith("/v1/recognize")
    upload = captured["files"]["image"]
    assert upload[0] == "image"
    assert upload[1].getvalue() == b"image-bytes"
    assert upload[2] == "image/png"
    assert result["markdown"] == "25 + 38 = 53"


def test_run_ocr_separates_question_and_answer(monkeypatch) -> None:
    monkeypatch.setattr(analysis_service, "call_ocr_service", lambda *_: {
        "markdown": "小明有25颗糖果，他们一共有多少颗？\n学生作答：25+38=53",
        "confidence": 0.91,
        "engine": "paddleocr-vl-1.6",
        "status": "success",
    })

    result = analysis_service.run_ocr(analysis_service.AnalysisRequest(
        student_id="S-0001",
        image="data:image/png;base64,aW1hZ2U=",
    ))

    assert result["text_status"] == "normal"
    assert result["original_question"] == "小明有25颗糖果，他们一共有多少颗？"
    assert result["student_write"] == "学生作答：25+38=53"
    assert result["ocr_markdown"].startswith("小明有25颗糖果")


def test_run_ocr_marks_unavailable_service_without_fabricating_text(monkeypatch) -> None:
    monkeypatch.setattr(
        analysis_service,
        "call_ocr_service",
        lambda *_: (_ for _ in ()).throw(requests.ConnectionError("OCR service unavailable")),
    )

    result = analysis_service.run_ocr(analysis_service.AnalysisRequest(
        student_id="S-0001",
        image="data:image/png;base64,aW1hZ2U=",
    ))

    assert result["text_status"] == "ocr_unavailable"
    assert result["original_question"] == ""
    assert result["student_write"] == ""
