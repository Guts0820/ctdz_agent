import sys
from pathlib import Path

import pytest
from fastapi import HTTPException


SERVICES_ROOT = Path(__file__).resolve().parents[1] / "services"
if str(SERVICES_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICES_ROOT))

from backend import api_gateway


def test_submit_preserves_ocr_unavailable_status(monkeypatch) -> None:
    def unavailable(_request):
        raise HTTPException(status_code=503, detail="OCR service is unavailable.")

    monkeypatch.setattr(api_gateway, "call_analysis_service", unavailable)

    with pytest.raises(HTTPException) as error:
        api_gateway.submit_homework(api_gateway.SubmitRequest(
            student_id="S-0001",
            image="data:image/png;base64,aW1hZ2U=",
        ))

    assert error.value.status_code == 503


def test_call_analysis_service_preserves_ocr_status(monkeypatch) -> None:
    class FailedAnalysisResponse:
        status_code = 503

        def raise_for_status(self) -> None:
            error = api_gateway.requests.HTTPError("OCR service is unavailable")
            error.response = self
            raise error

    monkeypatch.setattr(api_gateway.requests, "post", lambda *args, **kwargs: FailedAnalysisResponse())

    with pytest.raises(HTTPException) as error:
        api_gateway.call_analysis_service(api_gateway.SubmitRequest(
            student_id="S-0001",
            image="data:image/png;base64,aW1hZ2U=",
        ))

    assert error.value.status_code == 503
