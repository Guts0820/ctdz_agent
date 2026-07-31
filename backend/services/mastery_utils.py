"""
Mastery + Priority 双模型计算（移植自 eduagent priority_calculator）

Mastery（回答"学生会不会"）：四维加权 + 可信度修正
Priority（回答"优先复习哪个"）：五因子加权动态排序
"""

import math
from datetime import date, datetime, timedelta

RECENCY_DECAY = 0.85


def clip(value: float, minimum: float = 0, maximum: float = 100) -> float:
    return min(maximum, max(minimum, value))


def weighted_rate(results: list[bool], limit: int = 10) -> float:
    """时间衰减加权正确率：越近的作答权重越高"""
    recent = results[-limit:]
    if not recent:
        return 50.0
    size = len(recent)
    weights = [RECENCY_DECAY ** (size - i - 1) for i in range(size)]
    return 100 * sum(w * int(r) for w, r in zip(weights, recent)) / sum(weights)


def volatility(results: list[bool], limit: int = 10) -> float:
    """波动率：相邻两次结果翻转的频率"""
    recent = results[-limit:]
    if len(recent) < 2:
        return 0.0
    changes = sum(cur != prev for prev, cur in zip(recent, recent[1:]))
    return changes / (len(recent) - 1)


def weighted_error_severity(severities: list[float], limit: int = 5) -> float:
    """时间衰减加权错因严重度"""
    recent = severities[-limit:]
    if not recent:
        return 0.0
    size = len(recent)
    weights = [RECENCY_DECAY ** (size - i - 1) for i in range(size)]
    return 100 * sum(w * s for w, s in zip(weights, recent)) / sum(weights)


def trend_risk(results: list[bool]) -> float:
    """学习趋势：近期正确率 - 远期正确率（>50=退步，<50=进步）"""
    recent = results[-10:]
    if len(recent) < 4:
        return 50.0
    split = len(recent) // 2
    older_rate = 100 * sum(recent[:split]) / len(recent[:split])
    newer_rate = 100 * sum(recent[split:]) / len(recent[split:])
    return clip(50 + older_rate - newer_rate)


