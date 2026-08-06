# -*- coding: utf-8 -*-
"""零成本生成小学数学题库：模板 + Python 计算答案，写入 SQLite。

不使用 LLM：题干由生活化模板 + 随机数拼装，答案由程序算出，保证正确。
覆盖知识点与 knowledge 表 K 编号对应（人教版三年级）。

用法（仓库根目录）：
    python backend/database/generate_questions.py --count 20 --seed 42
可选：
    --count  生成题数（默认 20）
    --seed   随机种子，固定后可复现
    --dry-run 只打印不写入
"""
import argparse
import random
import sqlite3
import string
import sys

sys.path.insert(0, "backend/services")
from id_utils import generate_id


def two_digit_add_carry(rng):
    """K035 两位数加两位数（进位）：个位之和 >= 10。"""
    while True:
        a, b = rng.randint(16, 84), rng.randint(15, 83)
        if (a % 10) + (b % 10) >= 10:
            return a, b, a + b


def two_digit_add_no_carry(rng):
    """K034 两位数加两位数（不进位）：个位之和 < 10。"""
    while True:
        a, b = rng.randint(21, 73), rng.randint(11, 62)
        if (a % 10) + (b % 10) < 10:
            return a, b, a + b


def two_digit_sub_borrow(rng):
    """K037 两位数减两位数（退位）：个位不够减，且结果为正。"""
    while True:
        a, b = rng.randint(55, 98), rng.randint(26, 69)
        if (a % 10) < (b % 10) and a > b:
            return a, b, a - b


def two_digit_sub_no_borrow(rng):
    """K036 两位数减两位数（不退位）。"""
    while True:
        a, b = rng.randint(45, 95), rng.randint(12, 54)
        if (a % 10) >= (b % 10) and a > b:
            return a, b, a - b


def multi_digit_mul(rng):
    """K082 多位数乘一位数（进位）：两位数十位或个位乘后进位。"""
    while True:
        a, b = rng.randint(12, 98), rng.randint(2, 9)
        if a * b >= 100 or (a % 10) * b >= 10:
            return a, b, a * b


def rect_perimeter(rng):
    """K087 长方形周长。"""
    length, width = rng.randint(5, 15), rng.randint(3, 10)
    return length, width, 2 * (length + width)


def square_area(rng):
    """K105 正方形面积。"""
    side = rng.randint(4, 12)
    return side, None, side * side


TEMPLATES = [
    # (知识点, 名称, 模板函数, 题干构造)
    ("K035", "两位数加两位数（进位）", two_digit_add_carry,
     lambda a, b, ans: f"小明有{a}颗糖果，小红有{b}颗糖果，他们一共有多少颗糖果？", "颗", "计算题"),
    ("K035", "两位数加两位数（进位）", two_digit_add_carry,
     lambda a, b, ans: f"图书馆有{a}本故事书，又买来{b}本，现在一共有多少本？", "本", "计算题"),
    ("K035", "两位数加两位数（进位）", two_digit_add_carry,
     lambda a, b, ans: f"小华有{a}张邮票，小丽有{b}张邮票，他们两人一共有多少张邮票？", "张", "计算题"),
    ("K034", "两位数加两位数（不进位）", two_digit_add_no_carry,
     lambda a, b, ans: f"停车场有{a}辆汽车，又开进{b}辆，现在一共有多少辆？", "辆", "计算题"),
    ("K037", "两位数减两位数（退位）", two_digit_sub_borrow,
     lambda a, b, ans: f"书店有{a}本练习册，卖出{b}本，还剩多少本？", "本", "计算题"),
    ("K037", "两位数减两位数（退位）", two_digit_sub_borrow,
     lambda a, b, ans: f"食堂运来{a}千克大米，用去{b}千克，还剩多少千克？", "千克", "计算题"),
    ("K036", "两位数减两位数（不退位）", two_digit_sub_no_borrow,
     lambda a, b, ans: f"果园里有{a}棵桃树，砍掉了{b}棵，还剩多少棵？", "棵", "计算题"),
    ("K082", "多位数乘一位数（进位）", multi_digit_mul,
     lambda a, b, ans: f"每个盒子装了{a}个鸡蛋，有{b}盒，一共有多少个鸡蛋？", "个", "计算题"),
    ("K082", "多位数乘一位数（进位）", multi_digit_mul,
     lambda a, b, ans: f"学校买来{b}箱矿泉水，每箱有{a}瓶，一共有多少瓶？", "瓶", "计算题"),
    ("K087", "长方形周长", rect_perimeter,
     lambda a, b, ans: f"一个长方形的长是{a}厘米，宽是{b}厘米，它的周长是多少厘米？", "厘米", "应用题"),
    ("K105", "正方形面积", square_area,
     lambda a, b, ans: f"一个正方形的边长是{a}分米，它的面积是多少平方分米？", "平方分米", "应用题"),
]


def build_question(rng, template):
    kid, name, gen, stem_fn, unit, qtype = template
    a, b, ans = gen(rng)
    stem = stem_fn(a, b, ans)
    return {
        "knowledge_id": kid,
        "question_description": stem,
        "answer": f"{ans}{unit}" if unit else str(ans),
        "standard_solve_steps": f"先读清题意，找出已知条件；再列式计算；最后检查单位和结果。",
        "question_type": qtype,
        "difficulty": "medium",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    seen = set()
    questions = []
    attempts = 0
    while len(questions) < args.count and attempts < args.count * 20:
        attempts += 1
        template = rng.choice(TEMPLATES)
        q = build_question(rng, template)
        if q["question_description"] in seen:
            continue
        seen.add(q["question_description"])
        questions.append(q)

    print(f"生成 {len(questions)} 道题（尝试 {attempts} 次）")
    for q in questions[:3]:
        print(f"  [{q['knowledge_id']}] {q['question_description']} -> {q['answer']}")
    if len(questions) > 3:
        print(f"  … 共 {len(questions)} 道")
    if args.dry_run:
        return

    conn = sqlite3.connect("backend/database/example_db.db")
    conn.execute("PRAGMA foreign_keys = ON")
    existing = {r[0] for r in conn.execute("SELECT question_description FROM question").fetchall()}
    inserted = 0
    for q in questions:
        if q["question_description"] in existing:
            continue
        qid = "Q-" + "".join(rng.choices(string.ascii_uppercase + string.digits, k=8))
        conn.execute(
            "INSERT INTO question (question_id, question_description, question_type, difficulty, grade, textbook_version, standard_solve_steps, answer, created_at) "
            "VALUES (?, ?, ?, ?, '三年级', '人教版', ?, ?, datetime('now'))",
            (qid, q["question_description"], q["question_type"], q["difficulty"],
             q["standard_solve_steps"], q["answer"]),
        )
        conn.execute(
            "INSERT INTO question_knowledge_mapping (qkm_id, question_id, knowledge_id, mapping_weight) VALUES (?, ?, ?, 1.0)",
            (generate_id("QKM"), qid, q["knowledge_id"]),
        )
        existing.add(q["question_description"])
        inserted += 1
    conn.commit()
    conn.close()
    print(f"写入 {inserted} 道新题到题库")


if __name__ == "__main__":
    main()
