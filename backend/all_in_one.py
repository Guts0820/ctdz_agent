import json
import base64
import io
import requests
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
import sqlite3
import sys
sys.path.insert(0, 'backend/services')
from mastery_utils import calculate_mastery
from id_utils import generate_id

USE_REAL_OCR = False

app = FastAPI(title="AI Math Error Correction System - All in One", version="1.0.0")

DATABASE = "backend/database/example_db.db"
KG_SERVICE_URL = "http://localhost:8007"

if USE_REAL_OCR:
    try:
        from paddleocr import PaddleOCR
        ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
        
        def perform_ocr(image_data: bytes) -> dict:
            try:
                result = ocr.ocr(image_data, cls=True)
                lines = []
                for line in result[0]:
                    text = line[1][0].strip()
                    confidence = line[1][1]
                    if text:
                        lines.append({"text": text, "confidence": confidence})
                
                full_text = "\n".join([line["text"] for line in lines])
                avg_confidence = sum(line["confidence"] for line in lines) / len(lines) if lines else 0.0
                
                return {
                    "success": True,
                    "text": full_text,
                    "lines": lines,
                    "confidence": avg_confidence,
                    "status": "normal" if avg_confidence > 0.5 else "low_confidence"
                }
            except Exception as e:
                return {
                    "success": False,
                    "text": "",
                    "lines": [],
                    "confidence": 0.0,
                    "status": "ocr_failed",
                    "error": str(e)
                }
    except Exception as e:
        USE_REAL_OCR = False

if not USE_REAL_OCR:
    def perform_ocr(image_data: bytes) -> dict:
        sample_texts = [
            "小明有25颗糖果，小红有38颗糖果，他们一共有多少颗糖果？\n25+38=63",
            "计算：35+27=\n35+27=52",
            "一本书有120页，小明已经看了45页，还剩多少页没看？\n120-45=85",
            "一个长方形长8厘米，宽5厘米，周长是多少？\n(8+5)x2=26厘米"
        ]
        import random
        selected_text = random.choice(sample_texts)
        
        return {
            "success": True,
            "text": selected_text,
            "lines": [{"text": line, "confidence": 0.95} for line in selected_text.split("\n")],
            "confidence": 0.95,
            "status": "normal",
            "ocr_mode": "simulated"
        }

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

ERROR_TAG_BANK = {
    "C-001": {"level1": "计算", "level2": "口算与基本运算", "level3": "进位加法中十位漏加进位1"},
    "C-002": {"level1": "计算", "level2": "口算与基本运算", "level3": "退位减法中十位漏减退位1"},
    "C-004": {"level1": "计算", "level2": "口算与基本运算", "level3": "20以内加减法不熟练"},
    "K-001": {"level1": "概念", "level2": "定义混淆", "level3": "概念理解错误"},
    "R-001": {"level1": "审题", "level2": "遗漏条件", "level3": "审题不仔细"},
    "M-001": {"level1": "粗心", "level2": "抄错数字", "level3": "粗心错误"}
}

def fetch_knowledge_from_graph(knowledge_id: str) -> dict:
    try:
        response = requests.get(f"{KG_SERVICE_URL}/api/knowledge_points/{knowledge_id}", timeout=5)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None

