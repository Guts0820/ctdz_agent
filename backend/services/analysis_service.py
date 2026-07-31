import json
from datetime import datetime
from typing import List, Optional
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
import sqlite3
from id_utils import generate_id

app = FastAPI(title="Analysis Service", version="1.0.0")

DATABASE = "backend/database/example_db.db"

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
def process_analysis(request: AnalysisRequest):
    if request.image is None and request.original_question is None:
        raise HTTPException(status_code=400, detail="Either image or original_question is required")
    
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
    standard_answers = ["63", "25+38=63", "25加38等于63"]
    for std in standard_answers:
        if std in answer and len(answer) <= len(std) + 5:
            return True
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
    return {"status": "healthy", "service": "Analysis Service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)