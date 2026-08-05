"""系统 / 班级统计报表（SQLite 版）。"""

import sqlite3
from typing import List, Dict

from backend.config import DATABASE_PATH
from backend.insight.models import StatisticsOverview, ClassMasteryData, RevisionStatistics


def _get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class StatisticsReporter:
    def get_system_overview(self) -> StatisticsOverview:
        conn = _get_db()
        try:
            total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
            total_knowledge = conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
            total_questions = conn.execute("SELECT COUNT(*) FROM question").fetchone()[0]
            wrong = conn.execute("SELECT COUNT(*) FROM answer_history WHERE is_correct = 0").fetchone()[0]
            correct = conn.execute("SELECT COUNT(*) FROM answer_history WHERE is_correct = 1").fetchone()[0]
        finally:
            conn.close()
        return StatisticsOverview(
            total_students=total_students,
            total_teachers=1,
            total_questions=total_questions,
            total_knowledge=total_knowledge,
            total_wrong_records=wrong,
            total_revision_completed=correct,
        )

    def get_class_mastery(self, class_id: int = 0) -> List[ClassMasteryData]:
        conn = _get_db()
        try:
            rows = conn.execute(
                """
                SELECT km.knowledge_id, k.knowledge_scope AS title,
                       AVG(km.master_level * 100) AS avg_mastery,
                       COUNT(km.student_id) AS student_count
                FROM knowledge_mastery km
                LEFT JOIN knowledge k ON km.knowledge_id = k.knowledge_id
                GROUP BY km.knowledge_id
                ORDER BY avg_mastery ASC
                """
            ).fetchall()
            return [
                ClassMasteryData(
                    knowledge_id=r["knowledge_id"],
                    title=r["title"] or r["knowledge_id"],
                    average_mastery=round(r["avg_mastery"] or 0, 1),
                    student_count=r["student_count"],
                )
                for r in rows
            ]
        finally:
            conn.close()

    def get_revision_statistics(self) -> RevisionStatistics:
        conn = _get_db()
        try:
            wrong = conn.execute("SELECT COUNT(*) FROM answer_history WHERE is_correct = 0").fetchone()[0]
            correct = conn.execute("SELECT COUNT(*) FROM answer_history WHERE is_correct = 1").fetchone()[0]
            pending = conn.execute("SELECT COUNT(*) FROM push_record WHERE status IN ('pending', 'pushing')").fetchone()[0]
        finally:
            conn.close()
        total = wrong + correct
        rate = round(correct / total * 100, 1) if total else 0.0
        return RevisionStatistics(
            today_pending=pending,
            week_completed=correct,
            completion_rate=rate,
            multiple_error_rate=25.0,
        )

    def get_grade_distribution(self) -> Dict:
        conn = _get_db()
        try:
            rows = conn.execute(
                "SELECT student_grade, COUNT(*) AS cnt FROM students GROUP BY student_grade"
            ).fetchall()
            return {r["student_grade"] or "未知": r["cnt"] for r in rows}
        finally:
            conn.close()
