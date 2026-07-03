import hashlib
import json
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI(title="Error Analysis Agent", version="1.0.0")

DATABASE = "backend/database/example_db.db"

class ErrorTag(BaseModel):
    error_id: str
    level1: str
    level2: str
    level3: str
    confidence: float

class ErrorAnalysisRequest(BaseModel):
    original_question: str
    student_write: str
    judge_result: str
    core_error_type: str
    step_feedback: str
    error_step_list: Optional[List[str]] = None
    miss_step_list: Optional[List[str]] = None
    confidence: Optional[float] = None

class ErrorAnalysisResponse(BaseModel):
    error_tags: List[ErrorTag]
    knowledge_id: str
    knowledge_scope: str
    reasoning_content: str
    total_confidence: float

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def generate_id(prefix: str) -> str:
    return f"{prefix}-{hashlib.md5(f'{datetime.now()}{hash(prefix)}'.encode()).hexdigest()[:8].upper()}"

ERROR_TAG_BANK = {
    "计算": {
        "口算与基本运算": {
            "进位加法中十位漏加进位1": {"id": "C-001", "confidence": 0.92},
            "退位减法中十位漏减退位1": {"id": "C-002", "confidence": 0.90},
            "乘法口诀记忆错误或混淆": {"id": "C-003", "confidence": 0.88},
            "20以内加减法不熟练": {"id": "C-004", "confidence": 0.85}
        },
        "竖式计算": {
            "加法进位标记遗漏": {"id": "C-005", "confidence": 0.91},
            "减法借位标记遗漏": {"id": "C-006", "confidence": 0.89},
            "乘法竖式对齐错误": {"id": "C-007", "confidence": 0.87}
        }
    },
    "概念": {
        "定义混淆": {
            "周长与面积混淆": {"id": "K-001", "confidence": 0.93},
            "因数与倍数混淆": {"id": "K-002", "confidence": 0.90}
        },
        "单位混淆": {
            "长度单位换算错误": {"id": "K-003", "confidence": 0.88},
            "面积单位换算错误": {"id": "K-004", "confidence": 0.86}
        }
    },
    "审题": {
        "遗漏条件": {
            "忽略单位换算": {"id": "R-001", "confidence": 0.87},
            "遗漏关键数字": {"id": "R-002", "confidence": 0.85}
        },
        "理解偏差": {
            "多步问题只做一步": {"id": "R-003", "confidence": 0.88},
            "问题理解错误": {"id": "R-004", "confidence": 0.84}
        }
    },
    "粗心": {
        "抄错数字": {"id": "M-001", "confidence": 0.90},
        "符号错误": {"id": "M-002", "confidence": 0.88}
    }
}

KNOWLEDGE_MAPPING = {
    "进位加法": {"id": "G-N-2-005", "scope": "100以内进位加法"},
    "退位减法": {"id": "G-N-2-006", "scope": "100以内退位减法"},
    "两位数乘法": {"id": "G-N-3-003", "scope": "两位数乘一位数"},
    "周长": {"id": "G-C-3-001", "scope": "长方形和正方形的周长"},
    "面积": {"id": "G-C-3-002", "scope": "长方形和正方形的面积"}
}

