from datetime import date, datetime
from typing import Union

from pydantic import BaseModel, Field, model_validator

from review.domain.enums import AssessmentState


class PracticeEvidence(BaseModel):
    is_correct: bool
    occurred_at: datetime
    error_severity: float | None = Field(default=None, ge=0, le=1)


class KnowledgeStateInput(BaseModel):
    student_id: Union[int, str]
    knowledge_point_id: str
    correct_count: int = Field(ge=0)
    wrong_count: int = Field(ge=0)
    correct_streak: int = Field(ge=0)
    wrong_streak: int = Field(ge=0)
    evidence: list[PracticeEvidence] = Field(default_factory=list)
    importance: float = Field(default=50, ge=0, le=100)
    state_version: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def validate_counts(self) -> "KnowledgeStateInput":
        if self.correct_count + self.wrong_count < len(self.evidence):
            raise ValueError("累计答题次数不能小于证据记录数量")
        if self.correct_streak and self.wrong_streak:
            raise ValueError("正确连续次数和错误连续次数不能同时大于0")
        return self


class MasteryComponents(BaseModel):
    accuracy: float
    consistency: float
    retention: float
    error_control: float
    raw_mastery: float
    mastery: float
    confidence: float
    assessment_state: AssessmentState
    stability_days: float


class PriorityComponents(BaseModel):
    skill_gap: float
    error_severity: float
    forgetting_risk: float
    importance: float
    trend: float


class PriorityResult(BaseModel):
    student_id: Union[int, str]
    knowledge_point_id: str
    business_date: date
    mastery: MasteryComponents
    components: PriorityComponents
    priority: float
    formula_version: str
    state_version: int
    calculated_at: datetime


class PriorityRunRequest(BaseModel):
    student_id: Union[int, str]
    business_date: date | None = None


class PriorityRunResponse(BaseModel):
    run_id: str
    student_id: Union[int, str]
    business_date: date
    results: list[PriorityResult]
    formula_version: str
    created: bool
