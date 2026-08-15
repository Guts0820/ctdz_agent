import base64
import json
import re

import requests

from app.config import Settings
from app.models import EngineResult


def _extract_json(content: str) -> dict:
    text = content.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError("Qwen 未返回可解析的 JSON")
        parsed = json.loads(match.group(0))
    return parsed if isinstance(parsed, dict) else {}


class QwenVisionEngine:
    """基于通义千问 Qwen-VL 的结构化识别引擎（主识别）。"""

    def __init__(self, settings: Settings) -> None:
        if not settings.qwen_is_configured:
            raise ValueError("Qwen vision 未配置完整。")
        self._api_key = settings.qwen_api_key
        self._base_url = settings.qwen_base_url.rstrip("/")
        self._model = settings.qwen_model
        self._timeout_seconds = settings.qwen_timeout_seconds

    def recognize(self, image_bytes: bytes, content_type: str) -> EngineResult:
        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        system_prompt = (
            "你是小学数学作业识别助手。请仔细看整张图片，把题目和学生的作答完整转录出来。\n"
            "要求：\n"
            "1. 只转录图片中可见的文字、算式、数字，不判断对错、不补全缺失内容；\n"
            "2. 看不清的字符标注为 [不确定]；\n"
            "3. 图片中有多道题时，questions 列出全部，original_question/student_write 取第一道题；\n"
            "4. stem 是题目原文（不含学生填写的内容）；answer/student_write 只填学生手写或填写的数字、算式，"
            "作答区域空着就输出空字符串，不要把题目里的括号模板当作作答；\n"
            "4. 必须只输出严格 JSON，不要任何多余文字，格式：\n"
            '{"questions":[{"id":"题号","stem":"题目文本（不含学生填写内容）","answer":"学生填写的答案/作答"}],'
            '"original_question":"第一题题目","student_write":"第一题学生作答"}'
        )
        response = requests.post(
            f"{self._base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{encoded_image}"}},
                            {"type": "text", "text": "请识别这张数学作业图片，按格式输出 JSON。"},
                        ],
                    },
                ],
            },
            timeout=self._timeout_seconds,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        if isinstance(content, list):
            content = "\n".join(item.get("text", "") for item in content if isinstance(item, dict))
        raw_text = str(content).strip()

        parsed = _extract_json(raw_text)
        questions: list[dict[str, object]] = []
        for item in parsed.get("questions") or []:
            if not isinstance(item, dict):
                continue
            questions.append({
                "id": str(item.get("id", "") or ""),
                "stem": str(item.get("stem", "") or "").strip(),
                "answer": str(item.get("answer", "") or "").strip(),
            })

        original_question = str(parsed.get("original_question", "") or "").strip()
        student_write = str(parsed.get("student_write", "") or "").strip()
        if not original_question and questions:
            original_question = str(questions[0].get("stem", "") or "")
        if not student_write and questions:
            student_write = str(questions[0].get("answer", "") or "")

        # 安全护栏：作答不应等于/包含题目全文（VLM 偶发把题目模板当作答）
        if student_write and original_question:
            if student_write == original_question or original_question in student_write:
                student_write = ""

        display_parts: list[str] = []
        if original_question:
            display_parts.append(f"## 题目\n\n{original_question}")
        if student_write:
            display_parts.append(f"## 学生作答\n\n{student_write}")
        if not display_parts:
            display_parts.append(raw_text or "（未识别到内容）")

        text_lines: list[dict[str, object]] = [
            {"text": line.strip(), "score": 1.0}
            for line in student_write.splitlines()
            if line.strip()
        ]
        if not text_lines:
            text_lines = [
                {"text": str(q.get("answer", "") or ""), "score": 1.0}
                for q in questions
                if q.get("answer")
            ]

        return EngineResult(
            text="\n\n".join(display_parts),
            confidence=0.95,
            engine=f"qwen-vl-{self._model}",
            content_format="structured",
            review_required=False,
            blocks=(),
            raw_json={"parsed": parsed, "response": raw_text},
            text_lines=tuple(text_lines),
            parsed={"original_question": original_question, "student_write": student_write, "questions": questions},
        )