TEACHING_TEMPLATES = {
    "K035": {
        "basic": {"explain": "我们来学习两位数加两位数的进位加法。当两个数相加时，个位上的数字加起来如果等于或超过10，就要向十位进1。比如25+38，个位5+8=13，我们在个位写3，然后向十位进1，十位上2+3再加上进位的1等于6，所以结果是63。", "hints": ["先算个位，5+8等于多少？", "个位满十了吗？满十要怎么办？", "十位上的2+3还要加什么？"], "practice": [{"q": "18+25=？", "a": "43"}, {"q": "36+17=？", "a": "53"}]},
        "standard": {"explain": "两位数加两位数进位加法的计算方法：1. 相同数位对齐；2. 从个位加起；3. 个位相加满十，向十位进1；4. 十位相加时要记得加上进位的1。", "hints": ["检查一下个位相加是否满十", "十位相加时有没有忘记加进位"], "practice": [{"q": "45+28=？", "a": "73"}, {"q": "56+37=？", "a": "93"}]},
        "advanced": {"explain": "你已经掌握了进位加法的基本方法，继续加油！记住进位标记很重要哦。", "hints": ["你能说说进位加法的关键步骤吗？"], "practice": []}
    },
    "default": {
        "basic": {"explain": "我们来复习这个知识点。仔细看题目，按照正确的方法一步步计算。", "hints": ["第一步应该做什么？", "这里需要注意什么？"], "practice": [{"q": "练习题1", "a": "答案1"}]},
        "standard": {"explain": "这个知识点的关键是理解计算方法，按照步骤来做。", "hints": ["检查一下计算步骤"], "practice": [{"q": "变式题1", "a": "答案1"}]},
        "advanced": {"explain": "你已经基本掌握了这个知识点，继续巩固！", "hints": ["你能说说这个知识点的关键吗？"], "practice": []}
    }
}

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

@app.post("/api/v1/submit", response_model=SubmitResponse)
def submit_homework(request: SubmitRequest):
    try:
        analysis_result = process_analysis(request)
        
        if analysis_result["is_copy"]:
            return SubmitResponse(
                status="success",
                data={
                    "judge_result": analysis_result["judge_result"],
                    "is_copy": True,
                    "hints": ["你是怎么想到这个答案的？", "能说说你的计算过程吗？"],
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
            
            state_result = update_state(request.student_id, knowledge_id, True, analysis_result["confidence"])
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
        
        error_analysis_result = analyze_error(analysis_result)
        
        if not knowledge_id:
            knowledge_id = error_analysis_result.get("knowledge_id", "K252")
        
        knowledge_result = retrieve_knowledge(knowledge_id)
        
        frequency_result = check_frequency(request.student_id, knowledge_id)
        
        if not frequency_result["push_permission"]:
            state_result = update_state(request.student_id, knowledge_id, False, error_analysis_result["total_confidence"])
            
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
        
        state_before = update_state(request.student_id, knowledge_id, False, error_analysis_result["total_confidence"])
        
        teaching_result = generate_teaching(error_analysis_result, state_before["master_level"], analysis_result)
        
        if state_before["should_generate_review"]:
            review_result = generate_review(request.student_id, knowledge_id, state_before["knowledge_mastery_id"], state_before["master_level"])
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
                "ocr_text": analysis_result.get("ocr_text", ""),
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

def process_analysis(request: SubmitRequest) -> dict:
    question = request.original_question or ""
    answer = request.student_write or ""
    student_id = request.student_id
    question_id = request.question_id
    
    if request.image:
        try:
            if request.image.startswith("data:image"):
                image_data = base64.b64decode(request.image.split(",")[1])
            else:
                image_data = base64.b64decode(request.image)
            
            ocr_result = perform_ocr(image_data)
            
            if not ocr_result["success"]:
                return {
                    "judge_result": "unknown",
                    "step_feedback": f"OCR识别失败: {ocr_result['error']}",
                    "error_step_list": [],
                    "miss_step_list": ["OCR识别失败"],
                    "is_copy": False,
                    "core_error_type": "OCR失败",
                    "confidence": 0.0,
                    "original_question": "",
                    "student_write": "",
                    "ocr_text": "",
                    "student_id": student_id,
                    "question_id": question_id
                }
            
            ocr_text = ocr_result["text"]
            
            if not question:
                question = ocr_text
            
            if not answer:
                answer = ocr_text
            
            if ocr_result["status"] == "low_confidence":
                return {
                    "judge_result": "unknown",
                    "step_feedback": f"OCR识别置信度较低({ocr_result['confidence']:.2f})，请检查图片清晰度",
                    "error_step_list": [],
                    "miss_step_list": ["OCR识别置信度低"],
                    "is_copy": False,
                    "core_error_type": "OCR置信度低",
                    "confidence": ocr_result["confidence"],
                    "original_question": question,
                    "student_write": answer,
                    "ocr_text": ocr_text,
                    "student_id": student_id,
                    "question_id": question_id
                }
        except Exception as e:
            return {
                "judge_result": "unknown",
                "step_feedback": f"图片解码失败: {str(e)}",
                "error_step_list": [],
                "miss_step_list": ["图片解码失败"],
                "is_copy": False,
                "core_error_type": "图片处理失败",
                "confidence": 0.0,
                "original_question": question,
                "student_write": answer,
                "ocr_text": "",
                "student_id": student_id,
                "question_id": question_id
            }
    
    if not question:
        question = "小明有25颗糖果，小红有38颗糖果，他们一共有多少颗糖果？"
    
    if not answer:
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
            "student_id": student_id,
            "question_id": question_id
        }
    
    is_copy = "63" in answer and len(answer) <= 10 and "+" not in answer
    
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
            "student_id": student_id,
            "question_id": question_id
        }
    
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
                "student_id": student_id,
                "question_id": question_id
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
                "student_id": student_id,
                "question_id": question_id
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
                "student_id": student_id,
                "question_id": question_id
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
        "student_id": student_id,
        "question_id": question_id
    }

