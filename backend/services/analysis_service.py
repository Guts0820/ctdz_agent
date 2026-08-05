import json
import base64
import io
import os
import sys
import time
from datetime import datetime
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from fastapi import FastAPI, HTTPException
except ImportError:
    # 如果fastapi未安装，提供友好的错误提示
    import sys
    print("错误：无法导入 fastapi。请安装依赖：pip install fastapi", file=sys.stderr)
    # 使用占位符类以便代码可以解析，但会在运行时提示错误
    class FastAPI:
        def __init__(self, *args, **kwargs):
            raise ImportError("fastapi 未安装。请运行：pip install fastapi")
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)
from pydantic import BaseModel
import requests
import sqlite3
from backend.config import (
    DATABASE_PATH,
    OCR_ENABLED,
    OCR_MIN_CONFIDENCE,
    OCR_SERVICE_URL,
    OCR_TIMEOUT_SECONDS,
)
from backend.services.observability import log_event, timed
from id_utils import generate_id
from llm_client import call_llm_json, llm_enabled

app = FastAPI(title="Analysis Service", version="1.0.0")

DATABASE = DATABASE_PATH

class AnalysisRequest(BaseModel):
    student_id: str
    question_id: Optional[str] = None
    image: Optional[str] = None
    original_question: Optional[str] = None
    student_write: Optional[str] = None
    standard_solve_steps: Optional[str] = None
    text_status: str = "normal"

