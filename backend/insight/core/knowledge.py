"""主业务库（example_db.db）的通用查询助手。"""

import sqlite3

from backend.config import DATABASE_PATH


def _get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def knowledge_title(knowledge_id: str) -> str:
    if not knowledge_id:
        return ""
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT knowledge_scope FROM knowledge WHERE knowledge_id = ?",
            (knowledge_id,),
        ).fetchone()
        return row["knowledge_scope"] if row else ""
    finally:
        conn.close()


def questions_for_knowledge(knowledge_id: str, difficulty: int = 0, limit: int = 10) -> list[dict]:
    conn = _get_db()
    try:
        sql = """
            SELECT q.question_id, q.question_description, q.difficulty, q.answer
            FROM question q
            JOIN question_knowledge_mapping qkm ON q.question_id = qkm.question_id
            WHERE qkm.knowledge_id = ?
        """
        params: list = [knowledge_id]
        if difficulty > 0:
            sql += " AND q.difficulty = ?"
            params.append("easy" if difficulty <= 1 else "medium" if difficulty <= 2 else "hard")
        sql += " LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def mistake_cases_for_knowledge(knowledge_id: str, student_id: str = "") -> list[dict]:
    conn = _get_db()
    try:
        sql = """
            SELECT mc.mistake_case_id, mc.student_id, mc.current_status, mc.created_at,
                   q.question_id, q.question_description,
                   eb.level1, eb.level2, eb.level3, eb.error_description
            FROM mistake_case mc
            JOIN question q ON mc.question_id = q.question_id
            JOIN question_knowledge_mapping qkm ON q.question_id = qkm.question_id
            LEFT JOIN mistake_case_error mce ON mc.mistake_case_id = mce.mistake_case_id
            LEFT JOIN error_bank eb ON mce.error_id = eb.error_id
            WHERE qkm.knowledge_id = ?
        """
        params: list = [knowledge_id]
        if student_id:
            sql += " AND mc.student_id = ?"
            params.append(student_id)
        sql += " ORDER BY mc.created_at DESC LIMIT 10"
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def error_causes_for_knowledge(knowledge_id: str) -> list[dict]:
    conn = _get_db()
    try:
        rows = conn.execute(
            """
            SELECT eb.error_id, eb.level1, eb.level2, eb.level3,
                   eb.error_description, COUNT(mce.mce_id) AS occurrence_count
            FROM error_bank eb
            JOIN mistake_case_error mce ON eb.error_id = mce.error_id
            JOIN mistake_case mc ON mce.mistake_case_id = mc.mistake_case_id
            JOIN question q ON mc.question_id = q.question_id
            JOIN question_knowledge_mapping qkm ON q.question_id = qkm.question_id
            WHERE qkm.knowledge_id = ?
            GROUP BY eb.error_id
            ORDER BY occurrence_count DESC
            LIMIT 10
            """,
            (knowledge_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
