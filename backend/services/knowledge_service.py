import sqlite3
from typing import Optional
from datetime import datetime

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.config import DATABASE_PATH, DEFAULT_TEXTBOOK_VERSION, KNOWLEDGE_GRAPH_URL, HTTP_TIMEOUT_SECONDS
from backend.services.cache_utils import cache_get, cache_set
from backend.services.observability import log_event, timed

app = FastAPI(title="Knowledge Service", version="1.0.0")

KG_SERVICE_URL = KNOWLEDGE_GRAPH_URL
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

def fetch_knowledge_from_graph(knowledge_id: str) -> dict:
    cache_key = f"knowledge:{knowledge_id}"
    cached = cache_get(cache_key)
    if cached:
        return cached

    response = requests.get(f"{KG_SERVICE_URL}/api/knowledge_points/{knowledge_id}", timeout=HTTP_TIMEOUT_SECONDS)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    payload = response.json()
    cache_set(cache_key, payload)
    return payload

@app.post("/internal/api/v1/knowledge/retrieve", response_model=KnowledgeRetrieveResponse)
@timed("knowledge.retrieve")
def retrieve_knowledge(request: KnowledgeRetrieveRequest):
    log_event("knowledge.request", knowledge_id=request.knowledge_id, grade=request.grade)
    try:
        knowledge = fetch_knowledge_from_graph(request.knowledge_id)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=503, detail=f"知识图谱服务不可用: {str(e)}")
    
    if not knowledge:
        raise HTTPException(
            status_code=404,
            detail=f"知识点 {request.knowledge_id} 不存在"
        )
    
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
        prerequisite="",
        next_knowledge="",
        textbook_version=request.textbook_version or DEFAULT_TEXTBOOK_VERSION,
        unit="",
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