class AnalysisResponse(BaseModel):
    judge_result: str
    step_feedback: str
    error_step_list: List[str]
    miss_step_list: List[str]
    is_copy: bool
    core_error_type: str
    confidence: float
    original_question: str
    student_write: str
    text_status: str
    student_id: str
    question_id: Optional[str] = None

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.post("/internal/api/v1/analysis/process", response_model=AnalysisResponse)
@timed("analysis.process")
def process_analysis(request: AnalysisRequest):
    log_event("analysis.request", student_id=request.student_id, question_id=request.question_id)
    if request.image is None and request.original_question is None:
        raise HTTPException(status_code=400, detail="Either image or original_question is required")
    
    if request.image and OCR_ENABLED:
        ocr_result = run_ocr(request)
    else:
        ocr_result = simulate_ocr(request)
    
    if ocr_result["text_status"] != "normal":
        raise HTTPException(
            status_code=400,
            detail=f"OCR failed: {ocr_result['text_status']}"
        )
    
    parse_result = simulate_parse(ocr_result)
    
    process_result = simulate_process_check(parse_result, request.standard_solve_steps)
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        question_id = request.question_id
        if not question_id and request.original_question:
            cursor.execute('''
                SELECT question_id FROM question WHERE question_description = ?
            ''', (request.original_question,))
            row = cursor.fetchone()
            if row:
                question_id = row["question_id"]
        
        cursor.execute('''
            INSERT INTO answer_history (
                answer_history_id, student_id, question_id, submit_type, submit_count,
                ocr_question, student_ocr_answer, student_ocr_steps, is_correct,
                judge_result, step_feedback, error_step_list, miss_step_list,
                is_copy, core_error_type, confidence, submitted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            generate_id("AH"),
            request.student_id,
            question_id,
            "首次错题",
            1,
            process_result["original_question"],
            process_result["student_write"],
            "",
            process_result["judge_result"] == "correct",
            process_result["judge_result"],
            process_result["step_feedback"],
            json.dumps(process_result["error_step_list"]),
            json.dumps(process_result["miss_step_list"]),
            process_result["is_copy"],
            process_result["core_error_type"],
            process_result["confidence"],
            datetime.now().isoformat()
        ))
        conn.commit()
    
    process_result["student_id"] = request.student_id
    process_result["question_id"] = request.question_id
    return AnalysisResponse(**process_result)


# ---------- 真实 OCR 集成（handwriting_ocr_service，端口 8087） ----------

def decode_image(image: str) -> tuple[bytes, str]:
    """把 base64 图片（支持 data URI）解码为字节流和 content-type。"""
    if image.startswith("data:"):
        header, _, b64 = image.partition(",")
        content_type = header.split(";")[0].replace("data:", "") or "image/png"
    else:
        content_type = "image/png"
        b64 = image
    return base64.b64decode(b64), content_type


def call_ocr_service(image_bytes: bytes, content_type: str) -> dict:
    """调用 handwriting_ocr_service 的 POST /v1/recognize。"""
    url = f"{OCR_SERVICE_URL.rstrip('/')}/v1/recognize"
    response = requests.post(
        url,
        files={"image": ("image", io.BytesIO(image_bytes), content_type)},
        timeout=OCR_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def separate_question_answer(markdown: str, ocr_data: dict, request: AnalysisRequest) -> dict:
    """把 OCR 出的整段文字拆成题目和学生作答：LLM 优先，规则兜底。"""
    markdown = (markdown or "").strip()

    if markdown and llm_enabled():
        try:
            system_prompt = (
                "你是OCR后处理助手。把图片识别出的整段文字拆成\"题目\"和\"学生作答\"两部分，"
                "只输出严格JSON：{\"original_question\": \"...\", \"student_write\": \"...\"}。"
                "无法区分时 student_write 可为空字符串，不要编造内容。"
            )
            result = call_llm_json(system_prompt, f"识别文本：\n{markdown}")
            question = str(result.get("original_question", "") or "").strip()
            answer = str(result.get("student_write", "") or "").strip()
            if question:
                return {"original_question": question, "student_write": answer}
        except Exception:
            pass

    return rule_based_separation(markdown, ocr_data, request)


def rule_based_separation(markdown: str, ocr_data: dict, request: AnalysisRequest) -> dict:
    """规则兜底：优先用 OCR 服务的 questions 字段，其次按行启发式拆分。"""
    cleaned = markdown
    for token in ("![", "# "):
        cleaned = cleaned.replace(token, "")

    questions = ocr_data.get("questions") or []
    if questions:
        stem = str(questions[0].get("stem", "") or "").strip()
        if stem:
            rest = cleaned.replace(stem, "").strip()
            return {
                "original_question": stem,
                "student_write": rest or request.student_write or "",
            }

    lines = [ln.strip() for ln in cleaned.splitlines() if ln.strip()]
    question_lines = [ln for ln in lines if "？" in ln or "?" in ln]
    if question_lines and len(question_lines) < len(lines):
        answer_lines = [ln for ln in lines if ln not in question_lines]
        return {
            "original_question": "\n".join(question_lines),
            "student_write": "\n".join(answer_lines),
        }

    for label in ("学生作答", "作答", "答案"):
        if label in cleaned:
            _, _, tail = cleaned.partition(label)
            tail = tail.strip().lstrip("：: ")
            if tail:
                head = cleaned.split(label)[0].strip()
                return {"original_question": head, "student_write": tail}

    return {"original_question": cleaned, "student_write": request.student_write or ""}


def run_ocr(request: AnalysisRequest) -> dict:
    """执行真实 OCR，并做题目/作答分离；OCR 不可用时优雅回退到文本输入。"""
    try:
        image_bytes, content_type = decode_image(request.image)
        ocr_data = call_ocr_service(image_bytes, content_type)
    except Exception as exc:
        log_event("ocr.unavailable", error=str(exc))
        if request.original_question or request.student_write:
            return simulate_ocr(request)
        return {"text_status": "ocr_unavailable", "original_question": "", "student_write": ""}

    status = ocr_data.get("status", "success")
    markdown = str(ocr_data.get("markdown", "") or "")
    try:
        confidence = float(ocr_data.get("confidence", 0.0) or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0
    engine = str(ocr_data.get("engine", "") or "")

    if status == "low_confidence" or confidence < OCR_MIN_CONFIDENCE:
        log_event("ocr.low_confidence", confidence=confidence, engine=engine)
        if request.original_question or request.student_write:
            return simulate_ocr(request)
        return {
            "text_status": "low_confidence",
            "original_question": markdown,
            "student_write": "",
            "confidence": confidence,
            "engine": engine,
        }

    separated = separate_question_answer(markdown, ocr_data, request)
    return {
        "text_status": "normal",
        "original_question": separated["original_question"] or request.original_question or markdown,
        "student_write": separated["student_write"] or request.student_write or "",
        "confidence": confidence,
        "engine": engine,
        "ocr_markdown": markdown,
    }

def simulate_ocr(request: AnalysisRequest) -> dict:
    if request.image:
        text_status = "normal"
        original_question = request.original_question or "小明有25颗糖果，小红有38颗糖果，他们一共有多少颗糖果？"
        student_write = request.student_write or "25+38=53"
    elif request.original_question:
        text_status = "normal"
        original_question = request.original_question
        student_write = request.student_write or ""
    else:
        text_status = "empty"
        original_question = ""
        student_write = ""
    
    return {
        "text_status": text_status,
        "original_question": original_question,
        "student_write": student_write
    }

def simulate_parse(ocr_result: dict) -> dict:
    return {
        "original_question": ocr_result["original_question"],
        "student_write": ocr_result["student_write"]
    }

def simulate_process_check(parse_result: dict, standard_steps: Optional[str]) -> dict:
    question = parse_result["original_question"]
    answer = parse_result["student_write"]
    
    if not answer or answer.strip() == "":
        return {
            "judge_result": "unknown",
            "step_feedback": "未作答",
            "error_step_list": [],
            "miss_step_list": ["未作答"],
            "is_copy": False,
            "core_error_type": "未作答",
            "confidence": 0.95,
            "original_question": question,
            "student_write": answer,
            "text_status": "normal"
        }
    
    is_copy = check_plagiarism(answer)
    
    if is_copy:
        return {
            "judge_result": "copy_warning",
            "step_feedback": "检测到疑似抄袭",
            "error_step_list": [],
            "miss_step_list": [],
            "is_copy": True,
            "core_error_type": "疑似抄袭",
            "confidence": 0.90,
            "original_question": question,
            "student_write": answer,
            "text_status": "normal"
        }
    
    steps = analyze_steps(question, answer)
    
    return steps

def check_plagiarism(answer: str) -> bool:
    # 防抄袭检测按会议决定暂缓开发（低龄段看图题误判风险高），仅保留接口。
    # 原实现是简单的子串匹配，会把"63"这类正确短答案误判为抄袭，故先禁用。
    return False

def analyze_steps(question: str, answer: str) -> dict:
    if "25" in question and "38" in question:
        if "63" in answer:
            return {
                "judge_result": "correct",
                "step_feedback": "计算正确！",
                "error_step_list": [],
                "miss_step_list": [],
                "is_copy": False,
                "core_error_type": "",
                "confidence": 0.95,
                "original_question": question,
                "student_write": answer,
                "text_status": "normal"
            }
        elif "53" in answer:
            return {
                "judge_result": "wrong",
                "step_feedback": "十位计算时忘记加进位的1。个位5+8=13，写3进1，十位2+3+1=6，结果应为63。",
                "error_step_list": ["十位计算错误：2+3忘记加进位的1"],
                "miss_step_list": [],
                "is_copy": False,
                "core_error_type": "计算失误",
                "confidence": 0.92,
                "original_question": question,
                "student_write": answer,
                "text_status": "normal"
            }
        else:
            return {
                "judge_result": "wrong",
                "step_feedback": "计算结果不正确，请重新检查计算过程。",
                "error_step_list": ["计算结果错误"],
                "miss_step_list": [],
                "is_copy": False,
                "core_error_type": "计算失误",
                "confidence": 0.85,
                "original_question": question,
                "student_write": answer,
                "text_status": "normal"
            }
    
    return {
        "judge_result": "unknown",
        "step_feedback": "无法识别题目类型",
        "error_step_list": [],
        "miss_step_list": [],
        "is_copy": False,
        "core_error_type": "未知",
        "confidence": 0.50,
        "original_question": question,
        "student_write": answer,
        "text_status": "normal"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Analysis Service", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)
