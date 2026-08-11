from review.domain.enums import Difficulty, PlanMode
from review.schemas.priority import PriorityResult
from review.schemas.review import PlanningScoreBreakdown, QuestionInternal, ReviewPlanItem


DIFFICULTY_ORDER = {
    Difficulty.BASIC: 0,
    Difficulty.PRACTICE: 1,
    Difficulty.ADVANCED: 2,
}


class QuestionSelector:
    def select(
        self,
        questions: list[QuestionInternal],
        priorities: list[PriorityResult],
        mode: PlanMode,
        question_count: int | None,
        time_limit_minutes: int | None,
        excluded_question_ids: set[str] | None = None,
        already_covered: set[str] | None = None,
    ) -> list[ReviewPlanItem]:
        excluded = excluded_question_ids or set()
        covered = set(already_covered or set())
        candidates = [question for question in questions if question.id not in excluded]
        priority_map = {item.knowledge_point_id: item for item in priorities}
        selected: list[ReviewPlanItem] = []
        used_minutes = 0

        while candidates:
            if mode == PlanMode.QUESTION_COUNT and len(selected) >= (question_count or 0):
                break
            scored = [self._score(question, priority_map, covered) for question in candidates]
            question, breakdown = max(scored, key=lambda item: item[1].final_score)
            if mode == PlanMode.TIME_LIMIT:
                limit = time_limit_minutes or 0
                if selected and used_minutes + question.estimated_minutes > limit:
                    break
            selected.append(
                ReviewPlanItem(
                    position=len(selected) + 1,
                    question_id=question.id,
                    knowledge_point_ids=[item.knowledge_point_id for item in question.knowledge],
                    planning_score=breakdown,
                )
            )
            used_minutes += question.estimated_minutes
            covered.update(item.knowledge_point_id for item in question.knowledge)
            candidates.remove(question)

        return selected

    def _score(
        self,
        question: QuestionInternal,
        priority_map: dict[str, PriorityResult],
        covered: set[str],
    ) -> tuple[QuestionInternal, PlanningScoreBreakdown]:
        weights = [item.weight for item in question.knowledge if item.knowledge_point_id in priority_map]
        total_weight = sum(weights) or 1.0
        weighted_priority = sum(
            item.weight * priority_map[item.knowledge_point_id].priority
            for item in question.knowledge
            if item.knowledge_point_id in priority_map
        ) / total_weight

        coverage_bonus = 6 * sum(
            item.weight
            for item in question.knowledge
            if item.knowledge_point_id not in covered
        )
        weighted_mastery = sum(
            item.weight * priority_map[item.knowledge_point_id].mastery.mastery
            for item in question.knowledge
            if item.knowledge_point_id in priority_map
        ) / total_weight
        target = (
            Difficulty.BASIC
            if weighted_mastery < 50
            else Difficulty.PRACTICE
            if weighted_mastery < 75
            else Difficulty.ADVANCED
        )
        distance = abs(DIFFICULTY_ORDER[question.difficulty] - DIFFICULTY_ORDER[target])
        difficulty_adjustment = 5.0 if distance == 0 else 0.0 if distance == 1 else -8.0
        final_score = weighted_priority + coverage_bonus + difficulty_adjustment
        return question, PlanningScoreBreakdown(
            weighted_priority=round(weighted_priority, 2),
            coverage_bonus=round(coverage_bonus, 2),
            difficulty_adjustment=round(difficulty_adjustment, 2),
            final_score=round(final_score, 2),
        )


question_selector = QuestionSelector()
