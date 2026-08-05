from fastapi import APIRouter

from review.dependencies import session_service
from review.schemas.review import CorrectionRequest, CorrectionResponse


router = APIRouter(prefix="/attempts", tags=["Corrections"])


@router.post("/{attempt_id}/correction", response_model=CorrectionResponse)
def submit_correction(attempt_id: str, request: CorrectionRequest) -> CorrectionResponse:
    return session_service.correct(attempt_id, request)
