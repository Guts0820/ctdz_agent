import json
import sys
from datetime import datetime
from typing import Optional
try:
    from fastapi import FastAPI, HTTPException
except ImportError:
    print("错误：无法导入 fastapi。请运行 'pip install fastapi' 安装依赖。", file=sys.stderr)
    sys.exit(1)
from pydantic import BaseModel
import requests
import sqlite3
sys.path.insert(0, 'backend/services')
from id_utils import generate_id

app = FastAPI(title="AI Math Error Correction System API Gateway", version="1.0.0")

SERVICE_URLS = {
    "analysis": "http://127.0.0.1:8081",
    "error_analysis": "http://127.0.0.1:8082",
    "knowledge": "http://127.0.0.1:8083",
    "teaching": "http://127.0.0.1:8084",
    "state": "http://127.0.0.1:8085",
    "knowledge_graph": "http://127.0.0.1:8007"
}

DATABASE = "backend/database/example_db.db"

class SubmitRequest(BaseModel):
    student_id: str
    question_id: Optional[str] = None
    image: Optional[str] = None
    original_question: Optional[str] = None
    student_write: Optional[str] = None
    grade: Optional[str] = "三年级"

class SubmitResponse(BaseModel):
    status: str
    data: dict

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def lookup_knowledge_id(question_id: Optional[str]) -> Optional[str]:
    if not question_id:
        return None
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT knowledge_id FROM question_knowledge_mapping WHERE question_id = ?
        ''', (question_id,))
        row = cursor.fetchone()
        if row:
            return row["knowledge_id"]
    
    return None

@app.post("/api/v1/submit", response_model=SubmitResponse)
def submit_homework(request: SubmitRequest):
    try:
        analysis_result = call_analysis_service(request)
        
        if analysis_result["is_copy"]:
            guide_result = call_teaching_guide(analysis_result)
            return SubmitResponse(
                status="success",
                data={
                    "judge_result": analysis_result["judge_result"],
                    "is_copy": True,
                    "hints": guide_result.get("hints", []),
                    "explanation": "检测到疑似抄袭，请完成引导问题后重新提交",
                    "next_action": "guide"
                }
            )
        
        question_id = request.question_id or analysis_result.get("question_id")
        knowledge_id = lookup_knowledge_id(question_id)
        
        if analysis_result["judge_result"] == "correct":
            if not knowledge_id:
                return SubmitResponse(
                    status="success",
                    data={
                        "judge_result": "correct",
                        "step_feedback": analysis_result["step_feedback"],
                        "master_level": 1.0,
                        "next_action": "guide",
                        "warning": "无法确定题目对应的知识点，跳过状态更新"
                    }
                )
            
            state_result = call_state_service(request.student_id, knowledge_id, True, analysis_result["confidence"])
            return SubmitResponse(
                status="success",
                data={
                    "judge_result": "correct",
                    "step_feedback": analysis_result["step_feedback"],
                    "knowledge_id": knowledge_id,
                    "master_level": state_result["master_level"],
                    "next_action": state_result["next_action"]
                }
            )
        
        error_analysis_result = call_error_analysis_service(analysis_result)
        
        if not knowledge_id:
            knowledge_id = error_analysis_result.get("knowledge_id", "G-N-1-001")
        
        knowledge_result = call_knowledge_service({"knowledge_id": knowledge_id, "knowledge_scope": error_analysis_result.get("knowledge_scope", "")})
        
        frequency_result = call_frequency_check(request.student_id, knowledge_id)
        
        if not frequency_result["push_permission"]:
            state_result = call_state_service(request.student_id, knowledge_id, False, error_analysis_result["total_confidence"])
            
            return SubmitResponse(
                status="success",
                data={
                    "judge_result": analysis_result["judge_result"],
                    "step_feedback": analysis_result["step_feedback"],
                    "error_tags": error_analysis_result["error_tags"],
                    "knowledge_scope": error_analysis_result["knowledge_scope"],
                    "explanation": knowledge_result["knowledge_explanation"],
                    "master_level": state_result["master_level"],
                    "next_action": "frequency_limit_exceeded",
                    "frequency_info": frequency_result
                }
            )
        
        state_before = call_state_service(request.student_id, knowledge_id, False, error_analysis_result["total_confidence"])
        
        teaching_result = call_teaching_service(error_analysis_result, state_before["master_level"], analysis_result)
        
        if state_before["should_generate_review"]:
            review_result = call_generate_review(request.student_id, knowledge_id, state_before["knowledge_mastery_id"], state_before["master_level"])
        else:
            review_result = None
        
        return SubmitResponse(
            status="success",
            data={
                "judge_result": analysis_result["judge_result"],
                "step_feedback": analysis_result["step_feedback"],
                "error_step_list": analysis_result["error_step_list"],
                "miss_step_list": analysis_result["miss_step_list"],
                "is_copy": analysis_result["is_copy"],
                "core_error_type": analysis_result["core_error_type"],
                "confidence": analysis_result["confidence"],
                "error_tags": error_analysis_result["error_tags"],
                "knowledge_id": knowledge_id,
                "knowledge_scope": error_analysis_result["knowledge_scope"],
                "knowledge_explanation": knowledge_result["knowledge_explanation"],
                "difficulty": knowledge_result["difficulty"],
                "standard_solution": knowledge_result["standard_solution"],
                "explanation": teaching_result["explanation"],
                "hints": teaching_result["hints"],
                "practice_list": teaching_result["practice_list"],
                "teaching_mode": teaching_result["teaching_mode"],
                "master_level": state_before["master_level"],
                "next_action": state_before["next_action"],
                "correct_count": state_before["correct_count"],
                "wrong_count": state_before["wrong_count"],
                "mastery_status": state_before["mastery_status"],
                "review_plan": review_result
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def call_analysis_service(request: SubmitRequest) -> dict:
    url = f"{SERVICE_URLS['analysis']}/internal/api/v1/analysis/process"
    payload = {
        "student_id": request.student_id,
        "question_id": request.question_id,
        "image": request.image,
        "original_question": request.original_question,
        "student_write": request.student_write,
        "text_status": "normal"
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()

def call_error_analysis_service(analysis_result: dict) -> dict:
    url = f"{SERVICE_URLS['error_analysis']}/internal/api/v1/error-analysis/analyze"
    payload = {
        "student_id": analysis_result.get("student_id", ""),
        "question_id": analysis_result.get("question_id"),
        "original_question": analysis_result["original_question"],
        "student_write": analysis_result["student_write"],
        "judge_result": analysis_result["judge_result"],
        "core_error_type": analysis_result["core_error_type"],
        "step_feedback": analysis_result["step_feedback"],
        "error_step_list": analysis_result["error_step_list"],
        "miss_step_list": analysis_result["miss_step_list"],
        "confidence": analysis_result["confidence"]
    }
    response = requests.post(url, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()

def call_knowledge_service(error_analysis_result: dict) -> dict:
    url = f"{SERVICE_URLS['knowledge']}/internal/api/v1/knowledge/retrieve"
    payload = {
        "knowledge_id": error_analysis_result["knowledge_id"],
        "knowledge_scope": error_analysis_result["knowledge_scope"],
        "textbook_version": "人教版"
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()

def call_teaching_service(error_analysis_result: dict, master_level: float, analysis_result: dict) -> dict:
    url = f"{SERVICE_URLS['teaching']}/internal/api/v1/teaching/generate"
    payload = {
        "error_tags": error_analysis_result["error_tags"],
        "knowledge_scope": error_analysis_result["knowledge_scope"],
        "master_level": master_level,
        "original_question": analysis_result["original_question"],
        "student_write": analysis_result["student_write"],
        "difficulty": "medium",
        "grade": "三年级"
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()

def call_state_service(student_id: str, knowledge_id: str, is_correct: bool, confidence: float) -> dict:
    url = f"{SERVICE_URLS['state']}/internal/api/v1/state/update"
    payload = {
        "student_id": student_id,
        "knowledge_id": knowledge_id,
        "is_correct": is_correct,
        "confidence": confidence
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()

def call_frequency_check(student_id: str, knowledge_id: str) -> dict:
    url = f"{SERVICE_URLS['teaching']}/internal/api/v1/teaching/frequency-check"
    payload = {
        "student_id": student_id,
        "knowledge_id": knowledge_id,
        "current_time": datetime.now().isoformat()
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()

def call_generate_review(student_id: str, knowledge_id: str, knowledge_mastery_id: str, master_level: float) -> dict:
    url = f"{SERVICE_URLS['state']}/internal/api/v1/state/generate-review"
    payload = {
        "student_id": student_id,
        "knowledge_id": knowledge_id,
        "knowledge_mastery_id": knowledge_mastery_id,
        "master_level": master_level
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()

def call_teaching_guide(analysis_result: dict) -> dict:
    url = f"{SERVICE_URLS['teaching']}/internal/api/v1/teaching/generate"
    payload = {
        "error_tags": [],
        "knowledge_scope": "引导模式",
        "master_level": 0.9,
        "original_question": analysis_result["original_question"],
        "student_write": analysis_result["student_write"]
    }
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    return response.json()

@app.get("/api/v1/student/{student_id}/mastery")
def get_student_mastery(student_id: str):
    url = f"{SERVICE_URLS['state']}/internal/api/v1/state/mastery/{student_id}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()

@app.get("/health")
def health_check():
    results = {}
    for service, url in SERVICE_URLS.items():
        try:
            response = requests.get(f"{url}/health", timeout=3)
            results[service] = response.json()
        except:
            results[service] = {"status": "unhealthy"}
    return {"api_gateway": "healthy", "services": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)