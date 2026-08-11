from dataclasses import dataclass


@dataclass(frozen=True)
class EngineResult:
    """The normalized output returned by one recognition engine."""

    text: str
    confidence: float
    engine: str
    content_format: str = "plain_text"
    review_required: bool | None = None
    blocks: tuple[dict[str, object], ...] = ()
    raw_json: dict[str, object] | None = None


@dataclass(frozen=True)
class RecognitionResult:
    """The stable result returned by the recognition service."""

    markdown: str
    confidence: float
    engine: str
    fallback_used: bool
    status: str
    blocks: tuple[dict[str, object], ...] = ()
    raw_json: dict[str, object] | None = None
    questions: tuple[dict[str, object], ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "markdown": self.markdown,
            "confidence": self.confidence,
            "engine": self.engine,
            "fallback_used": self.fallback_used,
            "status": self.status,
            "blocks": list(self.blocks),
            "raw_json": self.raw_json,
            "questions": list(self.questions),
        }
