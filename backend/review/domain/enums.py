from enum import StrEnum


class PlanMode(StrEnum):
    QUESTION_COUNT = "question_count"
    TIME_LIMIT = "time_limit"


class PlanStatus(StrEnum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"


class ItemStatus(StrEnum):
    PENDING = "pending"
    CURRENT = "current"
    COMPLETED = "completed"


class AssessmentState(StrEnum):
    UNASSESSED = "unassessed"
    ASSESSED = "assessed"


class Difficulty(StrEnum):
    BASIC = "basic"
    PRACTICE = "practice"
    ADVANCED = "advanced"


class AnalysisStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
