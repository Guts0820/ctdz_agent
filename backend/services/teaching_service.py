import json
from datetime import datetime
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from id_utils import generate_id

app = FastAPI(title="Teaching Service", version="1.0.0")

DATABASE = "backend/database/example_db.db"

class ErrorTag(BaseModel):
    error_id: str
    level1: str
    level2: str
    level3: str

class PracticeQuestion(BaseModel):
    question_id: str
    question_description: str
    difficulty: str
    answer: str
    solution: str

class TeachingGenerateRequest(BaseModel):
    error_tags: List[ErrorTag]
    knowledge_scope: str
    master_level: float
    original_question: str
    student_write: str
    difficulty: Optional[str] = "medium"
    grade: Optional[str] = "三年级"

class TeachingGenerateResponse(BaseModel):
    explanation: str
    hints: List[str]
    practice_list: List[PracticeQuestion]
    reasoning_content: str
    teaching_mode: str

class FrequencyCheckRequest(BaseModel):
    student_id: str
    knowledge_id: str
    current_time: str

class FrequencyCheckResponse(BaseModel):
    push_permission: bool
    daily_push_count: int
    daily_limit: int
    weekly_push_count: int
    weekly_limit: int
    remaining_daily: int
    remaining_weekly: int

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

TEACHING_TEMPLATES = {
    "K035": {
        "basic_explain": "我们来学习两位数加两位数的进位加法。当两个数相加时，个位上的数字加起来如果等于或超过10，就要向十位进1。比如25+38，个位5+8=13，我们在个位写3，然后向十位进1，十位上2+3再加上进位的1等于6，所以结果是63。",
        "standard_explain": "两位数加两位数进位加法的计算方法：1. 相同数位对齐；2. 从个位加起；3. 个位相加满十，向十位进1；4. 十位相加时要记得加上进位的1。",
        "advanced_explain": "你已经掌握了进位加法的基本方法，继续加油！记住进位标记很重要哦。",
        "basic_hints": ["先算个位，5+8等于多少？", "个位满十了吗？满十要怎么办？", "十位上的2+3还要加什么？"],
        "standard_hints": ["检查一下个位相加是否满十", "十位相加时有没有忘记加进位"],
        "advanced_hints": ["你能说说进位加法的关键步骤吗？", "如果个位相加等于9，需要进位吗？"],
        "basic_practice": [
            {"question": "18+25=？", "answer": "43", "solution": "个位8+5=13，写3进1；十位1+2+1=4"},
            {"question": "36+17=？", "answer": "53", "solution": "个位6+7=13，写3进1；十位3+1+1=5"}
        ],
        "standard_practice": [
            {"question": "45+28=？", "answer": "73", "solution": "个位5+8=13，写3进1；十位4+2+1=7"},
            {"question": "56+37=？", "answer": "93", "solution": "个位6+7=13，写3进1；十位5+3+1=9"}
        ]
    },
    "K037": {
        "basic_explain": "我们来学习两位数减两位数的退位减法。当个位上的数字不够减时，要从十位借1当10。比如52-28，个位2-8不够减，从十位借1变成12，12-8=4；十位上5被借走1剩4，4-2=2，所以结果是24。",
        "standard_explain": "两位数减两位数退位减法的计算方法：1. 相同数位对齐；2. 从个位减起；3. 个位不够减，从十位退1；4. 十位相减时要减去退走的1。",
        "advanced_explain": "你已经掌握了退位减法的基本方法，注意退位标记哦！",
        "basic_hints": ["个位2-8够减吗？不够减怎么办？", "从十位借1后，个位变成多少？", "十位上的5被借走1后还剩多少？"],
        "standard_hints": ["检查一下个位是否需要退位", "十位相减时有没有忘记减退位"],
        "advanced_hints": ["你能说说退位减法的关键步骤吗？", "如果个位刚好够减，还需要退位吗？"],
        "basic_practice": [
            {"question": "42-18=？", "answer": "24", "solution": "个位2-8不够减，借1得12-8=4；十位4-1-1=2"},
            {"question": "53-27=？", "answer": "26", "solution": "个位3-7不够减，借1得13-7=6；十位5-1-2=2"}
        ],
        "standard_practice": [
            {"question": "64-38=？", "answer": "26", "solution": "个位4-8不够减，借1得14-8=6；十位6-1-3=2"},
            {"question": "72-45=？", "answer": "27", "solution": "个位2-5不够减，借1得12-5=7；十位7-1-4=2"}
        ]
    },
    "default": {
        "basic_explain": "我们来复习这个知识点。仔细看题目，按照正确的方法一步步计算。",
        "standard_explain": "这个知识点的关键是理解计算方法，按照步骤来做。",
        "advanced_explain": "你已经基本掌握了这个知识点，继续巩固！",
        "basic_hints": ["第一步应该做什么？", "这里需要注意什么？", "再检查一遍计算过程"],
        "standard_hints": ["检查一下计算步骤", "有没有遗漏什么？"],
        "advanced_hints": ["你能说说这个知识点的关键吗？", "如果换一种方法会怎么做？"],
        "basic_practice": [
            {"question": "练习题1", "answer": "答案1", "solution": "解析1"},
            {"question": "练习题2", "answer": "答案2", "solution": "解析2"}
        ],
        "standard_practice": [
            {"question": "变式题1", "answer": "答案1", "solution": "解析1"},
            {"question": "变式题2", "answer": "答案2", "solution": "解析2"}
        ]
    }
}

