from fastapi import APIRouter, HTTPException
from typing import List, Dict

from backend.insight.core.aggregator import aggregator
from backend.insight.core.learning_path import normalize_student_id
from backend.insight.models import GrowthReportData


router = APIRouter(prefix="/api", tags=["growth_report"])


def _generate_review_plan_for_user(user_id: int) -> List[Dict] | None:
    try:
        from review.dependencies import plan_service
        from review.schemas.review import CreateReviewPlanRequest
        plan = plan_service.create(
            CreateReviewPlanRequest(
                student_id=normalize_student_id(user_id),
                mode="question_count",
                question_count=5,
            )
        )
        return [
            {
                "position": item.position,
                "question_id": item.question_id,
                "knowledge_point_ids": item.knowledge_point_ids,
            }
            for item in plan.items
        ]
    except Exception:
        return None


@router.get("/growth_report/{user_id}", response_model=GrowthReportData)
def get_growth_report(user_id: int):
    try:
        return aggregator.generate_growth_report(user_id, review_plan=_generate_review_plan_for_user(user_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/five_dimension/{user_id}")
def get_five_dimension(user_id: int):
    try:
        return {"user_id": user_id, "dimensions": aggregator.five_dimension_scores(user_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weak_areas/{user_id}")
def get_weak_areas(user_id: int, threshold: int = 60):
    try:
        return {"user_id": user_id, "weak_areas": aggregator.weak_knowledge_areas(user_id, threshold)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent_progress/{user_id}")
def get_recent_progress(user_id: int):
    try:
        return {"user_id": user_id, "progress": aggregator.recent_progress(user_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/learning_path/{user_id}")
def get_learning_path(user_id: int, limit: int = 5):
    try:
        from backend.insight.core.learning_path import LearningPathRecommender
        path = LearningPathRecommender().generate_path(user_id, limit)
        return {"user_id": user_id, "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
