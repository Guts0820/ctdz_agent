import math
from datetime import date, datetime

from review.domain.enums import AssessmentState
from review.schemas.priority import (
    KnowledgeStateInput,
    MasteryComponents,
    PriorityComponents,
    PriorityResult,
)


RECENCY_DECAY = 0.85


def clip(value: float, minimum: float = 0, maximum: float = 100) -> float:
    return min(maximum, max(minimum, value))


def weighted_rate(results: list[bool], limit: int = 10) -> float:
    recent = results[-limit:]
    if not recent:
        return 50.0
    size = len(recent)
    weights = [RECENCY_DECAY ** (size - index - 1) for index in range(size)]
    return 100 * sum(weight * int(result) for weight, result in zip(weights, recent)) / sum(weights)


def volatility(results: list[bool], limit: int = 10) -> float:
    recent = results[-limit:]
    if len(recent) < 2:
        return 0.0
    changes = sum(current != previous for previous, current in zip(recent, recent[1:]))
    return changes / (len(recent) - 1)


def weighted_error_severity(severities: list[float], limit: int = 5) -> float:
    recent = severities[-limit:]
    if not recent:
        return 0.0
    size = len(recent)
    weights = [RECENCY_DECAY ** (size - index - 1) for index in range(size)]
    return 100 * sum(weight * severity for weight, severity in zip(weights, recent)) / sum(weights)


def trend_risk(results: list[bool]) -> float:
    recent = results[-10:]
    if len(recent) < 4:
        return 50.0
    split = len(recent) // 2
    older = recent[:split]
    newer = recent[split:]
    old_rate = 100 * sum(older) / len(older)
    new_rate = 100 * sum(newer) / len(newer)
    return clip(50 + old_rate - new_rate)


class PriorityCalculator:
    def calculate(
        self,
        state: KnowledgeStateInput,
        business_date: date,
        calculated_at: datetime,
        formula_version: str = "priority-v1.0",
    ) -> PriorityResult:
        evidence = sorted(state.evidence, key=lambda item: item.occurred_at)
        results = [item.is_correct for item in evidence]
        severities = [item.error_severity for item in evidence if not item.is_correct and item.error_severity is not None]
        total = state.correct_count + state.wrong_count

        history_accuracy = 100 * (state.correct_count + 2) / (total + 4)
        recent_accuracy = weighted_rate(results)
        accuracy = 50.0 if total == 0 else 0.3 * history_accuracy + 0.7 * recent_accuracy

        result_volatility = volatility(results)
        consistency = clip(
            recent_accuracy * (1 - 0.3 * result_volatility)
            + 3 * state.correct_streak
            - 8 * state.wrong_streak
        )

        stability_days = clip(
            7 + 0.15 * accuracy + 2 * state.correct_streak - 3 * state.wrong_streak,
            5,
            60,
        )
        correct_times = [item.occurred_at for item in evidence if item.is_correct]
        if correct_times:
            days_since_correct = max(0.0, (calculated_at - correct_times[-1]).total_seconds() / 86400)
            retention = 100 * math.exp(-days_since_correct / stability_days)
        else:
            retention = 0.0

        error_severity = weighted_error_severity(severities)
        error_control = clip(100 - error_severity - 8 * state.wrong_streak)
        raw_mastery = 0.4 * accuracy + 0.25 * consistency + 0.2 * retention + 0.15 * error_control
        confidence = 1 - math.exp(-total / 5)
        mastery = confidence * raw_mastery + (1 - confidence) * 50
        assessment_state = AssessmentState.UNASSESSED if total == 0 else AssessmentState.ASSESSED

        skill_mastery = 0.5 * accuracy + 0.3 * consistency + 0.2 * error_control
        skill_gap = 100 - skill_mastery
        latest_is_wrong = bool(evidence and not evidence[-1].is_correct)
        forgetting_risk = clip(
            100 - retention
            + (10 if latest_is_wrong else 0)
            + 5 * min(state.wrong_streak, 3)
        ) if correct_times else 0.0
        trend = trend_risk(results)
        priority = clip(
            0.35 * skill_gap
            + 0.25 * error_severity
            + 0.20 * forgetting_risk
            + 0.10 * state.importance
            + 0.10 * trend
        )

        return PriorityResult(
            student_id=state.student_id,
            knowledge_point_id=state.knowledge_point_id,
            business_date=business_date,
            mastery=MasteryComponents(
                accuracy=round(accuracy, 2),
                consistency=round(consistency, 2),
                retention=round(retention, 2),
                error_control=round(error_control, 2),
                raw_mastery=round(raw_mastery, 2),
                mastery=round(mastery, 2),
                confidence=round(confidence, 4),
                assessment_state=assessment_state,
                stability_days=round(stability_days, 2),
            ),
            components=PriorityComponents(
                skill_gap=round(skill_gap, 2),
                error_severity=round(error_severity, 2),
                forgetting_risk=round(forgetting_risk, 2),
                importance=round(state.importance, 2),
                trend=round(trend, 2),
            ),
            priority=round(priority, 2),
            formula_version=formula_version,
            state_version=state.state_version,
            calculated_at=calculated_at,
        )


priority_calculator = PriorityCalculator()
