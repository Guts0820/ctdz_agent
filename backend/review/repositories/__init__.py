"""SQLite 数据仓储：把同事复习引擎原来依赖的 Neo4j 数据源替换为本仓库 SQLite。

保持与同事 ReviewRepository 相同的接口（get_knowledge_states / get_questions /
get_question / save_plan / save_session / apply_attempt_evidence 等），
以便 services / api 层无需改动即可运行。
"""

import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from uuid import uuid4

from backend.config import DATABASE_PATH
from review.domain.enums import AnalysisStatus, Difficulty, PlanStatus
from review.schemas.priority import KnowledgeStateInput, PracticeEvidence, PriorityRunResponse
from review.schemas.review import (
    KnowledgeWeight,
    QuestionInternal,
    ReviewPlan,
)


@dataclass
class SessionRecord:
    id: str
    plan_id: str
    student_id: str
    status: PlanStatus
    current_position: int
    elapsed_seconds: int
    started_at: datetime
    resumed_at: datetime | None
    attempt_ids: list[str] = field(default_factory=list)


@dataclass
class AttemptRecord:
    id: str
    session_id: str
    question_id: str
    position: int
    selected_option: int
    is_correct: bool
    analysis_status: AnalysisStatus
    submitted_at: datetime
    correction_count: int = 0
    correction_is_correct: bool | None = None
    correction_selected_option: int | None = None
    correction_at: datetime | None = None
    policy_version: str | None = None


DIFFICULTY_MAP = {
    "easy": Difficulty.BASIC,
    "medium": Difficulty.PRACTICE,
    "hard": Difficulty.ADVANCED,
    1: Difficulty.BASIC,
    2: Difficulty.PRACTICE,
    3: Difficulty.ADVANCED,
}


def _normalize_student_id(student_id) -> str:
    if isinstance(student_id, int):
        return f"S-{student_id:04d}"
    return str(student_id)


