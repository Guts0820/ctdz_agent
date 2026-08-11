# -*- coding: utf-8 -*-
"""知识点编号迁移：把旧 G-N-* / G-C-* 编号统一到 K-* 编号体系。

背景：knowledge 主表始终由 knowledge_points.csv（K 编号）填充，但早期
question_knowledge_mapping / knowledge_mastery / frequency_limit 仍残留
Neo4j 时代的 G-* 编号，形成悬空引用。本脚本做一次性数据迁移，幂等可重复执行。

运行（在仓库根目录）：
    python backend/database/migrate_gn_to_k.py
"""
import os
import sqlite3

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_PATH = os.path.join(REPO_ROOT, "backend", "database", "example_db.db")

GN_TO_K = {
    "G-N-2-005": "K035",  # 100以内进位加法 -> 两位数加两位数（进位）
    "G-N-2-006": "K037",  # 100以内退位减法 -> 两位数减两位数（退位）
    "G-N-3-003": "K082",  # 两位数乘一位数 -> 多位数乘一位数（笔算乘法进位）
    "G-C-3-001": "K087",  # 长方形和正方形的周长
    "G-C-3-002": "K105",  # 长方形和正方形的面积
    "G-N-1-001": "K252",  # 数与代数
}


def migrate() -> int:
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    total = 0

    # 1) 题目-知识点映射
    for old, new in GN_TO_K.items():
        cur.execute(
            "UPDATE question_knowledge_mapping SET knowledge_id=? WHERE knowledge_id=?",
            (new, old),
        )
        total += cur.rowcount

    # 2) 掌握度：改 knowledge_id，并把主键里的 G-* 段一并替换，
    #    同时级联更新引用它的复习计划外键
    rows = cur.execute(
        "SELECT knowledge_mastery_id, knowledge_id FROM knowledge_mastery "
        "WHERE knowledge_id LIKE 'G-N-%' OR knowledge_id LIKE 'G-C-%'"
    ).fetchall()
    for mid, kid in rows:
        new = GN_TO_K.get(kid)
        if not new:
            print(f"跳过未知旧编号: {kid} ({mid})")
            continue
        new_mid = mid.replace(kid, new)
        cur.execute(
            "UPDATE knowledge_mastery SET knowledge_mastery_id=?, knowledge_id=? "
            "WHERE knowledge_mastery_id=?",
            (new_mid, new, mid),
        )
        total += cur.rowcount
        cur.execute(
            "UPDATE review_plan SET knowledge_mastery_id=? WHERE knowledge_mastery_id=?",
            (new_mid, mid),
        )
        total += cur.rowcount

    # 3) 频控记录
    for old, new in GN_TO_K.items():
        cur.execute(
            "UPDATE frequency_limit SET knowledge_id=? WHERE knowledge_id=?",
            (new, old),
        )
        total += cur.rowcount

    conn.commit()
    conn.close()
    return total


if __name__ == "__main__":
    print(f"数据库: {DATABASE_PATH}")
    affected = migrate()
    print(f"迁移完成，共影响 {affected} 行（重复执行应为 0）。")
