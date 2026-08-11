from fastapi import APIRouter, HTTPException
from typing import List, Dict

from backend.insight.core.statistics import StatisticsReporter
from backend.insight.core.learning_path import LearningPathRecommender, normalize_student_id
from backend.insight.core.aggregator import aggregator
from backend.insight.core import knowledge as kdb


router = APIRouter(prefix="/api/datahub", tags=["datahub"])

statistics = StatisticsReporter()
path_recommender = LearningPathRecommender()


@router.get("/statistics/overview")
def get_statistics_overview():
    try:
        return statistics.get_system_overview()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/class_mastery/{class_id}")
def get_class_mastery(class_id: int):
    try:
        result = statistics.get_class_mastery(class_id)
        return {"class_id": class_id, "knowledge_list": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/revision")
def get_revision_statistics():
    try:
        return statistics.get_revision_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/grade_distribution")
def get_grade_distribution():
    try:
        return statistics.get_grade_distribution()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning_path/{student_id}")
def get_learning_path(student_id: int, limit: int = 5):
    try:
        return {"student_id": student_id, "path": path_recommender.generate_path(student_id, limit)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comprehensive/{student_id}")
def get_comprehensive_analysis(student_id: int):
    try:
        sid = normalize_student_id(student_id)
        return {
            "student_id": student_id,
            "five_dimension_scores": aggregator.five_dimension_scores(student_id),
            "weak_knowledge_areas": aggregator.weak_knowledge_areas(student_id),
            "learning_path": path_recommender.generate_detailed_path(student_id, limit=5),
            "mistake_analysis": path_recommender.get_mistake_analysis(student_id),
            "student_id_formatted": sid,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/{knowledge_id}")
def get_knowledge_detail(knowledge_id: str):
    try:
        result = path_recommender.get_knowledge_detail(knowledge_id)
        if not result:
            raise HTTPException(status_code=404, detail="知识点不存在")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/{knowledge_id}/questions")
def get_knowledge_questions(knowledge_id: str, difficulty: int = 0, limit: int = 10):
    try:
        questions = kdb.questions_for_knowledge(knowledge_id, difficulty, limit)
        return {"knowledge_id": knowledge_id, "questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/{knowledge_id}/mistakes")
def get_knowledge_mistakes(knowledge_id: str, student_id: int = 0):
    try:
        sid = normalize_student_id(student_id) if student_id else ""
        return {
            "knowledge_id": knowledge_id,
            "mistakes": kdb.mistake_cases_for_knowledge(knowledge_id, sid),
            "error_analysis": kdb.error_causes_for_knowledge(knowledge_id),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mistake_analysis/{student_id}")
def get_mistake_analysis(student_id: int):
    try:
        return path_recommender.get_mistake_analysis(student_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
