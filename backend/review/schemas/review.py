from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from review.domain.enums import Difficulty, ItemStatus, PlanMode, PlanStatus


class KnowledgeWeight(BaseModel):
    knowledge_point_id: str
    weight: float = Field(gt=0, le=1)


class QuestionInternal(BaseModel):
    id: str
    prompt: str
    options: list[str]
    correct_option: int = Field(ge=0)
    knowledge: list[KnowledgeWeight]
    difficulty: Difficulty
    estimated_minutes: int = Field(default=2, ge=1)
    enabled: bool = True
    source_type: str = "sqlite"

    @model_validator(mode="after")
    def validate_correct_option(self) -> "QuestionInternal":
        if not self.options:
            max_opt = max(4, self.correct_option + 1)
            self.options = [str(i + 1) for i in range(max_opt)]
        if self.correct_option >= len(self.options):
            self.correct_option = len(self.options) - 1
        return self


class QuestionForStudent(BaseModel):
    id: str
    prompt: str
    options: list[str]
    knowledge_point_ids: list[str]
    difficulty: Difficulty
    source_type: str


class PlanningScoreBreakdown(BaseModel):
    weighted_priority: float
    coverage_bonus: float
    difficulty_adjustment: float
    final_score: float


class ReviewPlanItem(BaseModel):
    position: int
    question_id: str
    knowledge_point_ids: list[str]
    status: ItemStatus = ItemStatus.PENDING
    planning_score: PlanningScoreBreakdown


class CreateReviewPlanRequest(BaseModel):
    student_id: str
    mode: PlanMode = PlanMode.QUESTION_COUNT
    question_count: int | None = Field(default=10, ge=1, le=30)
    time_limit_minutes: int | None = Field(default=None, ge=1, le=120)
    business_date: date | None = None

    @model_validator(mode="after")
    def validate_capacity(self) -> "CreateReviewPlanRequest":
        if self.mode == PlanMode.QUESTION_COUNT and self.question_count is None:
            raise ValueError("按题量模式必须提供question_count")
        if self.mode == PlanMode.TIME_LIMIT and self.time_limit_minutes is None:
            raise ValueError("按时间模式必须提供time_limit_minutes")
        return self


class UpdatePlanCapacityRequest(BaseModel):
    question_count: int = Field(ge=1, le=30)


class ReviewPlan(BaseModel):
    id: str
    student_id: str
    business_date: date
    mode: PlanMode
    question_count: int | None
    time_limit_minutes: int | None
    priority_run_id: str
    status: PlanStatus
    items: list[ReviewPlanItem]
    created_at: datetime
    frozen_at: datetime | None = None
    planning_config_version: str


class StartSessionResponse(BaseModel):
    session_id: str
    plan_id: str
    status: PlanStatus
    current_position: int
    current_question: QuestionForStudent
    elapsed_seconds: int


class SessionStateResponse(BaseModel):
    session_id: str
    plan_id: str
    status: PlanStatus
    current_position: int
    total_questions: int
    elapsed_seconds: int
    current_question: QuestionForStudent | None
    wrong_attempt_ids: list[str] = Field(default_factory=list)


class SubmitAttemptRequest(BaseModel):
    question_id: str
    selected_option: int = Field(ge=0)


class AttemptResponse(BaseModel):
    attempt_id: str
    session_id: str
    question_id: str
    is_correct: bool
    analysis_status: str
    submitted_at: datetime
    next_position: int | None
    session_completed: bool


class CorrectionRequest(BaseModel):
    selected_option: int = Field(ge=0)


class CorrectionResponse(BaseModel):
    attempt_id: str
    correction_number: int
    is_correct: bool
    answer_revealed: bool
    correct_option: int | None = None
    policy_version: str
    recorded_at: datetime
