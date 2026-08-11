from fastapi import APIRouter

from review.dependencies import session_service
from review.schemas.review import (
    AttemptResponse,
    SessionStateResponse,
    StartSessionResponse,
    SubmitAttemptRequest,
)


router = APIRouter(tags=["Review Sessions"])


@router.post("/review-plans/{plan_id}/start", response_model=StartSessionResponse)
def start_session(plan_id: str) -> StartSessionResponse:
    return session_service.start(plan_id)


@router.get("/review-sessions/{session_id}", response_model=SessionStateResponse)
def get_session(session_id: str) -> SessionStateResponse:
    return session_service.state(session_id)


@router.post("/review-sessions/{session_id}/pause", response_model=SessionStateResponse)
def pause_session(session_id: str) -> SessionStateResponse:
    return session_service.pause(session_id)


@router.post("/review-sessions/{session_id}/resume", response_model=SessionStateResponse)
def resume_session(session_id: str) -> SessionStateResponse:
    return session_service.resume(session_id)


@router.post("/review-sessions/{session_id}/attempts", response_model=AttemptResponse)
def submit_attempt(session_id: str, request: SubmitAttemptRequest) -> AttemptResponse:
    return session_service.submit(session_id, request)
