import re
from typing import Protocol

from app.models import EngineResult, RecognitionResult
from app.services.markdown_formatter import format_markdown


class RecognitionEngine(Protocol):
    def recognize(self, image_bytes: bytes, content_type: str) -> EngineResult:
        """Recognize text from an image."""


class RecognitionService:
    def __init__(
        self,
        primary_engine: RecognitionEngine,
        confidence_threshold: float,
        fallback_engine: RecognitionEngine | None = None,
        fallback_factory: "Callable[[], RecognitionEngine] | None" = None,
    ) -> None:
        self.primary_engine = primary_engine
        self.fallback_engine = fallback_engine
        self._fallback_factory = fallback_factory
        self._loaded_fallback: RecognitionEngine | None = None
        self.confidence_threshold = confidence_threshold

    def _get_fallback(self) -> RecognitionEngine | None:
        if self.fallback_engine is not None:
            return self.fallback_engine
        if self._loaded_fallback is None and self._fallback_factory is not None:
            self._loaded_fallback = self._fallback_factory()
        return self._loaded_fallback

    def recognize(self, image_bytes: bytes, content_type: str) -> RecognitionResult:
        try:
            result = self.primary_engine.recognize(image_bytes, content_type)
            fallback_used = False
            primary_requires_review = (
                result.review_required
                if result.review_required is not None
                else result.confidence < self.confidence_threshold
            )
            fallback = self._get_fallback()
            if primary_requires_review and fallback is not None:
                try:
                    result = fallback.recognize(image_bytes, content_type)
                    fallback_used = True
                except Exception:
                    # A failed optional fallback must not discard a usable primary result.
                    pass
        except Exception:
            fallback = self._get_fallback()
            if fallback is None:
                raise
            result = fallback.recognize(image_bytes, content_type)
            fallback_used = True

        parsed = result.parsed or {}
        questions: tuple[dict[str, object], ...] = ()
        parsed_questions = parsed.get("questions") if isinstance(parsed, dict) else None
        if isinstance(parsed_questions, list):
            questions = tuple(parsed_questions)
        if not questions:
            questions = _build_questions(result.blocks)
        if not questions:
            questions = _build_questions_from_lines(result.text_lines)

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
                result.content_format,
                blocks=result.blocks,
            ),
            confidence=result.confidence,
            engine=result.engine,
            fallback_used=fallback_used,
            status=status,
            blocks=result.blocks,
            raw_json=result.raw_json,
            questions=questions,
            text_lines=result.text_lines,
            parsed=result.parsed,
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


def _build_questions_from_lines(
    text_lines: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    """从全文本行中提取形如 `1. 题目` / `1、题目` 的题号行作为候选题目。"""
    questions: list[dict[str, object]] = []
    for item in text_lines:
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        match = re.match(r"^(\d+)\s*[.、．]\s*(.*)$", text)
        if match and match.group(2).strip():
            questions.append({
                "id": match.group(1),
                "type": "unknown",
                "stem": text,
                "source": "text_line",
            })
    return tuple(questions)
