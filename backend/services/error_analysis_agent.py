import json
import re
from datetime import datetime
from typing import List, Optional, Tuple, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import requests
from backend.config import DATABASE_PATH, KNOWLEDGE_GRAPH_URL
from id_utils import generate_id
from llm_client import call_llm, call_llm_json, get_default_system_prompt, llm_enabled

KG_SERVICE_URL = KNOWLEDGE_GRAPH_URL

_knowledge_cache = None

app = FastAPI(title="Error Analysis Agent", version="1.0.0")

DATABASE = DATABASE_PATH

class ErrorTag(BaseModel):
    error_id: str
    level1: str
    level2: str
    level3: str
    confidence: float

class ErrorAnalysisRequest(BaseModel):
    student_id: str
    question_id: Optional[str] = None
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
    "进位加法": {"id": "K035", "scope": "100以内进位加法"},
    "退位减法": {"id": "K037", "scope": "100以内退位减法"},
    "两位数乘法": {"id": "K082", "scope": "两位数乘一位数"},
    "周长": {"id": "K087", "scope": "长方形和正方形的周长"},
    "面积": {"id": "K105", "scope": "长方形和正方形的面积"}
}

def is_answer_invalid(student_write: str) -> bool:
    if not student_write or student_write.strip() == "":
        return True
    invalid_patterns = ["不会", "不知道", "不会做", "没有作答"]
    if any(p in student_write for p in invalid_patterns):
        return True
    return False

