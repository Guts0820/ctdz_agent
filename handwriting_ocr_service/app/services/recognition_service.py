from typing import Protocol

from app.models import EngineResult, FormulaResult, RecognitionResult
from app.services.markdown_formatter import format_markdown


class RecognitionEngine(Protocol):
    def recognize(self, image_bytes: bytes, content_type: str) -> EngineResult:
        """Recognize text from an image."""


class FormulaRecognitionEngine(Protocol):
    def recognize_formulas(self, image_bytes: bytes, content_type: str) -> FormulaResult:
        """Recognize mathematical formulas from an image."""


class RecognitionService:
    def __init__(
        self,
        primary_engine: RecognitionEngine,
        fallback_engine: RecognitionEngine | None,
        confidence_threshold: float,
        formula_engine: FormulaRecognitionEngine | None = None,
    ) -> None:
        self.primary_engine = primary_engine
        self.fallback_engine = fallback_engine
        self.confidence_threshold = confidence_threshold
        self.formula_engine = formula_engine

    def recognize(self, image_bytes: bytes, content_type: str) -> RecognitionResult:
        primary_result = self.primary_engine.recognize(image_bytes, content_type)
        result = primary_result
        fallback_used = False
        formula_result: FormulaResult | None = None

        if self.formula_engine and primary_result.content_format != "markdown":
            try:
                candidate = self.formula_engine.recognize_formulas(image_bytes, content_type)
                if candidate.formulas:
                    formula_result = candidate
            except Exception:
                # Formula enhancement is optional; preserve readable handwriting text on failure.
                formula_result = None

        primary_requires_review = (
            primary_result.review_required
            if primary_result.review_required is not None
            else primary_result.confidence < self.confidence_threshold
        )
        if primary_requires_review and self.fallback_engine:
            try:
                result = self.fallback_engine.recognize(image_bytes, content_type)
                fallback_used = True
            except Exception:
                # A failed optional fallback must not discard a usable local result.
                result = primary_result

        questions = _build_questions(result.blocks)
        result_requires_review = (
            result.review_required
            if result.review_required is not None
            else result.confidence < self.confidence_threshold
        )
        status = "low_confidence" if result_requires_review else "success"
        return RecognitionResult(
            markdown=format_markdown(
                result.text,
                result.confidence,
                result.engine,
                status,
                formula_result.formulas if formula_result else (),
                result.content_format,
                blocks=result.blocks,
            ),
            confidence=result.confidence,
            engine=result.engine,
            fallback_used=fallback_used,
            status=status,
            formula_engine=formula_result.engine if formula_result else None,
            formula_confidence=formula_result.confidence if formula_result else None,
            blocks=result.blocks,
            raw_json=result.raw_json,
            questions=questions,
        )


def _build_questions(blocks: tuple[dict[str, object], ...]) -> tuple[dict[str, object], ...]:
    questions: list[dict[str, object]] = []
    for block in blocks:
        if block.get("type") != "text":
            continue
        text = str(block.get("text", "")).strip()
        if not text or not text.startswith(("(", "（")):
            continue
        question_number = text[1] if len(text) > 1 and text[1].isdigit() else None
        questions.append({
            "id": question_number or str(len(questions) + 1),
            "type": "fill_blank" if "(" in text or "（" in text else "unknown",
            "stem": text,
            "block_index": block.get("index"),
            "image_refs": [item.get("index") for item in blocks if item.get("type") == "image"],
        })
    return tuple(questions)
