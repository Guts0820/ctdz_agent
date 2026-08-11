import json
import sys
from datetime import datetime
from typing import Optional
from uuid import uuid4
try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.middleware.cors import CORSMiddleware
    from starlette.responses import JSONResponse
except ImportError:
    print("错误：无法导入 fastapi。请运行 'pip install fastapi' 安装依赖。", file=sys.stderr)
    sys.exit(1)
from pydantic import BaseModel
import requests
import sqlite3
import httpx
sys.path.insert(0, 'backend/services')
from backend.config import (
    DEFAULT_GRADE,
    DEFAULT_TEXTBOOK_VERSION,
    DATABASE_PATH,
    service_urls,
    INSIGHT_SERVICE_URL,
    HTTP_TIMEOUT_SECONDS,
    OCR_TIMEOUT_SECONDS,
    SERVICE_HEALTH_TIMEOUT_SECONDS,
)
from backend.services.cache_utils import cache_get, cache_set
from backend.services.observability import log_event, timed
from llm_client import call_llm_json, get_default_system_prompt, llm_enabled
from id_utils import generate_id

app = FastAPI(title="AI Math Error Correction System API Gateway", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERVICE_URLS = service_urls()

DATABASE = DATABASE_PATH

class SubmitRequest(BaseModel):
    student_id: str
    question_id: Optional[str] = None
    image: Optional[str] = None
    original_question: Optional[str] = None
    student_write: Optional[str] = None
    grade: Optional[str] = DEFAULT_GRADE

class SubmitResponse(BaseModel):
    status: str
    data: dict

class CreateBatchRequest(BaseModel):
    class_id: str
    teacher_id: str
    batch_date: str  # 格式: YYYY-MM-DD
    question_ids: list[str]

class BatchResponse(BaseModel):
    batch_id: str
    class_id: str
    teacher_id: str
    batch_date: str
    release_status: str
    question_count: int

class ReleasePartialRequest(BaseModel):
    question_ids: list[str]

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def lookup_knowledge_id(question_id: Optional[str]) -> Optional[str]:
    if not question_id:
        return None

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT knowledge_id FROM question_knowledge_mapping WHERE question_id = ?
            ''',
            (question_id,)
        )
        row = cursor.fetchone()
        if row:
            return row["knowledge_id"]

    return None


def lookup_question_standard_answer(question_id: Optional[str], original_question: Optional[str]) -> Optional[str]:
    cache_key = f"question_answer:{question_id or original_question or ''}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    with get_db() as conn:
        cursor = conn.cursor()
        if question_id:
            cursor.execute("SELECT answer FROM question WHERE question_id = ?", (question_id,))
            row = cursor.fetchone()
            if row and row["answer"]:
                cache_set(cache_key, row["answer"])
                return row["answer"]
        if original_question:
            cursor.execute("SELECT answer FROM question WHERE question_description = ?", (original_question,))
            row = cursor.fetchone()
            if row and row["answer"]:
                cache_set(cache_key, row["answer"])
                return row["answer"]
    return None


def is_answer_released(question_id: Optional[str]) -> bool:
    """判断某道题的答案能否返回给学生。

    True: 可以返回答案（已发布、精细放行过，或不属于任何受控批次）
    False: 不能返回答案（批次锁定状态）
    """
    if not question_id:
        return True
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT hb.release_status
            FROM homework_batch_question hbq
            JOIN homework_batch hb ON hbq.batch_id = hb.batch_id
            WHERE hbq.question_id = ?
            ORDER BY hb.created_at DESC LIMIT 1
            ''',
            (question_id,),
        )
        row = cursor.fetchone()
        if not row:
            return True
        if row["release_status"] == "released":
            return True
        if row["release_status"] == "partial":
            cursor.execute(
                "SELECT 1 FROM question_release_override WHERE question_id = ?",
                (question_id,),
            )
            return cursor.fetchone() is not None
        return False


def build_judge_prompt(question_json: dict, standard_answer: str) -> tuple[str, str]:
    system_prompt = get_default_system_prompt() or "你是一个数学判题专家。"
    user_prompt = json.dumps(
        {
            "task": "judge_math_answer",
            "question": question_json,
            "standard_answer": standard_answer,
            "output_schema": {
                "judge_result": "correct|wrong|copy_warning|unknown",
                "step_feedback": "string",
                "error_step_list": ["string"],
                "miss_step_list": ["string"],
                "is_copy": "boolean",
                "core_error_type": "string",
                "confidence": "number",
            },
            "rules": [
                "只依据题目、学生作答和标准答案判断，不要编造答案",
                "若学生作答与标准答案一致，judge_result 必须为 correct",
                "若明显抄写标准答案但缺少过程，可标记 copy_warning",
                "输出必须是严格 JSON"
            ],
        },
        ensure_ascii=False,
    )
    return system_prompt, user_prompt