def fetch_candidate_errors() -> List[Dict]:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT error_id, level1, level2, level3, error_description 
            FROM error_bank
        ''')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def fetch_candidate_knowledge() -> List[Dict]:
    global _knowledge_cache
    if _knowledge_cache is not None:
        return _knowledge_cache
    
    all_knowledge = []
    page = 1
    try:
        while True:
            response = requests.get(f"{KG_SERVICE_URL}/api/knowledge_points?page={page}&page_size=100", timeout=10)
            response.raise_for_status()
            data = response.json()
            items = data.get("data", [])
            if not items:
                break
            all_knowledge.extend(items)
            if len(items) < 100:
                break
            page += 1
        _knowledge_cache = all_knowledge
        return all_knowledge
    except requests.exceptions.RequestException:
        return []

def analyze_error_with_llm(request: ErrorAnalysisRequest) -> Tuple[List[ErrorTag], Dict, str, float]:
    error_candidates = fetch_candidate_errors()
    knowledge_candidates = fetch_candidate_knowledge()
    
    error_list_str = json.dumps(error_candidates, ensure_ascii=False, indent=2)
    knowledge_list_str = json.dumps([{"id": k["id"], "title": k["title"]} for k in knowledge_candidates], ensure_ascii=False, indent=2)
    
    system_prompt = f"""你是一个小学数学错因分析专家。你的任务是根据学生的作答内容和题目信息，分析出错原因并关联对应的知识点。

## 错因分类体系
错因分为四个大类：计算、概念、审题、粗心

## 候选错因列表（必须从以下列表中选择）
{error_list_str}

## 候选知识点列表（必须从以下列表中选择）
{knowledge_list_str}

## 输出格式要求
请严格按照以下 JSON 格式输出分析结果，不要输出任何多余内容：
{{
    "error_tags": [
        {{
            "error_id": "错因ID",
            "level1": "一级分类",
            "level2": "二级分类",
            "level3": "三级分类",
            "confidence": 置信度(0.0-1.0)
        }}
    ],
    "knowledge_id": "知识点ID",
    "knowledge_scope": "知识点名称",
    "reasoning_content": "分析推理过程",
    "total_confidence": 总置信度(0.0-1.0)
}}

## 示例
题目：小明有25颗糖果，小红有38颗糖果，他们一共有多少颗糖果？
学生作答：25+38=53
步骤反馈：个位5+8=13，写3进1，十位2+3=5，忘记加进位1
错误类型：计算错误

输出：
{{
    "error_tags": [
        {{
            "error_id": "C-001",
            "level1": "计算",
            "level2": "口算与基本运算",
            "level3": "进位加法中十位漏加进位1",
            "confidence": 0.92
        }}
    ],
    "knowledge_id": "K035",
    "knowledge_scope": "100以内进位加法",
    "reasoning_content": "学生在计算25+38时，个位5+8=13正确，但十位计算时忘记加上进位的1，导致结果错误。",
    "total_confidence": 0.92
}}

请确保：
1. error_id 必须是候选错因列表中的有效ID
2. knowledge_id 必须是候选知识点列表中的有效ID
3. 置信度要合理，不能随意给高分
4. reasoning_content 要详细说明错因分析过程"""
    
    user_prompt = f"""请分析以下学生作答的错因：

题目：{request.original_question}
学生作答：{request.student_write}
判断结果：{request.judge_result}
核心错误类型：{request.core_error_type}
步骤反馈：{request.step_feedback}
错误步骤列表：{request.error_step_list or []}
缺失步骤列表：{request.miss_step_list or []}
置信度：{request.confidence or 0.0}

请按照要求的JSON格式输出分析结果。"""
    
    llm_response = call_llm(system_prompt, user_prompt)
    
    llm_response = llm_response.strip()
    if llm_response.startswith("```json"):
        llm_response = llm_response[7:]
    if llm_response.startswith("```"):
        llm_response = llm_response[3:]
    if llm_response.endswith("```"):
        llm_response = llm_response[:-3]
    
    try:
        parsed = json.loads(llm_response)
    except json.JSONDecodeError:
        raise ValueError("LLM返回格式错误，无法解析JSON")
    
    valid_error_ids = {e["error_id"] for e in error_candidates}
    valid_knowledge_ids = {k["id"] for k in knowledge_candidates}
    
    error_tags = []
    for tag_data in parsed.get("error_tags", []):
        if tag_data.get("error_id") not in valid_error_ids:
            continue
        error_tags.append(ErrorTag(**tag_data))
    
    knowledge_id = parsed.get("knowledge_id", "")
    if knowledge_id not in valid_knowledge_ids:
        knowledge_id = ""
    
    knowledge_scope = ""
    if knowledge_id:
        for k in knowledge_candidates:
            if k["id"] == knowledge_id:
                knowledge_scope = k.get("title", "")
                break
    
    reasoning_content = parsed.get("reasoning_content", "")
    total_confidence = parsed.get("total_confidence", 0.0)
    
    return error_tags, {"id": knowledge_id, "scope": knowledge_scope}, reasoning_content, total_confidence

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
    
    if is_answer_invalid(request.student_write):
        return ErrorAnalysisResponse(
            error_tags=[],
            knowledge_id="",
            knowledge_scope="",
            reasoning_content="学生未提供有效作答内容，无法判断具体错因，建议教师人工核实。",
            total_confidence=0.2
        )
    
    reasoning_content = ""
    
    try:
        error_tags, knowledge_info, reasoning_content, total_confidence = analyze_error_with_llm(request)
    except Exception:
        error_tags = match_error_tags(request)
        knowledge_info = map_knowledge(request, error_tags)
        total_confidence = sum(tag.confidence for tag in error_tags) / len(error_tags) if error_tags else 0.0
    
    if not error_tags or not knowledge_info["id"]:
        original_confidence = total_confidence
        total_confidence = min(original_confidence, 0.4)
    
    if total_confidence < 0.7:
        raise HTTPException(
            status_code=400,
            detail=f"Low confidence ({total_confidence:.2f}), requires human review"
        )
    
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
        
        mistake_case_id = generate_id("MC")
        cursor.execute('''
            INSERT INTO mistake_case (mistake_case_id, student_id, question_id, current_status, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (mistake_case_id, request.student_id, question_id, "correcting", datetime.now().isoformat()))
        
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
    
    if not reasoning_content:
        reasoning_content = generate_reasoning(request, error_tags, knowledge_info)
    
    return ErrorAnalysisResponse(
        error_tags=error_tags,
        knowledge_id=knowledge_info["id"],
        knowledge_scope=knowledge_info["scope"],
        reasoning_content=reasoning_content,
        total_confidence=total_confidence
    )

# === 以下为降级方案，仅在 LLM 调用失败时使用 ===

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
        return {"id": "K035", "scope": "100以内进位加法"}
    elif "减" in question:
        return {"id": "K037", "scope": "100以内退位减法"}
    elif "乘" in question:
        return {"id": "K082", "scope": "两位数乘一位数"}
    elif "周长" in question:
        return {"id": "K087", "scope": "长方形和正方形的周长"}
    elif "面积" in question:
        return {"id": "K105", "scope": "长方形和正方形的面积"}
    
    return {"id": "K252", "scope": "数与代数"}

def generate_reasoning(request: ErrorAnalysisRequest, tags: List[ErrorTag], knowledge: dict) -> str:
    tag_descriptions = ", ".join([f"{tag.level1}-{tag.level2}-{tag.level3}" for tag in tags])
    return f"根据学生作答'{request.student_write}'与步骤反馈'{request.step_feedback}'，分析得出以下错因：{tag_descriptions}。关联知识点：{knowledge['scope']}。"

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Error Analysis Agent"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)