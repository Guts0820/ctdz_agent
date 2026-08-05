import os
import tempfile
from pathlib import Path

from app.models import EngineResult


class PaddleOCREngine:
    """Adapter for PaddleOCR 3.x's predict API."""

    def __init__(self) -> None:
        os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
        os.environ.setdefault("PADDLE_PDX_MODEL_SOURCE", "bos")
        if os.name == "nt":
            os.environ.setdefault("PADDLE_PDX_CACHE_HOME", r"C:\PaddleOCRCache")
        os.environ.setdefault("PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT", "False")
        try:
            from paddleocr import PaddleOCR
        except ImportError as error:
            raise RuntimeError("PaddleOCR is not installed. Install requirements.txt first.") from error

        self._ocr = PaddleOCR(
            lang="ch",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
        )

    def recognize(self, image_bytes: bytes, content_type: str) -> EngineResult:
        suffix = self._suffix_for(content_type)
        temporary_path = ""
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as image_file:
                image_file.write(image_bytes)
                temporary_path = image_file.name

            recognized_lines: list[str] = []
            confidences: list[float] = []
            for page_result in self._ocr.predict(temporary_path):
                texts = page_result["rec_texts"]
                scores = page_result["rec_scores"]
                for index, text in enumerate(texts):
                    if not text:
                        continue
                    recognized_lines.append(str(text).strip())
                    if index < len(scores):
                        confidences.append(float(scores[index]))

            text = "\n".join(line for line in recognized_lines if line)
            if not text:
                return EngineResult(text="", confidence=0.0, engine="paddleocr")
            confidence = sum(confidences) / len(confidences) if confidences else 0.0
            return EngineResult(text=text, confidence=confidence, engine="paddleocr")
        finally:
            if temporary_path:
                Path(temporary_path).unlink(missing_ok=True)

    @staticmethod
    def _suffix_for(content_type: str) -> str:
        return {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/bmp": ".bmp",
        }.get(content_type.lower(), ".img")