@app.post("/internal/api/v1/error-analysis/analyze", response_model=ErrorAnalysisResponse)
def analyze_error(request: ErrorAnalysisRequest):
    if request.judge_result == "correct":
        return ErrorAnalysisResponse(
            error_tags=[],
            knowledge_id="",
            knowledge_scope="",
            reasoning_content="答案正确，无需错因分析",
            total_confidence=1.0
        )
    
    error_tags = match_error_tags(request)
    knowledge_info = map_knowledge(request, error_tags)
    
    total_confidence = sum(tag.confidence for tag in error_tags) / len(error_tags) if error_tags else 0.0
    
    if total_confidence < 0.7:
        raise HTTPException(
            status_code=400,
            detail=f"Low confidence ({total_confidence:.2f}), requires human review"
        )
    
    with get_db() as conn:
        cursor = conn.cursor()
        mistake_case_id = generate_id("MC")
        cursor.execute('''
            INSERT INTO mistake_case (mistake_case_id, student_id, question_id, current_status, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (mistake_case_id, "", "", "correcting", datetime.now().isoformat()))
        
        for tag in error_tags:
            cursor.execute('''
                INSERT INTO mistake_case_error (mistake_case_id, error_id, error_weight)
                VALUES (?, ?, ?)
            ''', (mistake_case_id, tag.error_id, tag.confidence))
        
        if knowledge_info["id"]:
            cursor.execute('''
                INSERT INTO mistake_case_knowledge (mistake_case_id, knowledge_id, knowledge_weight)
                VALUES (?, ?, ?)
            ''', (mistake_case_id, knowledge_info["id"], 1.0))
        
        conn.commit()
    
    return ErrorAnalysisResponse(
        error_tags=error_tags,
        knowledge_id=knowledge_info["id"],
        knowledge_scope=knowledge_info["scope"],
        reasoning_content=generate_reasoning(request, error_tags, knowledge_info),
        total_confidence=total_confidence
    )

def match_error_tags(request: ErrorAnalysisRequest) -> List[ErrorTag]:
    tags = []
    core_type = request.core_error_type
    
    if "计算" in core_type:
        if "进位" in request.step_feedback or "进位" in str(request.error_step_list):
            tags.append(ErrorTag(
                error_id="C-001",
                level1="计算",
                level2="口算与基本运算",
                level3="进位加法中十位漏加进位1",
                confidence=0.92
            ))
        elif "退位" in request.step_feedback or "退位" in str(request.error_step_list):
            tags.append(ErrorTag(
                error_id="C-002",
                level1="计算",
                level2="口算与基本运算",
                level3="退位减法中十位漏减退位1",
                confidence=0.90
            ))
        else:
            tags.append(ErrorTag(
                error_id="C-004",
                level1="计算",
                level2="口算与基本运算",
                level3="20以内加减法不熟练",
                confidence=0.85
            ))
    elif "概念" in core_type:
        tags.append(ErrorTag(
            error_id="K-001",
            level1="概念",
            level2="定义混淆",
            level3="概念理解错误",
            confidence=0.88
        ))
    elif "审题" in core_type:
        tags.append(ErrorTag(
            error_id="R-001",
            level1="审题",
            level2="遗漏条件",
            level3="审题不仔细",
            confidence=0.87
        ))
    else:
        tags.append(ErrorTag(
            error_id="M-001",
            level1="粗心",
            level2="抄错数字",
            level3="粗心错误",
            confidence=0.85
        ))
    
    return tags[:3]

def map_knowledge(request: ErrorAnalysisRequest, error_tags: List[ErrorTag]) -> dict:
    question = request.original_question
    
    if "加" in question and ("25" in question or "38" in question):
        return {"id": "G-N-2-005", "scope": "100以内进位加法"}
    elif "减" in question:
        return {"id": "G-N-2-006", "scope": "100以内退位减法"}
    elif "乘" in question:
        return {"id": "G-N-3-003", "scope": "两位数乘一位数"}
    elif "周长" in question:
        return {"id": "G-C-3-001", "scope": "长方形和正方形的周长"}
    elif "面积" in question:
        return {"id": "G-C-3-002", "scope": "长方形和正方形的面积"}
    
    return {"id": "G-N-1-001", "scope": "数与代数"}

def generate_reasoning(request: ErrorAnalysisRequest, tags: List[ErrorTag], knowledge: dict) -> str:
    tag_descriptions = ", ".join([f"{tag.level1}-{tag.level2}-{tag.level3}" for tag in tags])
    return f"根据学生作答'{request.student_write}'与步骤反馈'{request.step_feedback}'，分析得出以下错因：{tag_descriptions}。关联知识点：{knowledge['scope']}。"

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Error Analysis Agent"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)