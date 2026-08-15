import os
import re
import tempfile
from collections import Counter
from pathlib import Path
from threading import Lock
from typing import Any

from app.models import EngineResult


_LATEX_COMMAND_RE = re.compile(
    r"\\(?:times|frac|div|sqrt|cdot|pm|mp|le|ge|leq|geq|neq|approx|equiv|in|notin|sum|prod|int|left|right|alpha|beta|gamma|delta|theta|pi|infty|text|mathrm|mathbf|overline|underline)(?![A-Za-z])"
)
_MATH_DELIMITER_RE = re.compile(r"(?<!\\)(?:\${1,2}|\\(?:\(|\)|\[|\]))")
_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
_FORMULA_CHARACTERS = frozenset(
    "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ\\{}[]()_.,:+-*/=<>| \t·×÷^"
)


def normalize_markdown_math(markdown: str) -> str:
    """Wrap bare LaTeX commands in delimiters understood by Markdown math renderers."""
    normalized_lines: list[str] = []
    fence_marker: str | None = None

    for line in markdown.splitlines():
        fence_match = _FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(1)
            if fence_marker is None:
                fence_marker = marker[0]
            elif marker.startswith(fence_marker):
                fence_marker = None
            normalized_lines.append(line)
            continue

        if fence_marker is not None:
            normalized_lines.append(line)
            continue
        normalized_lines.append(_normalize_math_line(line))

    return "\n".join(normalized_lines)


def _normalize_math_line(line: str) -> str:
    if not _LATEX_COMMAND_RE.search(line) or _MATH_DELIMITER_RE.search(line):
        return line

    heading_match = re.match(r"^(\s*#{1,6}\s+)(.*?)(\s*)$", line)
    if heading_match:
        prefix, content, suffix = heading_match.groups()
        if content and all(character in _FORMULA_CHARACTERS for character in content):
            return f"{prefix}${content}${suffix}"

    command_match = _LATEX_COMMAND_RE.search(line)
    if command_match is None:
        return line

    start = command_match.start()
    while start > 0 and line[start - 1] in _FORMULA_CHARACTERS:
        start -= 1
    end = command_match.end()
    while end < len(line) and line[end] in _FORMULA_CHARACTERS:
        end += 1

    raw_expression = line[start:end]
    expression = raw_expression.strip()
    if not expression:
        return line
    leading = raw_expression[: len(raw_expression) - len(raw_expression.lstrip())]
    trailing = raw_expression[len(raw_expression.rstrip()) :]
    return f"{line[:start]}{leading}${expression}${trailing}{line[end:]}"


