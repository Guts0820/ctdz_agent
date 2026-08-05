import asyncio

import app.main as main
from app.models import RecognitionResult


class FakeUpload:
    content_type = "image/png"

    async def read(self) -> bytes:
        return b"image"


def test_recognition_runs_cpu_inference_outside_the_async_event_loop(monkeypatch) -> None:
    threadpool_calls = 0
    inside_threadpool = False

    class FakeService:
        def recognize(self, image_bytes: bytes, content_type: str) -> RecognitionResult:
            return RecognitionResult(
                markdown="识别成功",
                confidence=0.9,
                engine="paddleocr-vl-1.6",
                fallback_used=False,
                status="success",
                blocks=({"type": "title", "text": "题目"}, {"type": "image", "text": "图片块"}),
            )

    async def fake_run_in_threadpool(function, *args):
        nonlocal inside_threadpool, threadpool_calls
        threadpool_calls += 1
        inside_threadpool = True
        try:
            return function(*args)
        finally:
            inside_threadpool = False

    def fake_build_recognition_service() -> FakeService:
        assert inside_threadpool, "model initialization must not block the event loop"
        return FakeService()

    monkeypatch.setattr(main, "build_recognition_service", fake_build_recognition_service)
    monkeypatch.setattr(main, "run_in_threadpool", fake_run_in_threadpool, raising=False)

    response = asyncio.run(main.recognize_handwriting(FakeUpload()))

    assert response["markdown"] == "识别成功"
    assert response["blocks"] == [{"type": "title", "text": "题目"}, {"type": "image", "text": "图片块"}]
    assert threadpool_calls == 1
