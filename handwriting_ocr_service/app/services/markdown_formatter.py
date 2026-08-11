from __future__ import annotations


def format_markdown(
    text: str,
    confidence: float,
    engine: str,
    status: str,
    content_format: str = "plain_text",
    blocks: tuple[dict[str, object], ...] = (),
) -> str:
    """Return a predictable Markdown document from normalized recognition text."""
    normalized_text = text.strip() or "（未识别到文本）"

    block_section = _format_block_section(blocks)
    metadata = (
        "## 识别信息\n\n"
        f"- 引擎：{engine}\n"
        f"- 质量评分：{confidence:.0%}\n"
        f"- 状态：{status}\n"
    )
    if content_format == "markdown":
        return f"{block_section}{normalized_text}\n\n---\n\n{metadata}"

    return (
        "# 手写文本识别结果\n\n"
        f"{block_section}"
        "## 识别文本\n\n"
        f"{normalized_text}\n\n"
        f"{metadata}"
    )


def _format_block_section(blocks: tuple[dict[str, object], ...]) -> str:
    if not blocks:
        return ""

    lines = ["## 版面块识别结果", ""]
    for index, block in enumerate(blocks, start=1):
        block_type = str(block.get("type", "unknown"))
        content = str(block.get("text", "")).strip()
        score = block.get("score")
        confidence_text = f"（{float(score):.0%}）" if isinstance(score, (int, float)) else ""
        lines.append(f"### 块 {index}：{block_type}{confidence_text}")
        if content:
            lines.append("")
            lines.append(content)
        lines.append("")
    return "\n".join(lines) + "\n"
