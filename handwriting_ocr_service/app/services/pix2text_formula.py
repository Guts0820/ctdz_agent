import tempfile
from pathlib import Path

from app.models import FormulaResult


class Pix2TextFormulaEngine:
    """Lazy Pix2Text adapter that extracts formula blocks as LaTeX."""

    def __init__(self, device: str) -> None:
        self._device = device
        self._client = None

    def recognize_formulas(self, image_bytes: bytes, content_type: str) -> FormulaResult:
        suffix = self._suffix_for(content_type)
        temporary_path = ""
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as image_file:
                image_file.write(image_bytes)
                temporary_path = image_file.name

            blocks = self._get_client().recognize(
                temporary_path,
                file_type="text_formula",
                return_text=False,
                auto_line_break=False,
            )
            formulas: list[str] = []
            scores: list[float] = []
            for block in blocks or []:
                if not isinstance(block, dict) or block.get("type") == "text":
                    continue
                formula = str(block.get("text", "")).strip()
                if formula:
                    formulas.append(formula)
                    score = block.get("score")
                    if isinstance(score, int | float):
                        scores.append(float(score))

            confidence = sum(scores) / len(scores) if scores else 0.0
            return FormulaResult(
                formulas=tuple(formulas),
                confidence=confidence,
                engine="pix2text",
            )
        finally:
            if temporary_path:
                Path(temporary_path).unlink(missing_ok=True)

    def _get_client(self):
        if self._client is None:
            try:
                from pix2text import Pix2Text
            except ImportError as error:
                raise RuntimeError("Pix2Text is not installed. Install requirements.txt first.") from error
            self._client = Pix2Text.from_config(enable_table=False, device=self._device)
        return self._client

    @staticmethod
    def _suffix_for(content_type: str) -> str:
        return {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/bmp": ".bmp",
        }.get(content_type.lower(), ".img")
