from datetime import datetime

from review.domain.enums import AnalysisStatus, ItemStatus, PlanStatus
from review.repositories import AttemptRecord, ReviewRepository, SessionRecord
from review.schemas.review import (
    AttemptResponse,
    CorrectionRequest,
    CorrectionResponse,
    QuestionForStudent,
    SessionStateResponse,
    StartSessionResponse,
    SubmitAttemptRequest,
)
from review.services.plan_service import PlanService


class SessionService:
    def __init__(self, repository: ReviewRepository, plan_service: PlanService) -> None:
        self.repository = repository
        self.plan_service = plan_service

    def start(self, plan_id: str) -> StartSessionResponse:
        plan = self.plan_service.get(plan_id)
        existing_id = self.repository.session_by_plan.get(plan_id)
        if existing_id:
            session = self.repository.sessions[existing_id]
            question = self._student_question(plan.items[session.current_position].question_id)
            return StartSessionResponse(
                session_id=session.id,
                plan_id=plan.id,
                status=session.status,
                current_position=session.current_position,
                current_question=question,
                elapsed_seconds=self._elapsed(session),
            )
        if not plan.items:
            raise ValueError("计划中没有可用题目")
        plan.status = PlanStatus.IN_PROGRESS
        plan.frozen_at = self.repository.now()
        plan.items[0].status = ItemStatus.CURRENT
        session = SessionRecord(
            id=self.repository.new_id("session"),
            plan_id=plan.id,
            student_id=plan.student_id,
            status=PlanStatus.IN_PROGRESS,
            current_position=0,
            elapsed_seconds=0,
            started_at=self.repository.now(),
            resumed_at=self.repository.now(),
        )
        self.repository.save_plan(plan)
        self.repository.save_session(session)
        return StartSessionResponse(
            session_id=session.id,
            plan_id=plan.id,
            status=session.status,
            current_position=0,
            current_question=self._student_question(plan.items[0].question_id),
            elapsed_seconds=0,
        )

    def state(self, session_id: str) -> SessionStateResponse:
        session = self._get(session_id)
        plan = self.plan_service.get(session.plan_id)
        current = None
        if session.status != PlanStatus.COMPLETED:
            current = self._student_question(plan.items[session.current_position].question_id)
        wrong_attempts = [
            attempt_id
            for attempt_id in session.attempt_ids
            if not self.repository.attempts[attempt_id].is_correct
        ]
        return SessionStateResponse(
            session_id=session.id,
            plan_id=plan.id,
            status=session.status,
            current_position=session.current_position,
            total_questions=len(plan.items),
            elapsed_seconds=self._elapsed(session),
            current_question=current,
            wrong_attempt_ids=wrong_attempts,
        )

    def pause(self, session_id: str) -> SessionStateResponse:
        session = self._get(session_id)
        if session.status != PlanStatus.IN_PROGRESS:
            raise ValueError("只有进行中的Session可以暂停")
        session.elapsed_seconds = self._elapsed(session)
        session.resumed_at = None
        session.status = PlanStatus.PAUSED
        self.plan_service.get(session.plan_id).status = PlanStatus.PAUSED
        return self.state(session_id)

    def resume(self, session_id: str) -> SessionStateResponse:
        session = self._get(session_id)
        if session.status != PlanStatus.PAUSED:
            raise ValueError("只有暂停的Session可以恢复")
        session.status = PlanStatus.IN_PROGRESS
        session.resumed_at = self.repository.now()
        self.plan_service.get(session.plan_id).status = PlanStatus.IN_PROGRESS
        return self.state(session_id)

    def submit(self, session_id: str, request: SubmitAttemptRequest) -> AttemptResponse:
        session = self._get(session_id)
        if session.status != PlanStatus.IN_PROGRESS:
            raise ValueError("Session当前不能提交答案")
        plan = self.plan_service.get(session.plan_id)
        item = plan.items[session.current_position]
        if request.question_id != item.question_id:
            raise ValueError("不能跳题或提交非当前题目")
        if any(self.repository.attempts[item_id].position == item.position for item_id in session.attempt_ids):
            raise ValueError("当前题目已经提交，不能修改")
        question = self.repository.get_question(request.question_id)
        if request.selected_option >= len(question.options):
            raise ValueError("选项超出范围")

        now = self.repository.now()
        attempt = AttemptRecord(
            id=self.repository.new_id("attempt"),
            session_id=session.id,
            question_id=question.id,
            position=item.position,
            selected_option=request.selected_option,
            is_correct=request.selected_option == question.correct_option,
            analysis_status=AnalysisStatus.COMPLETED,
            submitted_at=now,
        )
        self.repository.attempts[attempt.id] = attempt
        session.attempt_ids.append(attempt.id)
        item.status = ItemStatus.COMPLETED

        self.repository.apply_attempt_evidence(attempt)

        completed = session.current_position == len(plan.items) - 1
        next_position = None
        if completed:
            session.elapsed_seconds = self._elapsed(session)
            session.resumed_at = None
            session.status = PlanStatus.COMPLETED
            plan.status = PlanStatus.COMPLETED
        else:
            session.current_position += 1
            next_position = session.current_position
            plan.items[next_position].status = ItemStatus.CURRENT

        return AttemptResponse(
            attempt_id=attempt.id,
            session_id=session.id,
            question_id=question.id,
            is_correct=attempt.is_correct,
            analysis_status=attempt.analysis_status,
            submitted_at=attempt.submitted_at,
            next_position=next_position,
            session_completed=completed,
        )

    def correct(self, attempt_id: str, request: CorrectionRequest) -> CorrectionResponse:
        attempt = self.repository.attempts.get(attempt_id)
        if not attempt:
            raise LookupError("答题记录不存在")
        session = self._get(attempt.session_id)
        if session.status != PlanStatus.COMPLETED:
            raise ValueError("正式复习完成后才能集中订正")
        if attempt.is_correct:
            raise ValueError("正确题目不需要订正")
        if attempt.correction_count >= 1:
            raise ValueError("每道错题只允许订正一次")
        question = self.repository.get_question(attempt.question_id)
        if request.selected_option >= len(question.options):
            raise ValueError("选项超出范围")
        attempt.correction_count = 1
        attempt.correction_selected_option = request.selected_option
        attempt.correction_is_correct = request.selected_option == question.correct_option
        attempt.correction_at = self.repository.now()
        attempt.policy_version = "class-answer-policy-v1.0"
        reveal = bool(not attempt.correction_is_correct)
        return CorrectionResponse(
            attempt_id=attempt.id,
            correction_number=1,
            is_correct=bool(attempt.correction_is_correct),
            answer_revealed=reveal,
            correct_option=question.correct_option if reveal else None,
            policy_version=attempt.policy_version or "",
            recorded_at=attempt.correction_at,
        )

    def _get(self, session_id: str) -> SessionRecord:
        session = self.repository.sessions.get(session_id)
        if not session:
            raise LookupError("Session不存在")
        return session

    def _student_question(self, question_id: str) -> QuestionForStudent:
        question = self.repository.get_question(question_id)
        return QuestionForStudent(
            id=question.id,
            prompt=question.prompt,
            options=question.options,
            knowledge_point_ids=[item.knowledge_point_id for item in question.knowledge],
            difficulty=question.difficulty,
            source_type=question.source_type,
        )

    def _elapsed(self, session: SessionRecord) -> int:
        if session.status != PlanStatus.IN_PROGRESS or session.resumed_at is None:
            return session.elapsed_seconds
        delta = self.repository.now() - session.resumed_at
        return session.elapsed_seconds + max(0, int(delta.total_seconds()))