def analyze_error(analysis_result: dict) -> dict:
    if analysis_result["judge_result"] == "correct":
        return {"error_tags": [], "knowledge_id": "", "knowledge_scope": "", "reasoning_content": "答案正确", "total_confidence": 1.0}
    
    core_type = analysis_result["core_error_type"]
    question = analysis_result["original_question"]
    
    error_tags = []
    
    if "计算" in core_type:
        if "进位" in analysis_result["step_feedback"]:
            error_tags.append({"error_id": "C-001", **ERROR_TAG_BANK["C-001"], "confidence": 0.92})
        elif "退位" in analysis_result["step_feedback"]:
            error_tags.append({"error_id": "C-002", **ERROR_TAG_BANK["C-002"], "confidence": 0.90})
        else:
            error_tags.append({"error_id": "C-004", **ERROR_TAG_BANK["C-004"], "confidence": 0.85})
    elif "概念" in core_type:
        error_tags.append({"error_id": "K-001", **ERROR_TAG_BANK["K-001"], "confidence": 0.88})
    elif "审题" in core_type:
        error_tags.append({"error_id": "R-001", **ERROR_TAG_BANK["R-001"], "confidence": 0.87})
    else:
        error_tags.append({"error_id": "M-001", **ERROR_TAG_BANK["M-001"], "confidence": 0.85})
    
    if "加" in question:
        knowledge_id = "K035"
    elif "减" in question:
        knowledge_id = "K037"
    elif "乘" in question:
        knowledge_id = "K082"
    elif "周长" in question:
        knowledge_id = "K087"
    elif "面积" in question:
        knowledge_id = "K105"
    else:
        knowledge_id = "K252"
    
    total_confidence = sum(tag["confidence"] for tag in error_tags) / len(error_tags) if error_tags else 0.0
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        question_id = analysis_result.get("question_id")
        if not question_id and analysis_result.get("original_question"):
            cursor.execute('''
                SELECT question_id FROM question WHERE question_description = ?
            ''', (analysis_result["original_question"],))
            row = cursor.fetchone()
            if row:
                question_id = row["question_id"]
        
        mistake_case_id = generate_id("MC")
        cursor.execute('INSERT INTO mistake_case (mistake_case_id, student_id, question_id, current_status, created_at) VALUES (?, ?, ?, ?, ?)', (mistake_case_id, analysis_result.get("student_id", ""), question_id, "correcting", datetime.now().isoformat()))
        
        for tag in error_tags:
            cursor.execute('INSERT INTO mistake_case_error (mistake_case_id, error_id, error_weight) VALUES (?, ?, ?)', (mistake_case_id, tag["error_id"], tag["confidence"]))
        
        cursor.execute('INSERT INTO mistake_case_knowledge (mistake_case_id, knowledge_id, knowledge_weight) VALUES (?, ?, ?)', (mistake_case_id, knowledge_id, 1.0))
        conn.commit()
    
    knowledge_data = fetch_knowledge_from_graph(knowledge_id)
    knowledge_scope = knowledge_data.get("title", "") if knowledge_data else ""
    
    return {
        "error_tags": error_tags,
        "knowledge_id": knowledge_id,
        "knowledge_scope": knowledge_scope,
        "reasoning_content": f"根据学生作答分析得出错因：{[tag['level3'] for tag in error_tags]}",
        "total_confidence": total_confidence
    }

