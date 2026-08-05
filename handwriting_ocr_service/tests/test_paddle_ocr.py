import sys
from types import SimpleNamespace

from app.services.paddle_ocr import PaddleOCREngine


def test_uses_paddleocr_v3_predict_api_and_normalizes_recognition_output(monkeypatch) -> None:
    captured: dict[str, object] = {}
    monkeypatch.delenv("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", raising=False)
    monkeypatch.delenv("PADDLE_PDX_MODEL_SOURCE", raising=False)
    monkeypatch.delenv("PADDLE_PDX_CACHE_HOME", raising=False)
    monkeypatch.delenv("PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT", raising=False)

    class FakePaddleOCR:
        def __init__(self, **kwargs) -> None:
            captured["kwargs"] = kwargs

        def predict(self, image_path: str):
            captured["image_path"] = image_path
            return iter([{"rec_texts": ["12 + 3 = 15"], "rec_scores": [0.97]}])

    monkeypatch.setitem(sys.modules, "paddleocr", SimpleNamespace(PaddleOCR=FakePaddleOCR))
    engine = PaddleOCREngine()

    result = engine.recognize(b"fake image", "image/png")

    assert captured["kwargs"] == {
        "lang": "ch",
        "use_doc_orientation_classify": False,
        "use_doc_unwarping": False,
        "use_textline_orientation": False,
    }
    assert result.text == "12 + 3 = 15"
    assert result.confidence == 0.97
    assert result.engine == "paddleocr"
    assert __import__("os").environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] == "True"
    assert __import__("os").environ["PADDLE_PDX_MODEL_SOURCE"] == "bos"
    assert __import__("os").environ["PADDLE_PDX_CACHE_HOME"] == r"C:\PaddleOCRCache"
    assert __import__("os").environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] == "False"
