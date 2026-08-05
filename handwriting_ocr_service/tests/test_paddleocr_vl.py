import sys
from pathlib import Path
from types import SimpleNamespace

from app.services.paddleocr_vl import PaddleOCRVLEngine, normalize_markdown_math


class FakeVLResult(dict):
    def __init__(self, markdown_text: str, scores: list[float], boxes: list[dict[str, object]] | None = None) -> None:
        super().__init__(
            layout_det_res={"boxes": boxes if boxes is not None else [{"score": score} for score in scores]},
            parsing_res_list=[] if not markdown_text else [{"block_content": markdown_text}],
        )
        self._markdown_text = markdown_text

    @property
    def markdown(self) -> dict[str, object]:
        return {"markdown_texts": self._markdown_text, "markdown_images": {}}


def test_uses_v16_cpu_pipeline_and_returns_native_markdown(monkeypatch) -> None:
    captured: dict[str, object] = {}

    class FakePaddleOCRVL:
        def __init__(self, **kwargs) -> None:
            captured["kwargs"] = kwargs

        def predict(self, image_path: str):
            captured["image_path"] = image_path
            return [
                FakeVLResult(
                    "题目\n\n图片说明",
                    [0.92, 0.88],
                    boxes=[
                        {"label": "title", "score": 0.93, "text": "题目"},
                        {"label": "image", "score": 0.81, "text": "图片说明"},
                    ],
                )
            ]

    monkeypatch.setitem(sys.modules, "paddleocr", SimpleNamespace(PaddleOCRVL=FakePaddleOCRVL))
    engine = PaddleOCRVLEngine(device="cpu", pipeline_version="v1.6")

    result = engine.recognize(b"fake image", "image/png")

    assert captured["kwargs"] == {
        "pipeline_version": "v1.6",
        "device": "cpu",
        "use_doc_orientation_classify": False,
        "use_doc_unwarping": False,
        "use_layout_detection": True,
        "markdown_ignore_labels": ["image"],
    }
    assert result.text == "题目\n\n图片说明"
    assert result.confidence == 0.87
    assert result.engine == "paddleocr-vl-1.6"
    assert result.content_format == "markdown"
    assert result.review_required is False
    assert result.blocks[0]["type"] == "title"
    assert result.blocks[1]["type"] == "image"
    assert not Path(str(captured["image_path"])).exists()


def test_marks_empty_vl_output_for_review(monkeypatch) -> None:
    class FakePaddleOCRVL:
        def __init__(self, **kwargs) -> None:
            pass

        def predict(self, image_path: str):
            return [FakeVLResult("", [])]

    monkeypatch.setitem(sys.modules, "paddleocr", SimpleNamespace(PaddleOCRVL=FakePaddleOCRVL))
    engine = PaddleOCRVLEngine(device="cpu", pipeline_version="v1.6")

    result = engine.recognize(b"fake image", "image/jpeg")

    assert result.confidence == 0.0
    assert result.review_required is True


def test_does_not_invent_a_quality_score_when_layout_scores_are_missing(monkeypatch) -> None:
    class FakePaddleOCRVL:
        def __init__(self, **kwargs) -> None:
            pass

        def predict(self, image_path: str):
            return [FakeVLResult("有效识别结果", [])]

    monkeypatch.setitem(sys.modules, "paddleocr", SimpleNamespace(PaddleOCRVL=FakePaddleOCRVL))
    engine = PaddleOCRVLEngine(device="cpu", pipeline_version="v1.6")

    result = engine.recognize(b"fake image", "image/png")

    assert result.confidence == 0.0
    assert result.review_required is False


def test_marks_strongly_repeated_vl_output_for_review(monkeypatch) -> None:
    repeated_markdown = "\n".join(["同一段异常文本"] * 6)

    class FakePaddleOCRVL:
        def __init__(self, **kwargs) -> None:
            pass

        def predict(self, image_path: str):
            return [FakeVLResult(repeated_markdown, [0.99])]

    monkeypatch.setitem(sys.modules, "paddleocr", SimpleNamespace(PaddleOCRVL=FakePaddleOCRVL))
    engine = PaddleOCRVLEngine(device="cpu", pipeline_version="v1.6")

    result = engine.recognize(b"fake image", "image/webp")

    assert result.review_required is True


def test_wraps_bare_latex_commands_in_markdown_heading() -> None:
    markdown = "#### 0.07\\times40=0.28"

    normalized = normalize_markdown_math(markdown)

    assert normalized == "#### $0.07\\times40=0.28$"


def test_wraps_latex_commands_inside_an_inline_text_span() -> None:
    markdown = "答案：0.07\\times40=0.28"

    normalized = normalize_markdown_math(markdown)

    assert normalized == "答案：$0.07\\times40=0.28$"


def test_keeps_existing_math_delimiters_and_code_blocks_unchanged() -> None:
    markdown = "已经是 $a\\times b$\n\n```text\n裸命令：\\sqrt{x}\n```"

    assert normalize_markdown_math(markdown) == markdown
