from fastapi import APIRouter

from review.dependencies import plan_service
from review.schemas.review import CreateReviewPlanRequest, ReviewPlan, UpdatePlanCapacityRequest


router = APIRouter(prefix="/review-plans", tags=["Review Plans"])


@router.post("", response_model=ReviewPlan)
def create_review_plan(request: CreateReviewPlanRequest) -> ReviewPlan:
    return plan_service.create(request)


@router.get("/{plan_id}", response_model=ReviewPlan)
def get_review_plan(plan_id: str) -> ReviewPlan:
    return plan_service.get(plan_id)


@router.patch("/{plan_id}/capacity", response_model=ReviewPlan)
def update_plan_capacity(plan_id: str, request: UpdatePlanCapacityRequest) -> ReviewPlan:
    return plan_service.update_capacity(plan_id, request)
