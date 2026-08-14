"""知识点查询路由（SQLite 版）。"""

import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

_DB_PATH = Path(__file__).resolve().parents[3] / "backend" / "database" / "example_db.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


router = APIRouter(prefix="/api/knowledge_points", tags=["knowledge_points"])


@router.get("")
def list_knowledge_points(grade: Optional[str] = Query(None)):
    sql = (
        "SELECT knowledge_id, knowledge_name, knowledge_scope, grade, unit, "
        "difficulty, is_core FROM knowledge"
    )
    params = []
    if grade:
        grade_map = {
            "一年级": "1", "二年级": "2", "三年级": "3",
            "四年级": "4", "五年级": "5", "六年级": "6",
        }
        grade = grade_map.get(grade, grade)
        sql += " WHERE grade = ?"
        params.append(grade)
    sql += " ORDER BY knowledge_id"
    with _conn() as conn:
        rows = conn.execute(sql, params).fetchall()
    return {"total": len(rows), "data": [dict(r) for r in rows]}


@router.get("/{knowledge_id}")
def get_knowledge_point(knowledge_id: str):
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM knowledge WHERE knowledge_id = ?", (knowledge_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="知识点不存在")
    return dict(row)
