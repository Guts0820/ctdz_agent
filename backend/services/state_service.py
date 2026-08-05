import json
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

from backend.config import DATABASE_PATH
from backend.services.observability import log_event, timed
from mastery_utils import calculate_mastery, calculate_advanced, load_evidence
from id_utils import generate_id

app = FastAPI(title="State Service", version="1.0.0")

DATABASE = DATABASE_PATH


class StateUpdateRequest(BaseModel):
    student_id: str
    knowledge_id: str
    is_correct: bool
    confidence: float
    mistake_case_id: Optional[str] = None
    answer_history_id: Optional[str] = None


class StateUpdateResponse(BaseModel):
    master_level: float
    next_action: str
    correct_count: int
    wrong_count: int
    mastery_status: str
    knowledge_mastery_id: str
    should_generate_review: bool
    priority: float = 0.0
    formula: str = "advanced-v1"


class ReviewGenerateRequest(BaseModel):
    student_id: str
    knowledge_id: str
    knowledge_mastery_id: str
    master_level: float


class ReviewGenerateResponse(BaseModel):
    review_plan_id: str
    review_stages: list
    stage_dates: dict
    status: str
    push_records: list


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.post("/internal/api/v1/state/update", response_model=StateUpdateResponse)
@timed("state.update")
def update_state(request: StateUpdateRequest):
    log_event("state.request", student_id=request.student_id, knowledge_id=request.knowledge_id, is_correct=request.is_correct)
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT knowledge_mastery_id, correct_count, wrong_count, mastery_status
            FROM knowledge_mastery
            WHERE student_id = ? AND knowledge_id = ?
        ''', (request.student_id, request.knowledge_id))
        row = cursor.fetchone()

        if row:
            knowledge_mastery_id = row["knowledge_mastery_id"]
            correct_count = row["correct_count"]
            wrong_count = row["wrong_count"]
        else:
            knowledge_mastery_id = generate_id("KM")
            correct_count = 0
            wrong_count = 0
            cursor.execute('''
                INSERT INTO knowledge_mastery (
                    knowledge_mastery_id, student_id, knowledge_id,
                    mastery_status, correct_count, wrong_count, master_level
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (knowledge_mastery_id, request.student_id, request.knowledge_id, "pending", 0, 0, 0.0))

        if request.is_correct:
            correct_count += 1
            wrong_count = 0
        else:
            wrong_count += 1
            correct_count = 0

        # 尝试高级算法：从 answer_history 加载证据
        evidence = load_evidence(request.student_id, request.knowledge_id, DATABASE)
        if len(evidence) >= 2:
            result = calculate_advanced(
                student_id=int(request.student_id.replace("S-", "").replace("-", "0") or "0"),
                knowledge_point_id=request.knowledge_id,
                evidence=evidence,
            )
            master_level = result["mastery"]
            mastery_status = result["mastery_status"]
            priority = result["priority"]
        else:
            # 数据不足时回退简单算法
            master_level, mastery_status = calculate_mastery(correct_count, wrong_count)
            priority = 0.0

        next_action = determine_next_action(mastery_status, master_level)
        should_generate_review = mastery_status == "pending" and (correct_count >= 1 or wrong_count >= 1)

        cursor.execute('''
            UPDATE knowledge_mastery
            SET correct_count = ?, wrong_count = ?, master_level = ?,
                mastery_status = ?, updated_at = ?
            WHERE knowledge_mastery_id = ?
        ''', (correct_count, wrong_count, master_level, mastery_status,
              datetime.now().isoformat(), knowledge_mastery_id))

        conn.commit()

    return StateUpdateResponse(
        master_level=master_level,
        next_action=next_action,
        correct_count=correct_count,
        wrong_count=wrong_count,
        mastery_status=mastery_status,
        knowledge_mastery_id=knowledge_mastery_id,
        should_generate_review=should_generate_review,
        priority=priority,
    )


def determine_next_action(mastery_status: str, master_level: float) -> str:
    if mastery_status == "mastered":
        return "complete"
    elif mastery_status == "weak":
        return "teacher_intervention"
    elif master_level < 0.4:
        return "basic_practice"
    elif 0.4 <= master_level <= 0.8:
        return "practice"
    else:
        return "guide"


@app.post("/internal/api/v1/state/generate-review", response_model=ReviewGenerateResponse)
def generate_review(request: ReviewGenerateRequest):
    today = datetime.now().date()
    stage_dates = {
        "Day1": str(today + timedelta(days=1)),
        "Day3": str(today + timedelta(days=3)),
        "Day7": str(today + timedelta(days=7))
    }

    push_records = []

    with get_db() as conn:
        cursor = conn.cursor()

        for stage in ["Day1", "Day3", "Day7"]:
            stage_plan_id = generate_id("RP")
            cursor.execute('''
                INSERT INTO review_plan (
                    review_plan_id, knowledge_mastery_id, review_stage, status, created_at
                ) VALUES (?, ?, ?, ?, ?)
            ''', (stage_plan_id, request.knowledge_mastery_id, stage, "pending",
                  datetime.now().isoformat()))

            push_record_id = generate_id("PR")
            cursor.execute('''
                INSERT INTO push_record (
                    push_record_id, review_plan_id, push_date, push_stage, status
                ) VALUES (?, ?, ?, ?, ?)
            ''', (push_record_id, stage_plan_id, stage_dates[stage], stage.lower(), "pending"))

            push_records.append({
                "push_record_id": push_record_id,
                "stage": stage,
                "status": "pending"
            })

        conn.commit()

    return ReviewGenerateResponse(
        review_plan_id=push_records[0]["push_record_id"] if push_records else "",
        review_stages=["Day1", "Day3", "Day7"],
        stage_dates=stage_dates,
        status="generated",
        push_records=push_records
    )


@app.get("/internal/api/v1/state/mastery/{student_id}")
def get_mastery(student_id: str, knowledge_id: Optional[str] = None):
    with get_db() as conn:
        cursor = conn.cursor()

        if knowledge_id:
            cursor.execute('''
                SELECT km.*, k.knowledge_scope
                FROM knowledge_mastery km
                LEFT JOIN knowledge k ON km.knowledge_id = k.knowledge_id
                WHERE km.student_id = ? AND km.knowledge_id = ?
            ''', (student_id, knowledge_id))
            rows = [dict(row) for row in cursor.fetchall()]
        else:
            cursor.execute('''
                SELECT km.*, k.knowledge_scope
                FROM knowledge_mastery km
                LEFT JOIN knowledge k ON km.knowledge_id = k.knowledge_id
                WHERE km.student_id = ?
            ''', (student_id,))
            rows = [dict(row) for row in cursor.fetchall()]

        # 对每条记录用高级算法重算掌握度
        for row_dict in rows:
            evidence = load_evidence(
                row_dict["student_id"], row_dict["knowledge_id"], DATABASE
            )
            if len(evidence) >= 2:
                result = calculate_advanced(
                    student_id=0,
                    knowledge_point_id=row_dict["knowledge_id"],
                    evidence=evidence,
                )
                row_dict["master_level"] = result["mastery"]
                row_dict["mastery_status"] = result["mastery_status"]
                row_dict["priority"] = result["priority"]
                row_dict["_formula"] = "advanced-v1"

        return {"status": "success", "data": rows}


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "State Service", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8085)
