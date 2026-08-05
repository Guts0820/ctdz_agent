from app.models import EngineResult, FormulaResult
from app.services.recognition_service import RecognitionService


class FakeEngine:
    def __init__(self, result: EngineResult) -> None:
        self.result = result
        self.calls = 0

    def recognize(self, image_bytes: bytes, content_type: str) -> EngineResult:
        self.calls += 1
        return self.result


class FakeFormulaEngine:
    def __init__(self, result: FormulaResult) -> None:
        self.result = result
        self.calls = 0

    def recognize_formulas(self, image_bytes: bytes, content_type: str) -> FormulaResult:
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


def test_adds_pix2text_latex_formula_without_replacing_paddle_handwriting_text() -> None:
    primary = FakeEngine(EngineResult(text="计算下面的式子", confidence=0.95, engine="paddleocr"))
    formula = FakeFormulaEngine(
        FormulaResult(formulas=(r"\frac{1}{2} + \frac{1}{3}",), confidence=0.90, engine="pix2text")
    )
    service = RecognitionService(
        primary_engine=primary,
        fallback_engine=None,
        confidence_threshold=0.8,
        formula_engine=formula,
    )

    result = service.recognize(b"image", "image/png")

    assert "计算下面的式子" in result.markdown
    assert "## 数学公式（Pix2Text）" in result.markdown
    assert r"$$\frac{1}{2} + \frac{1}{3}$$" in result.markdown
    assert result.formula_engine == "pix2text"


def test_keeps_primary_text_when_pix2text_formula_enhancement_fails() -> None:
    class BrokenFormulaEngine:
        def recognize_formulas(self, image_bytes: bytes, content_type: str) -> FormulaResult:
            raise RuntimeError("formula model unavailable")

    primary = FakeEngine(EngineResult(text="8 ÷ 2", confidence=0.94, engine="paddleocr"))
    service = RecognitionService(
        primary_engine=primary,
        fallback_engine=None,
        confidence_threshold=0.8,
        formula_engine=BrokenFormulaEngine(),
    )

    result = service.recognize(b"image", "image/png")

    assert "8 ÷ 2" in result.markdown
    assert result.formula_engine is None


def test_preserves_native_vl_markdown_without_pix2text_duplication() -> None:
    primary = FakeEngine(
        EngineResult(
            text="# 解题过程\n\n$$\\frac{1}{2} + \\frac{1}{3}$$",
            confidence=0.91,
            engine="paddleocr-vl-1.6",
            content_format="markdown",
            review_required=False,
        )
    )
    formula = FakeFormulaEngine(
        FormulaResult(formulas=(r"\frac{1}{2} + \frac{1}{3}",), confidence=0.99, engine="pix2text")
    )
    service = RecognitionService(
        primary_engine=primary,
        fallback_engine=None,
        confidence_threshold=0.8,
        formula_engine=formula,
    )

    result = service.recognize(b"image", "image/png")

    assert result.status == "success"
    assert result.markdown.count(r"\frac{1}{2} + \frac{1}{3}") == 1
    assert "## 识别文本" not in result.markdown
    assert "引擎：paddleocr-vl-1.6" in result.markdown
    assert formula.calls == 0


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