def calculate_advanced(
    student_id: int,
    knowledge_point_id: str,
    evidence: list[dict],          # [{is_correct, occurred_at, error_severity}, ...]
    importance: float = 50.0,      # 知识点重要程度 0-100
) -> dict:
    """
    返回完整 Mastery + Priority 结果

    evidence 中 error_severity 取值范围 0-1，错题时有效
    """
    evidence = sorted(evidence, key=lambda e: e["occurred_at"])
    results = [e["is_correct"] for e in evidence]
    severities = [e["error_severity"] for e in evidence
                  if not e["is_correct"] and e.get("error_severity") is not None]

    correct_count = sum(results)
    wrong_count = len(results) - correct_count
    total = len(results)

    # ---- 连续对错计数 ----
    correct_streak = 0
    wrong_streak = 0
    for r in reversed(results):
        if r:
            if wrong_streak == 0:
                correct_streak += 1
            else:
                break
        else:
            if correct_streak == 0:
                wrong_streak += 1
            else:
                break

    now = datetime.now()

    # === Mastery 四维 ===

    # 1. Accuracy (40%)  —— 历史正确率 + 近期加权正确率
    history_accuracy = 100 * (correct_count + 2) / (total + 4) if total > 0 else 50.0
    recent_accuracy = weighted_rate(results)
    accuracy = 50.0 if total == 0 else 0.3 * history_accuracy + 0.7 * recent_accuracy

    # 2. Consistency (25%) —— 稳定性（波动率 + 连对/连错修正）
    result_volatility = volatility(results)
    consistency = clip(
        recent_accuracy * (1 - 0.3 * result_volatility)
        + 3 * correct_streak
        - 8 * wrong_streak
    )

    # 3. Retention (20%) —— 记忆保持度（指数衰减）
    stability_days = clip(
        7 + 0.15 * accuracy + 2 * correct_streak - 3 * wrong_streak,
        5, 60
    )
    correct_times = [e["occurred_at"] for e in evidence if e["is_correct"]]
    if correct_times:
        days_since_correct = max(0.0, (now - correct_times[-1]).total_seconds() / 86400)
        retention = 100 * math.exp(-days_since_correct / stability_days)
    else:
        retention = 0.0

    # 4. Error Control (15%) —— 错误控制力（错因严重度反向指标）
    error_severity_score = weighted_error_severity(severities)
    error_control = clip(100 - error_severity_score - 8 * wrong_streak)

    # 可信度修正：数据少时向 50 分收缩
    raw_mastery = 0.4 * accuracy + 0.25 * consistency + 0.2 * retention + 0.15 * error_control
    confidence = 1 - math.exp(-total / 5) if total > 0 else 0
    mastery = confidence * raw_mastery + (1 - confidence) * 50

    # === Priority 五因子 ===

    skill_mastery = 0.5 * accuracy + 0.3 * consistency + 0.2 * error_control
    skill_gap = 100 - skill_mastery

    latest_is_wrong = bool(evidence and not evidence[-1]["is_correct"])
    forgetting_risk = clip(
        100 - retention + (10 if latest_is_wrong else 0) + 5 * min(wrong_streak, 3)
    ) if correct_times else 0.0

    trend = trend_risk(results)

    priority = clip(
        0.35 * skill_gap
        + 0.25 * error_severity_score
        + 0.20 * forgetting_risk
        + 0.10 * importance
        + 0.10 * trend
    )

    # 掌握状态判定
    if mastery >= 85:
        mastery_status = "mastered"
    elif mastery < 40:
        mastery_status = "weak"
    else:
        mastery_status = "pending"

    return {
        "mastery": round(mastery, 2),
        "mastery_status": mastery_status,
        "confidence": round(confidence, 4),
        "components": {
            "accuracy": round(accuracy, 2),
            "consistency": round(consistency, 2),
            "retention": round(retention, 2),
            "error_control": round(error_control, 2),
            "raw_mastery": round(raw_mastery, 2),
        },
        "priority": round(priority, 2),
        "priority_components": {
            "skill_gap": round(skill_gap, 2),
            "error_severity": round(error_severity_score, 2),
            "forgetting_risk": round(forgetting_risk, 2),
            "importance": round(importance, 2),
            "trend": round(trend, 2),
        },
        "correct_streak": correct_streak,
        "wrong_streak": wrong_streak,
        "stability_days": round(stability_days, 2),
    }


def calculate_mastery(correct_count: int, wrong_count: int) -> tuple:
    """保留旧接口兼容性"""
    if correct_count >= 2:
        return 1.00, "mastered"
    elif wrong_count >= 2:
        return 0.00, "weak"
    elif correct_count == 0 and wrong_count == 0:
        return 0.00, "pending"
    else:
        total = correct_count + wrong_count
        master_level = (correct_count * 0.5) / total
        return round(master_level, 2), "pending"


def load_evidence(student_id: str, knowledge_id: str, db_path: str) -> list[dict]:
    """从 answer_history 表加载作答证据"""
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 通过 question_knowledge_mapping 找到该知识点下的所有题目
    cursor.execute('''
        SELECT ah.is_correct, ah.submitted_at, ah.core_error_type
        FROM answer_history ah
        JOIN question_knowledge_mapping qkm ON ah.question_id = qkm.question_id
        WHERE ah.student_id = ? AND qkm.knowledge_id = ?
        ORDER BY ah.submitted_at
    ''', (student_id, knowledge_id))
    rows = cursor.fetchall()

    evidence = []
    for row in rows:
        occurred_at = datetime.fromisoformat(row["submitted_at"]) if row["submitted_at"] else datetime.now()
        # 错因严重度映射
        severity_map = {
            "计算失误": 0.6, "概念混淆": 0.8, "审题错误": 0.5,
            "粗心": 0.3, "疑似抄袭": 0.9, "未作答": 0.2, "未知": 0.5, "": 0.5,
        }
        error_severity = severity_map.get(row["core_error_type"] or "", 0.5) if not row["is_correct"] else None

        evidence.append({
            "is_correct": bool(row["is_correct"]),
            "occurred_at": occurred_at,
            "error_severity": error_severity,
        })

    conn.close()
    return evidence
