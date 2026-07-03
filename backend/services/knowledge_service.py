import hashlib
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI(title="Knowledge Service", version="1.0.0")

DATABASE = "backend/database/example_db.db"

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

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

KNOWLEDGE_BASE = {
    "G-N-2-005": {
        "knowledge_scope": "100以内进位加法",
        "grade": "二年级",
        "unit": "第2单元",
        "explanation": "两位数加两位数时，个位相加满十要向十位进1。计算步骤：1. 相同数位对齐；2. 从个位加起；3. 个位相加满十，向十位进1；4. 十位相加时要加上进位的1。",
        "difficulty": "medium",
        "standard_solution": "以25+38为例：个位5+8=13，写3进1；十位2+3+1=6；结果为63。",
        "prerequisite": "G-N-2-001",
        "next_knowledge": "G-N-2-006",
        "common_errors": "1. 个位相加满十忘记进位；2. 十位相加时忘记加进位的1；3. 数位没有对齐。",
        "forbidden_explanation": "不要提'进位制''位值原理'等术语；不要直接讲竖式书写规范而不讲算理。",
        "example": "计算：25+38=？  46+27=？",
        "teaching_tips": "用小棒演示进位过程，让学生直观感受'个位满十变十位'。先练口算再练竖式。"
    },
    "G-N-2-006": {
        "knowledge_scope": "100以内退位减法",
        "grade": "二年级",
        "unit": "第2单元",
        "explanation": "两位数减两位数时，个位不够减要从十位退1当10。计算步骤：1. 相同数位对齐；2. 从个位减起；3. 个位不够减，从十位退1；4. 十位相减时要减去退走的1。",
        "difficulty": "medium",
        "standard_solution": "以52-28为例：个位2-8不够减，从十位退1得12-8=4；十位5-1-2=2；结果为24。",
        "prerequisite": "G-N-2-005",
        "next_knowledge": "G-N-3-001",
        "common_errors": "1. 个位不够减忘记退位；2. 十位相减时忘记减退位的1；3. 退位后个位计算错误。",
        "forbidden_explanation": "不要提'借位''退位减法法则'等术语；不要只讲步骤不讲算理。",
        "example": "计算：52-28=？  63-27=？",
        "teaching_tips": "用小棒演示退位过程，让学生看到'十位1变成个位10'。强调'退位点'的标记。"
    },
    "G-N-3-003": {
        "knowledge_scope": "两位数乘一位数",
        "grade": "三年级",
        "unit": "第6单元",
        "explanation": "两位数乘一位数，先用一位数乘两位数的个位，再用一位数乘两位数的十位，最后把两次乘得的积相加。如果个位相乘满几十，要向十位进几。",
        "difficulty": "hard",
        "standard_solution": "以24×3为例：4×3=12，写2进1；20×3=60，60+12=72；结果为72。",
        "prerequisite": "G-N-2-003",
        "next_knowledge": "G-N-3-004",
        "common_errors": "1. 忘记进位；2. 十位相乘时忘记加进位；3. 数位对齐错误。",
        "forbidden_explanation": "不要提'乘法分配律'的严格证明；不要直接给公式不讲算理。",
        "example": "计算：24×3=？  36×4=？",
        "teaching_tips": "用点子图或小棒演示乘法意义，把两位数拆成整十数和个位数分别相乘再相加。"
    },
    "G-C-3-001": {
        "knowledge_scope": "长方形和正方形的周长",
        "grade": "三年级",
        "unit": "第7单元",
        "explanation": "封闭图形一周的长度叫做周长。长方形周长=（长+宽）×2；正方形周长=边长×4。",
        "difficulty": "medium",
        "standard_solution": "长方形长5厘米、宽3厘米，周长=(5+3)×2=16厘米。",
        "prerequisite": "G-C-2-001",
        "next_knowledge": "G-C-3-002",
        "common_errors": "1. 周长与面积混淆；2. 长方形周长只算两条边；3. 忘记乘2。",
        "forbidden_explanation": "不要提'周长公式推导'的严格数学证明；不要提前讲面积。",
        "example": "一个长方形长8米、宽5米，周长是多少米？",
        "teaching_tips": "用绳子绕图形一周，让学生直观感受周长。多做测量活动。"
    },
    "G-C-3-002": {
        "knowledge_scope": "长方形和正方形的面积",
        "grade": "三年级",
        "unit": "第5单元",
        "explanation": "物体表面或封闭图形的大小叫做面积。长方形面积=长×宽；正方形面积=边长×边长。",
        "difficulty": "hard",
        "standard_solution": "长方形长5厘米、宽3厘米，面积=5×3=15平方厘米。",
        "prerequisite": "G-C-3-001",
        "next_knowledge": "G-C-4-001",
        "common_errors": "1. 面积与周长混淆；2. 忘记写面积单位；3. 单位换算错误。",
        "forbidden_explanation": "不要提'面积公式推导'的严格数学证明；不要混用周长和面积单位。",
        "example": "一个长方形长8米、宽5米，面积是多少平方米？",
        "teaching_tips": "用小正方形铺满长方形，让学生数个数理解面积公式。强调面积单位的重要性。"
    },
    "G-N-1-001": {
        "knowledge_scope": "数与代数",
        "grade": "—",
        "unit": "—",
        "explanation": "数与代数是数学的基础领域，包括数的认识、运算、应用等内容。",
        "difficulty": "easy",
        "standard_solution": "",
        "prerequisite": "",
        "next_knowledge": "",
        "common_errors": "",
        "forbidden_explanation": "",
        "example": "",
        "teaching_tips": ""
    }
}

@app.post("/internal/api/v1/knowledge/retrieve", response_model=KnowledgeRetrieveResponse)
def retrieve_knowledge(request: KnowledgeRetrieveRequest):
    knowledge = KNOWLEDGE_BASE.get(request.knowledge_id)
    
    if not knowledge:
        raise HTTPException(
            status_code=404,
            detail=f"Knowledge not found: {request.knowledge_id}"
        )
    
    scope_validation = validate_scope(request, knowledge)
    
    if not scope_validation:
        raise HTTPException(
            status_code=400,
            detail="Knowledge scope validation failed (out of syllabus)"
        )
    
    return KnowledgeRetrieveResponse(
        knowledge_explanation=knowledge["explanation"],
        difficulty=knowledge["difficulty"],
        standard_solution=knowledge["standard_solution"],
        scope_validation=scope_validation,
        prerequisite=knowledge["prerequisite"],
        next_knowledge=knowledge["next_knowledge"],
        textbook_version=request.textbook_version,
        unit=knowledge["unit"],
        common_errors=knowledge["common_errors"],
        forbidden_explanation=knowledge["forbidden_explanation"],
        example=knowledge["example"],
        teaching_tips=knowledge["teaching_tips"]
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
        if knowledge["grade"] != "—" and knowledge["grade"] not in allowed_grades:
            return False
    
    return True

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Knowledge Service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)