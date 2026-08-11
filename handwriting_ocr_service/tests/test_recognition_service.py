from app.models import EngineResult
from app.services.recognition_service import RecognitionService


class FakeEngine:
    def __init__(self, result: EngineResult) -> None:
        self.result = result
        self.calls = 0

    def recognize(self, image_bytes: bytes, content_type: str) -> EngineResult:
        self.calls += 1
        return self.result


def test_returns_primary_markdown_when_primary_confidence_is_sufficient() -> None:
    primary = FakeEngine(EngineResult(text="3 + 5 = 8", confidence=0.96, engine="paddleocr"))
    fallback = FakeEngine(EngineResult(text="should not run", confidence=0.99, engine="qwen"))
    service = RecognitionService(primary_engine=primary, fallback_engine=fallback, confidence_threshold=0.8)

    result = service.recognize(b"image", "image/png")

    assert result.engine == "paddleocr"
    assert result.fallback_used is False
    assert "3 + 5 = 8" in result.markdown
    assert fallback.calls == 0


def test_uses_qwen_fallback_for_low_confidence_primary_result() -> None:
    primary = FakeEngine(EngineResult(text="3 + 5 = ?", confidence=0.42, engine="paddleocr"))
    fallback = FakeEngine(EngineResult(text="3 + 5 = 8", confidence=0.91, engine="qwen"))
    service = RecognitionService(primary_engine=primary, fallback_engine=fallback, confidence_threshold=0.8)

    result = service.recognize(b"image", "image/jpeg")

    assert result.engine == "qwen"
    assert result.fallback_used is True
    assert result.status == "success"
    assert "3 + 5 = 8" in result.markdown


def test_keeps_low_confidence_result_when_no_fallback_is_configured() -> None:
    primary = FakeEngine(EngineResult(text="无法确认", confidence=0.30, engine="paddleocr"))
    service = RecognitionService(primary_engine=primary, fallback_engine=None, confidence_threshold=0.8)

    result = service.recognize(b"image", "image/png")

    assert result.status == "low_confidence"
    assert result.fallback_used is False
    assert "无法确认" in result.markdown


def test_uses_fallback_when_vl_quality_check_requires_review() -> None:
    primary = FakeEngine(
        EngineResult(
            text="重复的幻觉输出",
            confidence=0.99,
            engine="paddleocr-vl-1.6",
            content_format="markdown",
            review_required=True,
        )
    )
    fallback = FakeEngine(EngineResult(text="真实识别结果", confidence=0.90, engine="qwen"))
    service = RecognitionService(primary, fallback, confidence_threshold=0.8)

    result = service.recognize(b"image", "image/png")

    assert result.engine == "qwen"
    assert result.fallback_used is True
    assert "真实识别结果" in result.markdown


def test_accepts_valid_vl_output_even_when_layout_score_is_below_legacy_threshold() -> None:
    primary = FakeEngine(
        EngineResult(
            text="手写内容",
            confidence=0.70,
            engine="paddleocr-vl-1.6",
            content_format="markdown",
            review_required=False,
        )
    )
    fallback = FakeEngine(EngineResult(text="不应调用", confidence=0.99, engine="qwen"))
    service = RecognitionService(primary, fallback, confidence_threshold=0.8)

    result = service.recognize(b"image", "image/png")

    assert result.engine == "paddleocr-vl-1.6"
    assert result.status == "success"
    assert result.fallback_used is False
    assert fallback.calls == 0
