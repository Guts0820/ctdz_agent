import json
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import time
from mastery_utils import calculate_mastery
from id_utils import generate_id

app = FastAPI(title="Review Scheduler", version="1.0.0")

DATABASE = "backend/database/example_db.db"

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

class ReviewTask(BaseModel):
    review_plan_id: str
    student_id: str
    knowledge_id: str
    knowledge_scope: str
    review_stage: str
    push_date: str
    status: str

@app.get("/internal/api/v1/review/scheduler/run")
def run_scheduler():
    today = datetime.now().date()
    tasks = []
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pr.*, rp.knowledge_mastery_id, km.student_id, km.knowledge_id,
                   k.knowledge_scope
            FROM push_record pr
            JOIN review_plan rp ON pr.review_plan_id = rp.review_plan_id
            JOIN knowledge_mastery km ON rp.knowledge_mastery_id = km.knowledge_mastery_id
            JOIN knowledge k ON km.knowledge_id = k.knowledge_id
            WHERE pr.status = 'pending' AND pr.push_date = ?
        ''', (str(today),))
        
        rows = cursor.fetchall()
        
        for row in rows:
            task = {
                "push_record_id": row["push_record_id"],
                "review_plan_id": row["review_plan_id"],
                "student_id": row["student_id"],
                "knowledge_id": row["knowledge_id"],
                "knowledge_scope": row["knowledge_scope"],
                "review_stage": row["push_stage"],
                "push_date": row["push_date"],
                "status": row["status"]
            }
            
            cursor.execute('''
                UPDATE push_record
                SET status = 'pushing'
                WHERE push_record_id = ?
            ''', (row["push_record_id"],))
            
            tasks.append(task)
        
        conn.commit()
    
    if tasks:
        return {
            "status": "success",
            "message": f"Found {len(tasks)} tasks to push",
            "tasks": tasks,
            "pushed_at": datetime.now().isoformat()
        }
    else:
        return {
            "status": "success",
            "message": "No tasks to push today",
            "tasks": [],
            "pushed_at": datetime.now().isoformat()
        }

@app.get("/internal/api/v1/review/scheduler/today")
def get_today_tasks():
    today = datetime.now().date()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pr.*, rp.knowledge_mastery_id, km.student_id, km.knowledge_id,
                   k.knowledge_scope, km.mastery_status
            FROM push_record pr
            JOIN review_plan rp ON pr.review_plan_id = rp.review_plan_id
            JOIN knowledge_mastery km ON rp.knowledge_mastery_id = km.knowledge_mastery_id
            JOIN knowledge k ON km.knowledge_id = k.knowledge_id
            WHERE pr.push_date = ?
            ORDER BY pr.push_stage
        ''', (str(today),))
        
        rows = [dict(row) for row in cursor.fetchall()]
    
    return {
        "status": "success",
        "date": str(today),
        "total_tasks": len(rows),
        "tasks": rows
    }

@app.get("/internal/api/v1/review/scheduler/student/{student_id}")
def get_student_review_tasks(student_id: str):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pr.*, rp.review_stage, rp.status as plan_status,
                   k.knowledge_scope, km.mastery_status
            FROM push_record pr
            JOIN review_plan rp ON pr.review_plan_id = rp.review_plan_id
            JOIN knowledge_mastery km ON rp.knowledge_mastery_id = km.knowledge_mastery_id
            JOIN knowledge k ON km.knowledge_id = k.knowledge_id
            WHERE km.student_id = ?
            ORDER BY pr.push_date
        ''', (student_id,))
        
        rows = [dict(row) for row in cursor.fetchall()]
    
    return {
        "status": "success",
        "student_id": student_id,
        "total_tasks": len(rows),
        "tasks": rows
    }

@app.post("/internal/api/v1/review/scheduler/complete/{push_record_id}")
def complete_review_task(push_record_id: str, is_correct: bool):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT pr.*, rp.knowledge_mastery_id, km.student_id, km.knowledge_id,
                   km.correct_count, km.wrong_count
            FROM push_record pr
            JOIN review_plan rp ON pr.review_plan_id = rp.review_plan_id
            JOIN knowledge_mastery km ON rp.knowledge_mastery_id = km.knowledge_mastery_id
            WHERE pr.push_record_id = ?
        ''', (push_record_id,))
        
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Push record not found")
        
        correct_count = row["correct_count"]
        wrong_count = row["wrong_count"]
        
        if is_correct:
            correct_count += 1
            wrong_count = 0
        else:
            wrong_count += 1
            correct_count = 0
        
        master_level, mastery_status = calculate_mastery(correct_count, wrong_count)
        
        cursor.execute('''
            UPDATE knowledge_mastery
            SET correct_count = ?, wrong_count = ?, master_level = ?, mastery_status = ?,
                updated_at = ?
            WHERE knowledge_mastery_id = ?
        ''', (correct_count, wrong_count, master_level, mastery_status, datetime.now().isoformat(), row["knowledge_mastery_id"]))
        
        cursor.execute('''
            UPDATE push_record
            SET status = 'completed'
            WHERE push_record_id = ?
        ''', (push_record_id,))
        
        if mastery_status == "mastered":
            cursor.execute('''
                UPDATE review_plan
                SET status = 'completed', completed_at = ?
                WHERE review_plan_id = ?
            ''', (datetime.now().isoformat(), row["review_plan_id"]))
            
            cursor.execute('''
                UPDATE push_record
                SET status = 'completed'
                WHERE review_plan_id = ?
            ''', (row["review_plan_id"],))
        
        elif mastery_status == "weak":
            cursor.execute('''
                UPDATE review_plan
                SET status = 'cancelled', completed_at = ?
                WHERE review_plan_id = ?
            ''', (datetime.now().isoformat(), row["review_plan_id"]))
        
        conn.commit()
    
    return {
        "status": "success",
        "push_record_id": push_record_id,
        "is_correct": is_correct,
        "mastery_status": mastery_status,
        "master_level": master_level,
        "correct_count": correct_count,
        "wrong_count": wrong_count
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Review Scheduler"}

def start_scheduler():
    while True:
        try:
            run_scheduler()
        except Exception as e:
            print(f"Scheduler error: {e}")
        time.sleep(3600)

if __name__ == "__main__":
    import threading
    import uvicorn
    
    scheduler_thread = threading.Thread(target=start_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()
    
    uvicorn.run(app, host="0.0.0.0", port=8086)