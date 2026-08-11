from fastapi import APIRouter

from review.dependencies import priority_service
from review.schemas.priority import PriorityRunRequest, PriorityRunResponse


router = APIRouter(prefix="/priority-runs", tags=["Priority"])


@router.post("", response_model=PriorityRunResponse)
def calculate_priority(request: PriorityRunRequest) -> PriorityRunResponse:
    return priority_service.run_for_student(request.student_id, request.business_date)