def retrieve_knowledge(knowledge_id: str) -> dict:
    knowledge = fetch_knowledge_from_graph(knowledge_id)
    if not knowledge:
        raise HTTPException(status_code=404, detail=f"知识点 {knowledge_id} 不存在")
    
    return {
        "knowledge_explanation": knowledge.get("content", ""),
        "difficulty": knowledge.get("difficulty", "medium"),
        "standard_solution": ""
    }

def generate_teaching(error_analysis_result: dict, master_level: float, analysis_result: dict) -> dict:
    knowledge_id = error_analysis_result["knowledge_id"]
    template = TEACHING_TEMPLATES.get(knowledge_id, TEACHING_TEMPLATES["default"])
    
    if master_level < 0.4:
        mode = "BASIC"
        content = template["basic"]
    elif 0.4 <= master_level <= 0.8:
        mode = "STANDARD"
        content = template["standard"]
    else:
        mode = "ADVANCED"
        content = template["advanced"]
    
    practice_list = [{"question_id": generate_id("Q"), "question_description": p["q"], "answer": p["a"]} for p in content["practice"]]
    
    return {
        "explanation": content["explain"],
        "hints": content["hints"],
        "practice_list": practice_list,
        "teaching_mode": mode
    }

def update_state(student_id: str, knowledge_id: str, is_correct: bool, confidence: float) -> dict:
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT knowledge_mastery_id, correct_count, wrong_count FROM knowledge_mastery WHERE student_id = ? AND knowledge_id = ?', (student_id, knowledge_id))
        row = cursor.fetchone()
        
        if row:
            km_id = row["knowledge_mastery_id"]
            correct_count = row["correct_count"]
            wrong_count = row["wrong_count"]
        else:
            km_id = generate_id("KM")
            correct_count = 0
            wrong_count = 0
            cursor.execute('INSERT INTO knowledge_mastery (knowledge_mastery_id, student_id, knowledge_id, mastery_status, correct_count, wrong_count, master_level) VALUES (?, ?, ?, ?, ?, ?, ?)', (km_id, student_id, knowledge_id, "pending", 0, 0, 0.0))
        
        if is_correct:
            correct_count += 1
            wrong_count = 0
        else:
            wrong_count += 1
            correct_count = 0
        
        master_level, mastery_status = calculate_mastery(correct_count, wrong_count)
        
        if master_level < 0.4:
            next_action = "basic_practice"
        elif 0.4 <= master_level <= 0.8:
            next_action = "practice"
        else:
            next_action = "guide"
        
        should_generate_review = mastery_status == "pending" and (correct_count >= 1 or wrong_count >= 1)
        
        cursor.execute('UPDATE knowledge_mastery SET correct_count = ?, wrong_count = ?, master_level = ?, mastery_status = ?, updated_at = ? WHERE knowledge_mastery_id = ?', (correct_count, wrong_count, master_level, mastery_status, datetime.now().isoformat(), km_id))
        conn.commit()
    
    return {
        "master_level": master_level,
        "next_action": next_action,
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "mastery_status": mastery_status,
        "knowledge_mastery_id": km_id,
        "should_generate_review": should_generate_review
    }

