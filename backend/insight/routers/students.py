"""学生/班级查询路由（SQLite 版，替代缺失的 Neo4j 路由）。"""

import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException

_DB_PATH = Path(__file__).resolve().parents[3] / "backend" / "database" / "example_db.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


router = APIRouter(prefix="/api/students", tags=["students"])


@router.get("")
def list_students():
    with _conn() as conn:
        rows = conn.execute(
            "SELECT student_id, student_name, student_class, student_grade FROM students ORDER BY student_id"
        ).fetchall()
    return {"data": [dict(r) for r in rows]}


@router.get("/classes")
def list_classes():
    with _conn() as conn:
        rows = conn.execute(
            "SELECT student_class, COUNT(*) as count FROM students GROUP BY student_class ORDER BY student_class"
        ).fetchall()
    return {"data": [{"class_name": r["student_class"], "count": r["count"]} for r in rows]}


@router.get("/class/{class_name}/mastery")
def get_class_mastery(class_name: str):
    """班级知识点掌握度聚合（按知识点的平均掌握度）"""
    with _conn() as conn:
        rows = conn.execute(
            """SELECT km.knowledge_id, k.knowledge_name, k.knowledge_scope,
                      ROUND(AVG(km.master_level), 4) as avg_mastery,
                      COUNT(DISTINCT km.student_id) as student_count
               FROM knowledge_mastery km
               JOIN students s ON km.student_id = s.student_id
               LEFT JOIN knowledge k ON km.knowledge_id = k.knowledge_id
               WHERE s.student_class = ?
               GROUP BY km.knowledge_id
               ORDER BY avg_mastery ASC""",
            (class_name,),
        ).fetchall()
    return {"class_name": class_name, "data": [dict(r) for r in rows]}


@router.get("/class/{class_name}")
def get_class_students(class_name: str):
    with _conn() as conn:
        rows = conn.execute(
            """SELECT student_id, student_name, student_class, student_grade
               FROM students WHERE student_class = ? ORDER BY student_id""",
            (class_name,),
        ).fetchall()
    return {"class_name": class_name, "data": [dict(r) for r in rows]}


@router.get("/{student_id}")
def get_student(student_id: str):
    with _conn() as conn:
        row = conn.execute(
            """SELECT student_id, student_name, student_class, student_grade
               FROM students WHERE student_id = ?""",
            (student_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="学生不存在")
        mastery = conn.execute(
            """SELECT km.knowledge_id, k.knowledge_name, km.master_level, km.mastery_status
               FROM knowledge_mastery km
               LEFT JOIN knowledge k ON km.knowledge_id = k.knowledge_id
               WHERE km.student_id = ?""",
            (student_id,),
        ).fetchall()
    result = dict(row)
    result["mastery"] = [dict(r) for r in mastery]
    return result