class PaddleOCRVLEngine:
    """Adapter for the complete PaddleOCR-VL document parsing pipeline."""

    def __init__(self, device: str = "cpu", pipeline_version: str = "v1.6") -> None:
        os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")
        os.environ.setdefault("PADDLE_PDX_MODEL_SOURCE", "bos")
        if os.name == "nt":
            os.environ.setdefault("PADDLE_PDX_CACHE_HOME", r"C:\PaddleOCRCache")
        os.environ.setdefault("PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT", "False")

        try:
            from paddleocr import PaddleOCRVL
        except Exception as error:
            raise RuntimeError(
                "PaddleOCR-VL could not be imported. Install the doc-parser dependencies "
                "in the dedicated VL virtual environment."
            ) from error

        self._pipeline_version = pipeline_version
        self._predict_lock = Lock()
        self._pipeline = PaddleOCRVL(
            pipeline_version=pipeline_version,
            device=device,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_layout_detection=True,
            use_ocr_for_image_block=True,
            markdown_ignore_labels=["image"],
        )

    def recognize(self, image_bytes: bytes, content_type: str) -> EngineResult:
        temporary_path = ""
        try:
            with tempfile.NamedTemporaryFile(
                suffix=self._suffix_for(content_type), delete=False
            ) as image_file:
                image_file.write(image_bytes)
                temporary_path = image_file.name

            with self._predict_lock:
                page_results = self._pipeline.predict(temporary_path)

            markdown_pages: list[str] = []
            layout_scores: list[float] = []
            blocks: list[dict[str, object]] = []
            raw_results: list[dict[str, object]] = []
            for page_index, page_result in enumerate(page_results, start=1):
                raw_results.append(self._json_safe(page_result))
                parsed_markdown, parsed_blocks = self._parse_page_result(page_result, page_index)
                if parsed_markdown:
                    markdown_pages.append(parsed_markdown)
                layout_scores.extend(self._extract_layout_scores(page_result))
                blocks.extend(parsed_blocks)

            markdown_text = normalize_markdown_math("\n\n".join(markdown_pages).strip())
            quality_score = (
                round(sum(layout_scores) / len(layout_scores), 6)
                if layout_scores
                else 0.0
            )
            return EngineResult(
                text=markdown_text,
                confidence=quality_score,
                engine=f"paddleocr-vl-{self._pipeline_version.removeprefix('v')}",
                content_format="markdown",
                review_required=self._requires_review(markdown_text),
                blocks=tuple(blocks),
                raw_json={"pages": raw_results},
            )
        finally:
            if temporary_path:
                Path(temporary_path).unlink(missing_ok=True)

    @staticmethod
    def _json_safe(value: Any) -> dict[str, object]:
        if isinstance(value, dict):
            return {str(key): PaddleOCRVLEngine._json_safe_item(item) for key, item in value.items()}
        return {"value": PaddleOCRVLEngine._json_safe_item(value)}

    @staticmethod
    def _json_safe_item(value: Any) -> object:
        if isinstance(value, dict):
            return {str(key): PaddleOCRVLEngine._json_safe_item(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [PaddleOCRVLEngine._json_safe_item(item) for item in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if hasattr(value, "__dict__"):
            return PaddleOCRVLEngine._json_safe_item(vars(value))
        return str(value)

    @staticmethod
    def _extract_markdown(page_result: Any) -> str:
        markdown_data = getattr(page_result, "markdown", None)
        if not isinstance(markdown_data, dict):
            return ""
        markdown_text = markdown_data.get("markdown_texts", "")
        if isinstance(markdown_text, str):
            return markdown_text.strip()
        if isinstance(markdown_text, (list, tuple)):
            return "\n\n".join(str(item).strip() for item in markdown_text if item).strip()
        return ""

    @classmethod
    def _parse_page_result(cls, page_result: Any, page_index: int) -> tuple[str, list[dict[str, object]]]:
        markdown_data = getattr(page_result, "markdown", None)
        blocks = cls._extract_blocks(page_result, page_index)
        if isinstance(page_result, dict):
            pruned = page_result.get("prunedResult")
            if isinstance(pruned, dict):
                blocks = cls._extract_pruned_blocks(pruned, page_index)
                markdown_data = pruned.get("markdown") or markdown_data
        markdown_text = cls._extract_markdown_from_payload(markdown_data)
        if not markdown_text and blocks:
            markdown_text = cls._compose_markdown_from_blocks(blocks)
        markdown_text = cls._align_markdown_to_blocks(markdown_text, blocks)
        return markdown_text, blocks

    @staticmethod
    def _extract_markdown_from_payload(markdown_data: Any) -> str:
        if not isinstance(markdown_data, dict):
            return ""
        markdown_text = markdown_data.get("markdown_texts", "")
        if isinstance(markdown_text, str):
            return markdown_text.strip()
        if isinstance(markdown_text, (list, tuple)):
            return "\n\n".join(str(item).strip() for item in markdown_text if item).strip()
        return ""

    @classmethod
    def _extract_pruned_blocks(cls, pruned: dict[str, Any], page_index: int) -> list[dict[str, object]]:
        blocks: list[dict[str, object]] = []
        parsing_res_list = pruned.get("parsing_res_list", [])
        if not isinstance(parsing_res_list, (list, tuple)):
            return blocks
        for block_index, item in enumerate(parsing_res_list, start=1):
            if not isinstance(item, dict):
                continue
            block_type = str(item.get("block_label") or item.get("type") or "unknown")
            blocks.append(
                {
                    "page": page_index,
                    "index": block_index,
                    "type": block_type,
                    "score": item.get("score"),
                    "text": str(item.get("block_content", "")).strip(),
                    "bbox": item.get("block_bbox"),
                }
            )
        return blocks

    @staticmethod
    def _compose_markdown_from_blocks(blocks: list[dict[str, object]]) -> str:
        lines: list[str] = []
        for block in blocks:
            block_type = str(block.get("type", "unknown"))
            content = str(block.get("text", "")).strip()
            if block_type == "image":
                lines.append(f"## 图片块\n\n{content or '（图片）'}")
            elif block_type == "text":
                lines.append(content)
            else:
                lines.append(f"## {block_type}\n\n{content}")
        return "\n\n".join(line for line in lines if line).strip()

    @staticmethod
    def _align_markdown_to_blocks(markdown_text: str, blocks: list[dict[str, object]]) -> str:
        if not markdown_text or not blocks:
            return markdown_text
        markdown_lines = [line.strip() for line in markdown_text.splitlines() if line.strip()]
        if not markdown_lines:
            return markdown_text

        block_lines: list[str] = []
        for block in blocks:
            block_type = str(block.get("type", "unknown"))
            content = str(block.get("text", "")).strip()
            if block_type == "image":
                block_lines.append(content or "（图片）")
            elif content:
                block_lines.extend([segment.strip() for segment in content.splitlines() if segment.strip()])

        if not block_lines:
            return markdown_text

        matched_lines: list[str] = []
        used_indexes: set[int] = set()
        for block_line in block_lines:
            for index, markdown_line in enumerate(markdown_lines):
                if index in used_indexes:
                    continue
                if block_line == markdown_line or block_line in markdown_line or markdown_line in block_line:
                    matched_lines.append(markdown_line)
                    used_indexes.add(index)
                    break

        if matched_lines:
            remaining_lines = [line for index, line in enumerate(markdown_lines) if index not in used_indexes]
            return "\n\n".join(matched_lines + remaining_lines).strip()
        return markdown_text

    @classmethod
    def _extract_layout_scores(cls, page_result: Any) -> list[float]:
        if not isinstance(page_result, dict):
            return []
        return cls._scores_from_layout_result(page_result.get("layout_det_res"))

    @classmethod
    def _extract_blocks(cls, page_result: Any, page_index: int) -> list[dict[str, object]]:
        if not isinstance(page_result, dict):
            return []

        # 优先使用 VL 解析结果（含图片块内的手写/文本转录）
        parsing_res_list = page_result.get("parsing_res_list")
        if isinstance(parsing_res_list, (list, tuple)) and parsing_res_list:
            blocks: list[dict[str, object]] = []
            for block_index, item in enumerate(parsing_res_list, start=1):
                if isinstance(item, dict):
                    block_label = item.get("block_label") or item.get("label") or "unknown"
                    block_content = item.get("block_content") or item.get("content") or ""
                    block_bbox = item.get("block_bbox") or item.get("bbox")
                    score = item.get("score")
                else:
                    block_label = getattr(item, "label", None) or "unknown"
                    block_content = getattr(item, "content", "") or ""
                    block_bbox = getattr(item, "block_bbox", None) or getattr(item, "bbox", None)
                    score = getattr(item, "score", None)
                blocks.append({
                    "page": page_index,
                    "index": block_index,
                    "type": str(block_label),
                    "score": float(score) if isinstance(score, (int, float)) else None,
                    "text": str(block_content).strip(),
                    "bbox": block_bbox,
                })
            return blocks

        layout_result = page_result.get("layout_det_res")
        if not isinstance(layout_result, dict):
            return []

        blocks: list[dict[str, object]] = []
        boxes = layout_result.get("boxes", [])
        if not isinstance(boxes, (list, tuple)):
            return []

        for box_index, box in enumerate(boxes, start=1):
            if not isinstance(box, dict):
                continue
            block_type = str(box.get("label") or box.get("type") or "unknown")
            score = box.get("score")
            block = {
                "page": page_index,
                "index": box_index,
                "type": block_type,
                "score": float(score) if isinstance(score, (int, float, str)) and str(score).strip() else None,
                "text": cls._box_text(box),
            }
            blocks.append(block)
        return blocks

    @staticmethod
    def _box_text(box: dict[str, object]) -> str:
        for key in ("text", "block_content", "markdown_text", "content"):
            value = box.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    @classmethod
    def _scores_from_layout_result(cls, layout_result: Any) -> list[float]:
        if isinstance(layout_result, (list, tuple)):
            scores: list[float] = []
            for item in layout_result:
                scores.extend(cls._scores_from_layout_result(item))
            return scores
        if not isinstance(layout_result, dict):
            return []

        boxes = layout_result.get("boxes", [])
        scores = []
        for box in boxes if isinstance(boxes, (list, tuple)) else []:
            if not isinstance(box, dict) or "score" not in box:
                continue
            try:
                scores.append(float(box["score"]))
            except (TypeError, ValueError):
                continue
        return scores

    @staticmethod
    def _requires_review(markdown_text: str) -> bool:
        if not markdown_text.strip():
            return True
        lines = [line.strip() for line in markdown_text.splitlines() if line.strip()]
        if len(lines) >= 4:
            most_common_count = Counter(lines).most_common(1)[0][1]
            if most_common_count / len(lines) >= 0.6:
                return True
        return False

    @staticmethod
    def _suffix_for(content_type: str) -> str:
        return {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/bmp": ".bmp",
        }.get(content_type.lower(), ".img")