def check_frequency(student_id: str, knowledge_id: str) -> dict:
    daily_limit = 5
    weekly_limit = 3
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT daily_push_count, weekly_push_count, last_reset_date FROM frequency_limit WHERE student_id = ? AND knowledge_id = ?', (student_id, knowledge_id))
        row = cursor.fetchone()
        
        if row:
            daily_count = row["daily_push_count"]
            weekly_count = row["weekly_push_count"]
            last_reset = row["last_reset_date"]
            
            today = datetime.now().date()
            if last_reset != str(today):
                daily_count = 0
                cursor.execute('UPDATE frequency_limit SET daily_push_count = 0, last_reset_date = ? WHERE student_id = ? AND knowledge_id = ?', (str(today), student_id, knowledge_id))
                conn.commit()
        else:
            daily_count = 0
            weekly_count = 0
            cursor.execute('INSERT INTO frequency_limit (frequency_limit_id, student_id, knowledge_id, daily_push_count, weekly_push_count, last_reset_date) VALUES (?, ?, ?, ?, ?, ?)', (generate_id("FL"), student_id, knowledge_id, 0, 0, str(datetime.now().date())))
            conn.commit()
    
    return {
        "push_permission": daily_count < daily_limit and weekly_count < weekly_limit,
        "daily_push_count": daily_count,
        "daily_limit": daily_limit,
        "weekly_push_count": weekly_count,
        "weekly_limit": weekly_limit,
        "remaining_daily": daily_limit - daily_count,
        "remaining_weekly": weekly_limit - weekly_count
    }

def generate_review(student_id: str, knowledge_id: str, knowledge_mastery_id: str, master_level: float) -> dict:
    review_plan_id = generate_id("RP")
    
    today = datetime.now().date()
    stage_dates = {
        "Day1": str(today + timedelta(days=1)),
        "Day3": str(today + timedelta(days=3)),
        "Day7": str(today + timedelta(days=7))
    }
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        for stage in ["Day1", "Day3", "Day7"]:
            cursor.execute('INSERT INTO review_plan (review_plan_id, knowledge_mastery_id, review_stage, status, created_at) VALUES (?, ?, ?, ?, ?)', (review_plan_id, knowledge_mastery_id, stage, "pending", datetime.now().isoformat()))
            
            push_record_id = generate_id("PR")
            cursor.execute('INSERT INTO push_record (push_record_id, review_plan_id, push_date, push_stage, status) VALUES (?, ?, ?, ?, ?)', (push_record_id, review_plan_id, stage_dates[stage], stage.lower(), "pending"))
        
        conn.commit()
    
    return {
        "review_plan_id": review_plan_id,
        "review_stages": ["Day1", "Day3", "Day7"],
        "stage_dates": stage_dates,
        "status": "generated"
    }

@app.get("/api/v1/student/{student_id}/mastery")
def get_student_mastery(student_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT km.*, k.knowledge_scope FROM knowledge_mastery km LEFT JOIN knowledge k ON km.knowledge_id = k.knowledge_id WHERE km.student_id = ?', (student_id,))
        rows = [dict(row) for row in cursor.fetchall()]
    
    return {"status": "success", "data": rows}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/v1/submit/image")
async def submit_image(
    student_id: str,
    image: UploadFile = File(...),
    grade: str = "三年级"
):
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "tiff"}
    MAX_SIZE = 5 * 1024 * 1024
    
    filename = image.filename.lower()
    if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HTTPException(status_code=400, detail="不支持的图片格式，请上传jpg/jpeg/png/bmp格式")
    
    image_data = await image.read()
    if len(image_data) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="图片大小超过限制（最大5MB）")
    
    ocr_result = perform_ocr(image_data)
    
    if not ocr_result["success"]:
        return SubmitResponse(
            status="error",
            data={
                "judge_result": "unknown",
                "step_feedback": f"OCR识别失败: {ocr_result['error']}",
                "is_copy": False,
                "next_action": "ocr_failed"
            }
        )
    
    request = SubmitRequest(
        student_id=student_id,
        image=base64.b64encode(image_data).decode("utf-8"),
        original_question="",
        student_write="",
        grade=grade
    )
    
    return submit_homework(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)