@app.post("/api/v1/submit", response_model=SubmitResponse)
@timed("submit_homework")
def submit_homework(request: SubmitRequest):
    request_id = uuid4().hex
    log_event("submit.request", request_id=request_id, student_id=request.student_id, question_id=request.question_id)
    try:
        analysis_result = call_analysis_service(request)
        standard_answer = lookup_question_standard_answer(request.question_id or analysis_result.get("question_id"), analysis_result.get("original_question"))
        if standard_answer and llm_enabled():
            question_json = {
                "original_question": analysis_result.get("original_question") or request.original_question or "",
                "student_write": analysis_result.get("student_write") or request.student_write or "",
                "question_id": request.question_id or analysis_result.get("question_id"),
                "grade": request.grade or DEFAULT_GRADE,
                "textbook_version": DEFAULT_TEXTBOOK_VERSION,
            }
            try:
                system_prompt, user_prompt = build_judge_prompt(question_json, standard_answer)
                llm_judge = call_llm_json(system_prompt, user_prompt)
                analysis_result.update({
                    "judge_result": llm_judge.get("judge_result", analysis_result.get("judge_result", "unknown")),
                    "step_feedback": llm_judge.get("step_feedback", analysis_result.get("step_feedback", "")),
                    "error_step_list": llm_judge.get("error_step_list", analysis_result.get("error_step_list", [])),
                    "miss_step_list": llm_judge.get("miss_step_list", analysis_result.get("miss_step_list", [])),
                    "is_copy": llm_judge.get("is_copy", analysis_result.get("is_copy", False)),
                    "core_error_type": llm_judge.get("core_error_type", analysis_result.get("core_error_type", "")),
                    "confidence": llm_judge.get("confidence", analysis_result.get("confidence", 0.0)),
                })
            except Exception as exc:
                analysis_result["llm_fallback_reason"] = str(exc)

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
            knowledge_id = error_analysis_result.get("knowledge_id", "K252")
        
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
        
        response_data = {
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

        # 答案权限过滤：题目答案未放行时，隐藏标准答案与完整讲解
        if not is_answer_released(question_id):
            response_data["standard_solution"] = None
            response_data["explanation"] = "老师还没放行答案，请先自己订正并再次提交。"
            response_data["hints"] = []
            response_data["answer_released"] = False
        else:
            response_data["answer_released"] = True

        return SubmitResponse(status="success", data=response_data)
    
    except requests.HTTPError as e:
        status = e.response.status_code if e.response is not None else 500
        if 400 <= status < 500:
            raise HTTPException(
                status_code=status,
                detail=f"上游服务错误({status}): {e.response.text[:300] if e.response is not None else e}",
            )
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        log_event("submit.error", request_id=request_id, error=str(e))
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
    # 分析服务内部可能执行真实 OCR（推理约 25 秒/张，首次加载模型更久），
    # 使用 OCR 级别的超时预算，避免图片识别期间被网关判超时。
    response = requests.post(url, json=payload, timeout=OCR_TIMEOUT_SECONDS)
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
        "textbook_version": DEFAULT_TEXTBOOK_VERSION
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
        "grade": DEFAULT_GRADE
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
    response = requests.get(url, timeout=HTTP_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()

# ==================== 教师端批次管理接口（移植自同事仓库） ====================

@app.post("/api/v1/teacher/homework_batch", response_model=BatchResponse)
def create_homework_batch(request: CreateBatchRequest):
    """创建作业批次，默认锁定（locked），学生看不到完整答案。"""
    batch_id = generate_id("HB")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            '''
            INSERT INTO homework_batch (batch_id, class_id, teacher_id, batch_date, release_status, created_at)
            VALUES (?, ?, ?, ?, 'locked', ?)
            ''',
            (batch_id, request.class_id, request.teacher_id, request.batch_date, datetime.now().isoformat()),
        )
        for qid in request.question_ids:
            cursor.execute(
                "INSERT INTO homework_batch_question (batch_id, question_id) VALUES (?, ?)",
                (batch_id, qid),
            )
        conn.commit()
    return BatchResponse(
        batch_id=batch_id,
        class_id=request.class_id,
        teacher_id=request.teacher_id,
        batch_date=request.batch_date,
        release_status="locked",
        question_count=len(request.question_ids),
    )


@app.post("/api/v1/teacher/homework_batch/{batch_id}/release")
def release_batch(batch_id: str):
    """一键放行整批作业。"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT batch_id FROM homework_batch WHERE batch_id = ?", (batch_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"批次不存在: {batch_id}")
        cursor.execute(
            "UPDATE homework_batch SET release_status = 'released', release_time = ? WHERE batch_id = ?",
            (datetime.now().isoformat(), batch_id),
        )
        conn.commit()
    return {"status": "success", "message": f"批次 {batch_id} 已全部放行", "release_status": "released"}


@app.post("/api/v1/teacher/homework_batch/{batch_id}/release_partial")
def release_batch_partial(batch_id: str, request: ReleasePartialRequest):
    """精细放行部分题目。"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT batch_id FROM homework_batch WHERE batch_id = ?", (batch_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail=f"批次不存在: {batch_id}")
        for qid in request.question_ids:
            cursor.execute(
                "INSERT OR IGNORE INTO question_release_override (batch_id, question_id, released_at) VALUES (?, ?, ?)",
                (batch_id, qid, datetime.now().isoformat()),
            )
        cursor.execute(
            "UPDATE homework_batch SET release_status = 'partial', release_time = ? WHERE batch_id = ?",
            (datetime.now().isoformat(), batch_id),
        )
        conn.commit()
    return {
        "status": "success",
        "message": f"已放行 {len(request.question_ids)} 道题目",
        "release_status": "partial",
        "released_count": len(request.question_ids),
    }


@app.get("/api/v1/teacher/homework_batch")
def list_homework_batches(class_id: Optional[str] = None, teacher_id: Optional[str] = None):
    """列出作业批次（含批次内题目），教师端展示用。"""
    with get_db() as conn:
        cursor = conn.cursor()
        sql = "SELECT * FROM homework_batch WHERE 1=1"
        params: list = []
        if class_id:
            sql += " AND class_id = ?"
            params.append(class_id)
        if teacher_id:
            sql += " AND teacher_id = ?"
            params.append(teacher_id)
        sql += " ORDER BY created_at DESC"
        batches = [dict(row) for row in cursor.execute(sql, params).fetchall()]
        for b in batches:
            rows = cursor.execute(
                "SELECT question_id FROM homework_batch_question WHERE batch_id = ?",
                (b["batch_id"],),
            ).fetchall()
            b["question_ids"] = [r["question_id"] for r in rows]
    return {"status": "success", "data": batches}


@app.get("/api/questions")
def list_questions(
    grade: Optional[str] = None,
    knowledge_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
):
    """题库列表（SQLite），供教师端创建作业批次时选题。"""
    with get_db() as conn:
        cursor = conn.cursor()
        where = ["1=1"]
        params: list = []
        if grade:
            where.append("q.grade = ?")
            params.append(grade)
        if knowledge_id:
            where.append("qkm.knowledge_id = ?")
            params.append(knowledge_id)
        where_sql = " AND ".join(where)
        total = cursor.execute(
            f"SELECT COUNT(*) FROM question q LEFT JOIN question_knowledge_mapping qkm ON q.question_id = qkm.question_id WHERE {where_sql}",
            params,
        ).fetchone()[0]
        rows = cursor.execute(
            f'''
            SELECT q.question_id, q.question_description, q.question_type, q.difficulty,
                   q.grade, q.textbook_version, qkm.knowledge_id
            FROM question q
            LEFT JOIN question_knowledge_mapping qkm ON q.question_id = qkm.question_id
            WHERE {where_sql}
            ORDER BY q.question_id
            LIMIT ? OFFSET ?
            ''',
            params + [page_size, (max(page, 1) - 1) * page_size],
        ).fetchall()
    questions = [
        {
            "id": r["question_id"],
            "text": r["question_description"],
            "question_type": r["question_type"],
            "difficulty": r["difficulty"],
            "grade": r["grade"],
            "textbook_version": r["textbook_version"],
            "knowledge_id": r["knowledge_id"],
        }
        for r in rows
    ]
    return {"status": "success", "data": questions, "total": total, "page": page, "page_size": page_size}


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def insight_proxy(path: str, request: Request):
    """统一 API 入口：网关本地未处理的 /api/* 请求转发到 Insight 服务（8010）。

    网关已注册的 /api/v1/submit、/api/v1/student/{id}/mastery 会优先匹配本地路由，
    其余（登录/注册/错题本/报告/复习等）统一经此转发，前端只需访问 8000 一个端口。
    """
    url = f"{INSIGHT_SERVICE_URL.rstrip('/')}/api/{path}"
    body = await request.body()
    headers = {}
    if body:
        headers["Content-Type"] = request.headers.get("content-type", "application/json")
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            resp = await client.request(
                request.method,
                url,
                params=dict(request.query_params),
                content=body or None,
                headers=headers,
            )
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Insight 服务不可用: {exc}")

    content = None
    if resp.content:
        try:
            content = resp.json()
        except Exception:
            content = resp.text
    return JSONResponse(status_code=resp.status_code, content=content)


@app.get("/health")
def health_check():
    results = {}
    for service, url in SERVICE_URLS.items():
        try:
            response = requests.get(f"{url}/health", timeout=SERVICE_HEALTH_TIMEOUT_SECONDS)
            results[service] = response.json()
        except Exception as exc:
            results[service] = {"status": "unhealthy", "error": str(exc)}
    overall_status = "healthy" if all(v.get("status") == "healthy" for v in results.values()) else "degraded"
    return {"api_gateway": overall_status, "services": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
