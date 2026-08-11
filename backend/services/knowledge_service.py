import sqlite3
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.config import DATABASE_PATH, DEFAULT_TEXTBOOK_VERSION
from backend.services.cache_utils import cache_get, cache_set
from backend.services.observability import log_event, timed

app = FastAPI(title="Knowledge Service", version="1.0.0")

DATABASE = DATABASE_PATH

class KnowledgeRetrieveRequest(BaseModel):
    knowledge_id: str
    knowledge_scope: Optional[str] = None
    grade: Optional[str] = None
    textbook_version: Optional[str] = "人教版"

class KnowledgeRetrieveResponse(BaseModel):
    knowledge_explanation: str
    difficulty: str
    standard_solution: str
    scope_validation: bool
    prerequisite: str
    next_knowledge: str
    textbook_version: str
    unit: str
    common_errors: str
    forbidden_explanation: str
    example: str
    teaching_tips: str

def fetch_knowledge_from_sqlite(knowledge_id: str, knowledge_scope: str | None = None) -> dict:
    cache_key = f"knowledge:{knowledge_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    import sqlite3
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            """
            SELECT knowledge_id, knowledge_scope, knowledge_name, grade,
                   textbook_version, unit, prerequisite, next_knowledge,
                   difficulty, is_core
            FROM knowledge
            WHERE knowledge_id = ?
            """,
            (knowledge_id,),
        ).fetchone()
        if row is None and knowledge_scope:
            # 兼容两套知识点编号（G-N-* 与 K-*）：按名称模糊匹配一次
            row = conn.execute(
                """
                SELECT knowledge_id, knowledge_scope, knowledge_name, grade,
                       textbook_version, unit, prerequisite, next_knowledge,
                       difficulty, is_core
                FROM knowledge
                WHERE knowledge_scope LIKE ?
                ORDER BY length(knowledge_scope) ASC
                LIMIT 1
                """,
                (f"%{knowledge_scope}%",),
            ).fetchone()
    finally:
        conn.close()

    if not row:
        # 找不到时不再中断整条链路：返回最小兜底数据，教学内容仍由错因分析的知识点名称驱动
        return {
            "id": knowledge_id,
            "title": knowledge_scope or knowledge_id,
            "content": knowledge_scope or "",
            "difficulty": "medium",
            "grade": "",
            "unit": "",
            "prerequisite": "",
            "next_knowledge": "",
            "textbook_version": "",
            "common_mistakes": "",
            "example": "",
            "teaching_points": "",
        }

    payload = {
        "id": row["knowledge_id"],
        "title": row["knowledge_scope"] or row["knowledge_name"],
        "content": row["knowledge_scope"] or "",
        "difficulty": row["difficulty"] or "medium",
        "grade": row["grade"] or "",
        "unit": row["unit"] or "",
        "prerequisite": row["prerequisite"] or "",
        "next_knowledge": row["next_knowledge"] or "",
        "textbook_version": row["textbook_version"] or "",
        "common_mistakes": "",
        "example": "",
        "teaching_points": "",
    }
    cache_set(cache_key, payload)
    return payload

@app.post("/internal/api/v1/knowledge/retrieve", response_model=KnowledgeRetrieveResponse)
@timed("knowledge.retrieve")
def retrieve_knowledge(request: KnowledgeRetrieveRequest):
    log_event("knowledge.request", knowledge_id=request.knowledge_id, grade=request.grade)
    try:
        knowledge = fetch_knowledge_from_sqlite(request.knowledge_id, request.knowledge_scope)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"知识点检索失败: {str(e)}")
    
    scope_validation = validate_scope(request, knowledge)
    
    if not scope_validation:
        raise HTTPException(
            status_code=400,
            detail="Knowledge scope validation failed (out of syllabus)"
        )
    
    return KnowledgeRetrieveResponse(
        knowledge_explanation=knowledge.get("content", ""),
        difficulty=knowledge.get("difficulty", "medium"),
        standard_solution="",
        scope_validation=scope_validation,
        prerequisite=knowledge.get("prerequisite", ""),
        next_knowledge=knowledge.get("next_knowledge", ""),
        textbook_version=knowledge.get("textbook_version") or request.textbook_version or DEFAULT_TEXTBOOK_VERSION,
        unit=knowledge.get("unit", ""),
        common_errors=knowledge.get("common_mistakes", ""),
        forbidden_explanation="",
        example=knowledge.get("example", ""),
        teaching_tips=knowledge.get("teaching_points", "")
    )

def validate_scope(request: KnowledgeRetrieveRequest, knowledge: dict) -> bool:
    if request.grade:
        grade_mapping = {
            "一年级": ["一年级"],
            "二年级": ["一年级", "二年级"],
            "三年级": ["一年级", "二年级", "三年级"],
            "四年级": ["一年级", "二年级", "三年级", "四年级"],
            "五年级": ["一年级", "二年级", "三年级", "四年级", "五年级"],
            "六年级": ["一年级", "二年级", "三年级", "四年级", "五年级", "六年级"]
        }
        allowed_grades = grade_mapping.get(request.grade, [])
        grade = knowledge.get("grade", "")
        if grade != "—" and grade != "" and grade not in allowed_grades:
            return False
    
    return True

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Knowledge Service", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)
