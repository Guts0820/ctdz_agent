"""初始化 Insight 相关数据：用户账号库建表 + 演示数据（可重复执行）。"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.user_database import user_db


def main():
    user_db.connect()

    user = user_db.get_user("test_student")
    if not user:
        user_id = user_db.insert_user("test_student", "123456", grade=5, semester="上册")
        print(f"创建演示用户 test_student，user_id={user_id}")
    else:
        user_id = user["id"]
        print(f"演示用户已存在，user_id={user_id}")

    # 学习进度（知识点使用主库 knowledge 表中真实存在的 K 编号）
    demo_progress = [
        ("K035", 85, 17, 3),
        ("K037", 70, 14, 6),
        ("K082", 90, 18, 2),
        ("K087", 60, 12, 8),
        ("K105", 45, 9, 11),
        ("K068", 55, 11, 9),
        ("K069", 80, 16, 4),
        ("K070", 75, 15, 5),
        ("K074", 65, 13, 7),
        ("K076", 50, 10, 10),
        ("K079", 78, 15, 5),
        ("K081", 40, 8, 12),
        ("K083", 88, 17, 3),
        ("K084", 35, 7, 13),
        ("K086", 92, 18, 2),
    ]
    for kid, mastery, correct, wrong in demo_progress:
        user_db.execute(
            """
            INSERT OR REPLACE INTO learning_progress
            (user_id, knowledge_id, mastery_level, correct_count, wrong_count)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, kid, mastery, correct, wrong),
        )
    print(f"写入学习进度 {len(demo_progress)} 条")

    user_db.execute(
        """
        INSERT OR REPLACE INTO wrong_question
        (user_id, question_id, wrong_answer, wrong_count, reviewed)
        VALUES (?, 'Q-0001', '25+38=53', 3, 0)
        """,
        (user_id,),
    )
    user_db.execute(
        """
        INSERT OR REPLACE INTO wrong_question
        (user_id, question_id, wrong_answer, wrong_count, reviewed)
        VALUES (?, 'Q-0003', '周长=40厘米', 2, 1)
        """,
        (user_id,),
    )
    user_db.execute(
        """
        INSERT OR REPLACE INTO answer_record
        (user_id, question_id, answer, is_correct, time_spent)
        VALUES (?, 'Q-0002', '24', 1, 30)
        """,
        (user_id,),
    )
    user_db.execute(
        """
        INSERT OR REPLACE INTO answer_record
        (user_id, question_id, answer, is_correct, time_spent)
        VALUES (?, 'Q-0004', '36平方分米', 1, 45)
        """,
        (user_id,),
    )
    user_db.execute(
        """
        INSERT OR REPLACE INTO answer_record
        (user_id, question_id, answer, is_correct, time_spent)
        VALUES (?, 'Q-0005', '70', 0, 20)
        """,
        (user_id,),
    )
    print("写入错题本 / 答题记录演示数据完成")

    # 复习引擎演示：给 S-0001 补齐与题库映射一致的掌握度记录（G-N-* 编号）
    import sqlite3
    from backend.config import DATABASE_PATH
    conn = sqlite3.connect(DATABASE_PATH)
    cur = conn.cursor()
    demo_mastery = [
        ("G-N-2-005", "pending", 1, 3, 0.4),   # 100以内进位加法（弱）
        ("G-N-2-006", "pending", 2, 1, 0.6),   # 100以内退位减法（中）
        ("G-C-3-001", "pending", 1, 2, 0.5),   # 周长（弱）
        ("G-C-3-002", "pending", 3, 0, 0.8),   # 面积（较好）
        ("G-N-3-003", "pending", 2, 1, 0.7),   # 两位数乘法（中）
    ]
    for kid, status, correct, wrong, level in demo_mastery:
        cur.execute(
            "SELECT knowledge_mastery_id FROM knowledge_mastery WHERE student_id='S-0001' AND knowledge_id=?",
            (kid,),
        )
        row = cur.fetchone()
        if row:
            cur.execute(
                """
                UPDATE knowledge_mastery
                SET mastery_status=?, correct_count=?, wrong_count=?, master_level=?, updated_at=datetime('now')
                WHERE knowledge_mastery_id=?
                """,
                (status, correct, wrong, level, row[0]),
            )
        else:
            cur.execute(
                """
                INSERT INTO knowledge_mastery
                (knowledge_mastery_id, student_id, knowledge_id, mastery_status,
                 correct_count, wrong_count, master_level, created_at, updated_at)
                VALUES (?, 'S-0001', ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """,
                (f"KM-DEMO-{kid}", kid, status, correct, wrong, level),
            )
    conn.commit()
    conn.close()
    print("补齐复习引擎演示掌握度记录 5 条（S-0001 × G-N-*）")


if __name__ == "__main__":
    main()
