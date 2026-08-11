import base64
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


def test_run_ocr_sends_decoded_image_and_returns_normalized_result(monkeypatch) -> None:
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

    image_data_url = "data:image/png;base64," + base64.b64encode(b"image-bytes").decode()
    result = analysis_service.run_ocr(image_data_url)

    assert captured["url"].endswith("/v1/recognize")
    assert captured["files"] == {"image": ("homework.png", b"image-bytes", "image/png")}
    assert result == {
        "markdown": "25 + 38 = 53",
        "confidence": 0.91,
        "engine": "paddleocr-vl-1.6",
        "fallback_used": False,
        "status": "success",
    }


def test_run_ocr_reports_unavailable_service_as_503(monkeypatch) -> None:
    def fake_post(*args, **kwargs):
        raise requests.ConnectionError("OCR service unavailable")

    monkeypatch.setattr(analysis_service.requests, "post", fake_post)

    with pytest.raises(HTTPException) as error:
        analysis_service.run_ocr("data:image/jpeg;base64,aW1hZ2U=")

    assert error.value.status_code == 503
    assert "OCR" in str(error.value.detail)


def test_run_ocr_preserves_ocr_client_error_status(monkeypatch) -> None:
    class RejectedResponse:
        status_code = 413

        def raise_for_status(self) -> None:
            error = requests.HTTPError("payload too large")
            error.response = self
            raise error

    monkeypatch.setattr(analysis_service.requests, "post", lambda *args, **kwargs: RejectedResponse())

    with pytest.raises(HTTPException) as error:
        analysis_service.run_ocr("data:image/png;base64,aW1hZ2U=")

    assert error.value.status_code == 413
