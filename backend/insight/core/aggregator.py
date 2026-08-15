"""成长报告聚合器（五维能力 / 薄弱点 / 近期进步 / 学习路径 / 复习计划）。"""

from typing import List, Dict, Optional

from backend.insight.core import knowledge as kdb
from backend.insight.core.learning_path import LearningPathRecommender, normalize_student_id
from backend.insight.models import GrowthReportData, LearningPathNode
from backend.user_database import user_db


OPERATION_KEYWORDS = ["计算", "运算", "加减", "乘除", "竖式", "口算", "笔算", "混合运算"]
LOGIC_KEYWORDS = ["推理", "规律", "逻辑", "排列", "组合", "归纳", "演绎", "判断"]
SPATIAL_KEYWORDS = ["图形", "几何", "空间", "位置", "方向", "对称", "面积", "体积", "周长"]
LANGUAGE_KEYWORDS = ["应用题", "解决问题", "文字题", "理解", "表达", "描述"]


class DataAggregator:
    def __init__(self):
        self.path_recommender = LearningPathRecommender()

    def _ability_score(self, user_id: int, keywords: List[str]) -> int:
        progress = user_db.get_learning_progress(user_id)
        if not progress:
            return 0
        scores = []
        for p in progress:
            title = kdb.knowledge_title(p["knowledge_id"])
            if not keywords or any(kw in title for kw in keywords):
                scores.append(p["mastery_level"])
        return round(sum(scores) / len(scores)) if scores else 0

    def _resilience_score(self, user_id: int) -> int:
        wrong = user_db.get_wrong_questions(user_id)
        reviewed = sum(1 for w in wrong if w["reviewed"])
        records = user_db.get_answer_records(user_id, limit=100)
        correct = sum(1 for r in records if r["is_correct"])
        total = len(records)

        review_rate = reviewed / len(wrong) if wrong else 0.5
        persist_rate = min(correct / max(total - correct, 1), 2.0) if total > 0 else 0.5
        score = round((review_rate * 0.4 + persist_rate * 0.4 + 0.5 * 0.2) * 100)
        return min(max(score, 0), 100)

    def five_dimension_scores(self, user_id: int) -> List[Dict]:
        labels = {
            "operation": "运算能力",
            "logic": "逻辑思维",
            "spatial": "空间想象",
            "language": "语言推理",
            "resilience": "学习韧性",
        }
        scores = {
            "operation": self._ability_score(user_id, OPERATION_KEYWORDS),
            "logic": self._ability_score(user_id, LOGIC_KEYWORDS),
            "spatial": self._ability_score(user_id, SPATIAL_KEYWORDS),
            "language": self._ability_score(user_id, LANGUAGE_KEYWORDS),
            "resilience": self._resilience_score(user_id),
        }
        return [
            {"dimension": dim, "score": scores[dim], "max_score": 100, "label": labels[dim]}
            for dim in labels
        ]

    def weak_knowledge_areas(self, user_id: int, threshold: int = 60) -> List[Dict]:
        weak = user_db.get_weak_knowledge_points(user_id, threshold)
        result = []
        for wp in weak:
            title = kdb.knowledge_title(wp["knowledge_id"]) or wp["knowledge_id"]
            level = wp["mastery_level"]
            suggestions = []
            if level < 40:
                suggestions.append("建议重新学习基础知识，理解核心概念")
                suggestions.append("多做基础练习题，巩固知识点")
            elif level < 60:
                suggestions.append("建议重点复习该知识点的典型例题")
                suggestions.append("尝试使用不同方法解题，加深理解")
            if wp["wrong_count"] >= 3:
                suggestions.append("建议查看错题解析，分析错误原因")
            result.append({
                "knowledge_id": wp["knowledge_id"],
                "title": title,
                "mastery_level": level,
                "error_count": wp["wrong_count"],
                "difficulty": "基础" if level < 40 else "进阶" if level < 60 else "提高",
                "suggestions": suggestions,
            })
        return sorted(result, key=lambda x: x["mastery_level"])

    def mastered_knowledge_areas(self, user_id: int, threshold: int = 80) -> List[Dict]:
        mastered = user_db.get_mastered_knowledge_points(user_id, threshold)
        result = []
        for mp in mastered:
            title = kdb.knowledge_title(mp["knowledge_id"]) or mp["knowledge_id"]
            result.append({
                "knowledge_id": mp["knowledge_id"],
                "title": title,
                "mastery_level": mp["mastery_level"],
            })
        return result

    def recent_progress(self, user_id: int) -> List[Dict]:
        progress = user_db.get_learning_progress(user_id)
        result = []
        for p in progress:
            total = p["correct_count"] + p["wrong_count"]
            if total == 0:
                continue
            rate = p["correct_count"] / total
            previous = max(0, p["mastery_level"] - round(rate * 15))
            result.append({
                "knowledge_id": p["knowledge_id"],
                "title": kdb.knowledge_title(p["knowledge_id"]) or p["knowledge_id"],
                "previous_mastery": previous,
                "current_mastery": p["mastery_level"],
                "improvement": p["mastery_level"] - previous,
                "achieved": p["mastery_level"] >= 80,
            })
        return sorted(result, key=lambda x: x["improvement"], reverse=True)[:5]

    def generate_growth_report(self, user_id: int, review_plan: Optional[List[Dict]] = None) -> GrowthReportData:
        path_nodes = [
            LearningPathNode(
                knowledge_id=n["knowledge_id"],
                title=n["title"],
                order=n["order"],
                estimated_time=n.get("estimated_time", "45分钟"),
                type=n.get("type", "normal"),
                prerequisites=n.get("prerequisites", []),
            )
            for n in self.path_recommender.generate_path(user_id, limit=5)
        ]
        return GrowthReportData(
            student_id=user_id,
            five_dimension_scores=self.five_dimension_scores(user_id),
            weak_knowledge_areas=self.weak_knowledge_areas(user_id),
            mastered_knowledge_areas=self.mastered_knowledge_areas(user_id),
            recent_progress=self.recent_progress(user_id),
            learning_path=path_nodes,
            review_plan=review_plan,
        )


aggregator = DataAggregator()