def get_teaching_template(knowledge_scope: str) -> dict:
    if "加法" in knowledge_scope:
        return TEACHING_TEMPLATES["K035"]
    elif "减法" in knowledge_scope:
        return TEACHING_TEMPLATES["K037"]
    else:
        return TEACHING_TEMPLATES["default"]

@app.post("/internal/api/v1/teaching/generate", response_model=TeachingGenerateResponse)
def generate_teaching(request: TeachingGenerateRequest):
    template = get_teaching_template(request.knowledge_scope)
    
    if request.master_level < 0.4:
        teaching_mode = "BASIC"
        explanation = template["basic_explain"]
        hints = template["basic_hints"]
        practice_data = template["basic_practice"]
    elif 0.4 <= request.master_level <= 0.8:
        teaching_mode = "STANDARD"
        explanation = template["standard_explain"]
        hints = template["standard_hints"]
        practice_data = template["standard_practice"]
    else:
        teaching_mode = "ADVANCED"
        explanation = template["advanced_explain"]
        hints = template["advanced_hints"]
        practice_data = []
    
    practice_list = [
        PracticeQuestion(
            question_id=generate_id("Q"),
            question_description=p["question"],
            difficulty=request.difficulty,
            answer=p["answer"],
            solution=p["solution"]
        ) for p in practice_data
    ]
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO teaching_content (
                teaching_content_id, mistake_case_id, explanation, hints,
                practice_list, reasoning_content, master_level, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            generate_id("TC"),
            "",
            explanation,
            json.dumps(hints),
            json.dumps([p.dict() for p in practice_list]),
            f"根据掌握度{request.master_level:.2f}，选择{teaching_mode}教学模式",
            request.master_level,
            datetime.now().isoformat()
        ))
        conn.commit()
    
    return TeachingGenerateResponse(
        explanation=explanation,
        hints=hints,
        practice_list=practice_list,
        reasoning_content=f"基于知识点'{request.knowledge_scope}'和掌握度{request.master_level:.2f}，生成{teaching_mode}模式的教学内容。错因：{[tag.level3 for tag in request.error_tags]}",
        teaching_mode=teaching_mode
    )

@app.post("/internal/api/v1/teaching/frequency-check", response_model=FrequencyCheckResponse)
def check_frequency(request: FrequencyCheckRequest):
    daily_limit = 5
    weekly_limit = 3
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT daily_push_count, weekly_push_count, last_reset_date
            FROM frequency_limit
            WHERE student_id = ? AND knowledge_id = ?
        ''', (request.student_id, request.knowledge_id))
        row = cursor.fetchone()
        
        if row:
            daily_push_count = row["daily_push_count"]
            weekly_push_count = row["weekly_push_count"]
            last_reset_date = row["last_reset_date"]
            
            today = datetime.now().date()
            if last_reset_date != str(today):
                daily_push_count = 0
                cursor.execute('''
                    UPDATE frequency_limit
                    SET daily_push_count = 0, last_reset_date = ?
                    WHERE student_id = ? AND knowledge_id = ?
                ''', (str(today), request.student_id, request.knowledge_id))
                conn.commit()
        else:
            daily_push_count = 0
            weekly_push_count = 0
            cursor.execute('''
                INSERT INTO frequency_limit (
                    frequency_limit_id, student_id, knowledge_id,
                    daily_push_count, weekly_push_count, last_reset_date
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (generate_id("FL"), request.student_id, request.knowledge_id, 0, 0, str(datetime.now().date())))
            conn.commit()
    
    push_permission = daily_push_count < daily_limit and weekly_push_count < weekly_limit
    
    return FrequencyCheckResponse(
        push_permission=push_permission,
        daily_push_count=daily_push_count,
        daily_limit=daily_limit,
        weekly_push_count=weekly_push_count,
        weekly_limit=weekly_limit,
        remaining_daily=daily_limit - daily_push_count,
        remaining_weekly=weekly_limit - weekly_push_count
    )

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Teaching Service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)