def _get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class ReviewRepository:
    def __init__(self) -> None:
        self.priority_runs: dict[tuple[str, date], PriorityRunResponse] = {}
        self.plans: dict[str, ReviewPlan] = {}
        self.plan_by_student_date: dict[tuple[str, date], str] = {}
        self.sessions: dict[str, SessionRecord] = {}
        self.session_by_plan: dict[str, str] = {}
        self.attempts: dict[str, AttemptRecord] = {}
        self._questions_cache: list[QuestionInternal] | None = None
        self._questions_cache_time: datetime | None = None

    # ---------- 基础 ----------

    def now(self) -> datetime:
        return datetime.now()

    def new_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid4().hex[:16]}"

    # ---------- 知识点状态（来自 knowledge_mastery + answer_history） ----------

    def get_knowledge_states(self, student_id) -> list[KnowledgeStateInput]:
        sid = _normalize_student_id(student_id)
        conn = _get_db()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT km.knowledge_id, km.mastery_status, km.correct_count, km.wrong_count,
                       km.master_level, k.knowledge_scope
                FROM knowledge_mastery km
                LEFT JOIN knowledge k ON km.knowledge_id = k.knowledge_id
                WHERE km.student_id = ?
                ORDER BY km.updated_at DESC
                """,
                (sid,),
            )
            rows = [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

        states = []
        for row in rows:
            evidence = self._load_evidence(sid, row["knowledge_id"])
            correct_count = row["correct_count"] or 0
            wrong_count = row["wrong_count"] or 0
            if evidence:
                correct_count = sum(1 for e in evidence if e.is_correct)
                wrong_count = len(evidence) - correct_count
            correct_streak, wrong_streak = self._streaks(evidence)
            states.append(
                KnowledgeStateInput(
                    student_id=sid,
                    knowledge_point_id=row["knowledge_id"],
                    correct_count=correct_count,
                    wrong_count=wrong_count,
                    correct_streak=correct_streak,
                    wrong_streak=wrong_streak,
                    evidence=evidence,
                    importance=50.0,
                    state_version=1,
                )
            )
        return states

    def get_fallback_states(self, student_id) -> list[KnowledgeStateInput]:
        sid = _normalize_student_id(student_id)
        conn = _get_db()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT knowledge_id FROM question_knowledge_mapping
                UNION
                SELECT knowledge_id FROM knowledge_mastery WHERE student_id = ?
                LIMIT 20
                """,
                (sid,),
            )
            rows = [r[0] for r in cur.fetchall()]
        finally:
            conn.close()

        return [
            KnowledgeStateInput(
                student_id=sid,
                knowledge_point_id=kid,
                correct_count=0,
                wrong_count=0,
                correct_streak=0,
                wrong_streak=0,
                evidence=[],
                importance=50.0,
                state_version=1,
            )
            for kid in rows
        ]

    def _load_evidence(self, student_id: str, knowledge_id: str) -> list[PracticeEvidence]:
        conn = _get_db()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT ah.is_correct, ah.submitted_at, ah.core_error_type
                FROM answer_history ah
                JOIN question_knowledge_mapping qkm ON ah.question_id = qkm.question_id
                WHERE ah.student_id = ? AND qkm.knowledge_id = ?
                ORDER BY ah.submitted_at
                """,
                (student_id, knowledge_id),
            )
            rows = cur.fetchall()
        finally:
            conn.close()

        severity_map = {
            "计算失误": 0.6, "概念混淆": 0.8, "审题错误": 0.5,
            "粗心": 0.3, "疑似抄袭": 0.9, "未作答": 0.2, "未知": 0.5, "": 0.5,
        }
        evidence = []
        for row in rows:
            occurred_at = datetime.fromisoformat(row["submitted_at"]) if row["submitted_at"] else datetime.now()
            evidence.append(
                PracticeEvidence(
                    is_correct=bool(row["is_correct"]),
                    occurred_at=occurred_at,
                    error_severity=severity_map.get(row["core_error_type"] or "", 0.5)
                    if not row["is_correct"] else None,
                )
            )
        return evidence

    @staticmethod
    def _streaks(evidence: list[PracticeEvidence]) -> tuple[int, int]:
        correct_streak = 0
        wrong_streak = 0
        for ev in reversed(evidence):
            if ev.is_correct:
                if wrong_streak > 0:
                    break
                correct_streak += 1
            else:
                if correct_streak > 0:
                    break
                wrong_streak += 1
        return correct_streak, wrong_streak

    # ---------- 题目（来自 question + question_knowledge_mapping） ----------

    def get_questions(self) -> list[QuestionInternal]:
        cache_ttl = 300
        now = self.now()
        if self._questions_cache and self._questions_cache_time:
            if (now - self._questions_cache_time).total_seconds() < cache_ttl:
                return self._questions_cache

        conn = _get_db()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT q.question_id, q.question_description, q.difficulty, q.answer,
                       qkm.knowledge_id, qkm.mapping_weight
                FROM question q
                LEFT JOIN question_knowledge_mapping qkm ON q.question_id = qkm.question_id
                ORDER BY q.question_id
                """
            )
            rows = [dict(r) for r in cur.fetchall()]
        finally:
            conn.close()

        question_map = {}
        for row in rows:
            qid = row["question_id"]
            if qid not in question_map:
                answer = (row["answer"] or "").strip()
                options, correct_option = self._build_options(answer)
                question_map[qid] = {
                    "id": qid,
                    "prompt": row["question_description"] or "",
                    "options": options,
                    "correct_option": correct_option,
                    "knowledge": [],
                    "difficulty": DIFFICULTY_MAP.get((row["difficulty"] or "medium").lower(), Difficulty.PRACTICE),
                    "estimated_minutes": 2,
                    "enabled": True,
                    "source_type": "sqlite",
                }
            if row.get("knowledge_id"):
                question_map[qid]["knowledge"].append(
                    KnowledgeWeight(
                        knowledge_point_id=row["knowledge_id"],
                        weight=float(row["mapping_weight"] or 1.0),
                    )
                )

        questions = []
        for qid, qdata in question_map.items():
            if not qdata["knowledge"]:
                qdata["knowledge"].append(KnowledgeWeight(knowledge_point_id="unknown", weight=1.0))
            questions.append(QuestionInternal(**qdata))

        self._questions_cache = questions
        self._questions_cache_time = now
        return questions

    @staticmethod
    def _build_options(answer: str) -> tuple[list[str], int]:
        if answer:
            try:
                num = float(answer)
                if num == int(num):
                    num = int(num)
                wrong_options = [
                    str(int(num) + 1),
                    str(int(num) - 1) if int(num) > 0 else str(int(num) + 2),
                    str(int(num) * 2),
                ]
                return [str(num)] + wrong_options[:3], 0
            except (ValueError, TypeError):
                pass
        return ["选项A", "选项B", "选项C", "选项D"], 0

    def get_fallback_questions(self) -> list[QuestionInternal]:
        fallback_data = [
            {"id": "FB-001", "prompt": "计算 2.4 × 0.35，正确的结果是？", "options": ["0.084", "0.84", "8.4", "84"], "correct_option": 1, "knowledge": [KnowledgeWeight(knowledge_point_id="K001", weight=1.0)], "difficulty": Difficulty.BASIC, "estimated_minutes": 2, "enabled": True, "source_type": "fallback"},
            {"id": "FB-002", "prompt": "7.2 ÷ 0.6 的商是多少？", "options": ["1.2", "12", "120", "0.12"], "correct_option": 1, "knowledge": [KnowledgeWeight(knowledge_point_id="K002", weight=1.0)], "difficulty": Difficulty.BASIC, "estimated_minutes": 2, "enabled": True, "source_type": "fallback"},
            {"id": "FB-003", "prompt": "三角形底8cm、高5cm，面积是多少？", "options": ["13cm²", "20cm²", "40cm²", "80cm²"], "correct_option": 1, "knowledge": [KnowledgeWeight(knowledge_point_id="K003", weight=1.0)], "difficulty": Difficulty.PRACTICE, "estimated_minutes": 2, "enabled": True, "source_type": "fallback"},
            {"id": "FB-004", "prompt": "1÷6的商用循环小数表示是？", "options": ["0.16", "0.1666…", "0.6161…", "1.666…"], "correct_option": 1, "knowledge": [KnowledgeWeight(knowledge_point_id="K004", weight=1.0)], "difficulty": Difficulty.PRACTICE, "estimated_minutes": 2, "enabled": True, "source_type": "fallback"},
            {"id": "FB-005", "prompt": "盒中有3个红球和2个蓝球，摸到红球的可能性是？", "options": ["2/5", "3/5", "1/2", "3/2"], "correct_option": 1, "knowledge": [KnowledgeWeight(knowledge_point_id="K005", weight=1.0)], "difficulty": Difficulty.BASIC, "estimated_minutes": 2, "enabled": True, "source_type": "fallback"},
        ]
        return [QuestionInternal(**data) for data in fallback_data]

    def get_question(self, question_id: str) -> QuestionInternal:
        questions = self.get_questions()
        for q in questions:
            if q.id == question_id:
                return q
        fallback = self.get_fallback_questions()
        for q in fallback:
            if q.id == question_id:
                return q
        if fallback:
            return fallback[0]
        raise LookupError(f"Question not found: {question_id}")

    # ---------- 计划 / 会话 / 作答 ----------

    def get_plan_for_date(self, student_id: str, business_date: date) -> ReviewPlan | None:
        plan_id = self.plan_by_student_date.get((student_id, business_date))
        return self.plans.get(plan_id) if plan_id else None

    def save_plan(self, plan: ReviewPlan) -> None:
        self.plans[plan.id] = plan
        self.plan_by_student_date[(plan.student_id, plan.business_date)] = plan.id

    def save_session(self, session: SessionRecord) -> None:
        self.sessions[session.id] = session
        self.session_by_plan[session.plan_id] = session.id

    def apply_attempt_evidence(self, attempt: AttemptRecord) -> None:
        """把一次复习作答写入 answer_history，并同步更新 knowledge_mastery。"""
        session = self.sessions.get(attempt.session_id)
        if not session:
            return
        student_id = session.student_id
        question = self.get_question(attempt.question_id)
        selected_text = question.options[attempt.selected_option] if attempt.selected_option < len(question.options) else ""

        conn = _get_db()
        try:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO answer_history (
                    answer_history_id, student_id, question_id, submit_type, submit_count,
                    ocr_question, student_ocr_answer, student_ocr_steps, is_correct,
                    judge_result, step_feedback, error_step_list, miss_step_list,
                    is_copy, core_error_type, confidence, submitted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.new_id("AH"),
                    student_id,
                    attempt.question_id,
                    "复习任务",
                    1,
                    question.prompt,
                    selected_text,
                    "",
                    1 if attempt.is_correct else 0,
                    "correct" if attempt.is_correct else "wrong",
                    "" if attempt.is_correct else "作答错误，请查看讲解并订正",
                    "[]",
                    "[]",
                    0,
                    "" if attempt.is_correct else "复习错误",
                    0.95 if attempt.is_correct else 0.80,
                    attempt.submitted_at.isoformat(),
                ),
            )

            for kw in question.knowledge:
                self._update_mastery(cur, student_id, kw.knowledge_point_id, attempt.is_correct)
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def _update_mastery(cur: sqlite3.Cursor, student_id: str, knowledge_id: str, is_correct: bool) -> None:
        cur.execute(
            """
            SELECT knowledge_mastery_id, correct_count, wrong_count, master_level, mastery_status
            FROM knowledge_mastery
            WHERE student_id = ? AND knowledge_id = ?
            """,
            (student_id, knowledge_id),
        )
        row = cur.fetchone()
        if row:
            km_id = row["knowledge_mastery_id"]
            correct_count = row["correct_count"] or 0
            wrong_count = row["wrong_count"] or 0
        else:
            km_id = f"KM-{uuid4().hex[:8].upper()}"
            correct_count = 0
            wrong_count = 0
            cur.execute(
                """
                INSERT INTO knowledge_mastery (
                    knowledge_mastery_id, student_id, knowledge_id,
                    mastery_status, correct_count, wrong_count, master_level
                ) VALUES (?, ?, ?, 'pending', 0, 0, 0.0)
                """,
                (km_id, student_id, knowledge_id),
            )

        if is_correct:
            correct_count += 1
            wrong_count = 0
        else:
            wrong_count += 1
            correct_count = 0

        if correct_count >= 2:
            master_level, mastery_status = 1.0, "mastered"
        elif wrong_count >= 2:
            master_level, mastery_status = 0.0, "weak"
        elif correct_count == 0 and wrong_count == 0:
            master_level, mastery_status = 0.0, "pending"
        else:
            total = correct_count + wrong_count
            master_level = round((correct_count * 0.5) / total, 2)
            mastery_status = "pending"

        cur.execute(
            """
            UPDATE knowledge_mastery
            SET correct_count = ?, wrong_count = ?, master_level = ?,
                mastery_status = ?, updated_at = ?
            WHERE knowledge_mastery_id = ?
            """,
            (correct_count, wrong_count, master_level, mastery_status, datetime.now().isoformat(), km_id),
        )


repository = ReviewRepository()
