"""学习路径推荐（SQLite 版，替代同事的 Neo4j 查询）。"""

from typing import List, Dict

from backend.insight.core import knowledge as kdb
from backend.user_database import user_db


def normalize_student_id(student_id) -> str:
    if isinstance(student_id, int):
        return f"S-{student_id:04d}"
    return str(student_id)


class LearningPathRecommender:
    def _weak_knowledge(self, student_id: int, threshold: int = 60) -> List[Dict]:
        progress = user_db.get_weak_knowledge_points(student_id, threshold)
        result = []
        for p in progress:
            result.append({
                "knowledge_id": p["knowledge_id"],
                "title": kdb.knowledge_title(p["knowledge_id"]) or p["knowledge_id"],
                "mastery_level": p["mastery_level"],
                "wrong_count": p["wrong_count"],
            })
        return sorted(result, key=lambda x: x["mastery_level"])

    def _prerequisites(self, knowledge_id: str) -> List[str]:
        import sqlite3
        from backend.config import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT prerequisite, next_knowledge FROM knowledge WHERE knowledge_id = ?",
                (knowledge_id,),
            ).fetchone()
            if not row:
                return []
            out = []
            for pid in (row["prerequisite"], row["next_knowledge"]):
                if pid:
                    title = kdb.knowledge_title(pid)
                    out.append(f"{pid}: {title}" if title else pid)
            return out
        finally:
            conn.close()

    def generate_path(self, student_id: int, limit: int = 5) -> List[Dict]:
        weak = self._weak_knowledge(student_id)
        sid = normalize_student_id(student_id)
        nodes = []

        for item in weak[:limit]:
            mastery = item["mastery_level"]
            nodes.append({
                "knowledge_id": item["knowledge_id"],
                "title": item["title"],
                "mastery_level": mastery,
                "order": len(nodes) + 1,
                "estimated_time": "45分钟" if mastery < 40 else "30分钟",
                "type": "weak" if mastery < 40 else "learning",
                "prerequisites": self._prerequisites(item["knowledge_id"]),
                "recommended_questions": kdb.questions_for_knowledge(item["knowledge_id"], limit=3),
                "mistakes": kdb.mistake_cases_for_knowledge(item["knowledge_id"], sid),
                "error_analysis": kdb.error_causes_for_knowledge(item["knowledge_id"]),
                "suggestions": self._suggestions(mastery),
            })

        return nodes

    @staticmethod
    def _suggestions(mastery_level: int) -> List[str]:
        if mastery_level < 40:
            return ["建议从基础概念开始重新学习", "观看知识点讲解视频", "完成基础难度的练习题"]
        return ["建议重点复习该知识点的典型例题", "尝试使用不同方法解题，加深理解"]

    def generate_detailed_path(self, student_id: int, limit: int = 5) -> Dict:
        path = self.generate_path(student_id, limit)
        return {
            "student_id": student_id,
            "path": path,
            "total_nodes": len(path),
        }

    def get_knowledge_detail(self, knowledge_id: str) -> Dict:
        title = kdb.knowledge_title(knowledge_id)
        if not title:
            return {}
        return {
            "id": knowledge_id,
            "title": title,
            "prerequisites": self._prerequisites(knowledge_id),
            "questions": kdb.questions_for_knowledge(knowledge_id, limit=10),
            "error_analysis": kdb.error_causes_for_knowledge(knowledge_id),
        }

    def get_mistake_analysis(self, student_id: int) -> Dict:
        sid = normalize_student_id(student_id)
        import sqlite3
        from backend.config import DATABASE_PATH
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT eb.level1, COUNT(*) AS cnt
                FROM mistake_case mc
                JOIN mistake_case_error mce ON mc.mistake_case_id = mce.mistake_case_id
                JOIN error_bank eb ON mce.error_id = eb.error_id
                WHERE mc.student_id = ?
                GROUP BY eb.level1
                """,
                (sid,),
            ).fetchall()
            distribution = {r["level1"]: r["cnt"] for r in rows}
            total = sum(distribution.values())
            return {
                "student_id": student_id,
                "total_mistakes": total,
                "error_distribution": distribution,
            }
        finally:
            conn.close()
