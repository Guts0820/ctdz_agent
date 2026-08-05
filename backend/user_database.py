"""用户账号与学习数据存储层（移植自同事 D:/backend/user_database.py）。

数据存于仓库根目录的 backend/user_data.db，与主业务库（example_db.db）分离：
- user             用户账号（注册/登录）
- wrong_question   错题本
- learning_progress 学习进度（掌握度、对错次数）
- answer_record    答题记录
"""

import sqlite3
import os

from backend.config import get_env


DATABASE_PATH = get_env("USER_DATABASE_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_data.db"))


class UserDatabase:
    def __init__(self):
        pass

    def _get_connection(self):
        conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self, conn):
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                grade INTEGER,
                semester TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wrong_question (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                wrong_answer TEXT,
                error_cause_id TEXT,
                wrong_count INTEGER DEFAULT 1,
                last_wrong_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed BOOLEAN DEFAULT 0,
                reviewed_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user(id),
                UNIQUE(user_id, question_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                knowledge_id TEXT NOT NULL,
                mastery_level INTEGER DEFAULT 0,
                correct_count INTEGER DEFAULT 0,
                wrong_count INTEGER DEFAULT 0,
                last_practice_time TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user(id),
                UNIQUE(user_id, knowledge_id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS answer_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                question_id TEXT NOT NULL,
                answer TEXT NOT NULL,
                is_correct BOOLEAN NOT NULL,
                time_spent INTEGER,
                answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user(id)
            )
        """)

        conn.commit()
        cursor.close()

    def connect(self):
        conn = self._get_connection()
        self._create_tables(conn)
        conn.close()

    def close(self):
        pass

    def query(self, sql, params=None):
        if params is None:
            params = ()
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            result = cursor.fetchall()
            cursor.close()
            return result
        finally:
            conn.close()

    def execute(self, sql, params=None):
        if params is None:
            params = ()
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            lastrowid = cursor.lastrowid
            cursor.close()
            return lastrowid
        finally:
            conn.close()

    def insert_user(self, username, password, grade=None, semester=None):
        try:
            return self.execute("""
                INSERT INTO user (username, password, grade, semester)
                VALUES (?, ?, ?, ?)
            """, (username, password, grade, semester))
        except sqlite3.IntegrityError:
            return None

    def get_user(self, username):
        result = self.query("SELECT * FROM user WHERE username = ?", (username,))
        return dict(result[0]) if result else None

    def get_user_by_id(self, user_id):
        result = self.query("SELECT * FROM user WHERE id = ?", (user_id,))
        return dict(result[0]) if result else None

    def add_wrong_question(self, user_id, question_id, wrong_answer=None, error_cause_id=None):
        result = self.query("""
            SELECT id, wrong_count FROM wrong_question
            WHERE user_id = ? AND question_id = ?
        """, (user_id, question_id))

        if result:
            wrong_count = result[0]["wrong_count"] + 1
            self.execute("""
                UPDATE wrong_question
                SET wrong_count = ?, last_wrong_time = CURRENT_TIMESTAMP,
                    wrong_answer = ?, error_cause_id = ?, reviewed = 0
                WHERE id = ?
            """, (wrong_count, wrong_answer, error_cause_id, result[0]["id"]))
            return result[0]["id"]
        else:
            return self.execute("""
                INSERT INTO wrong_question (user_id, question_id, wrong_answer, error_cause_id)
                VALUES (?, ?, ?, ?)
            """, (user_id, question_id, wrong_answer, error_cause_id))

    def get_wrong_questions(self, user_id):
        result = self.query("""
            SELECT * FROM wrong_question
            WHERE user_id = ? ORDER BY last_wrong_time DESC
        """, (user_id,))
        return [dict(row) for row in result]

    def mark_wrong_question_reviewed(self, user_id, question_id):
        self.execute("""
            UPDATE wrong_question
            SET reviewed = 1, reviewed_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND question_id = ?
        """, (user_id, question_id))

    def update_learning_progress(self, user_id, knowledge_id, is_correct):
        result = self.query("""
            SELECT * FROM learning_progress
            WHERE user_id = ? AND knowledge_id = ?
        """, (user_id, knowledge_id))

        if result:
            correct_count = result[0]["correct_count"] + (1 if is_correct else 0)
            wrong_count = result[0]["wrong_count"] + (0 if is_correct else 1)
            total = correct_count + wrong_count
            mastery_level = round((correct_count / total) * 100) if total > 0 else 0

            self.execute("""
                UPDATE learning_progress
                SET correct_count = ?, wrong_count = ?, mastery_level = ?,
                    last_practice_time = CURRENT_TIMESTAMP
                WHERE user_id = ? AND knowledge_id = ?
            """, (correct_count, wrong_count, mastery_level, user_id, knowledge_id))
        else:
            correct_count = 1 if is_correct else 0
            wrong_count = 0 if is_correct else 1
            mastery_level = 100 if is_correct else 0

            self.execute("""
                INSERT INTO learning_progress
                (user_id, knowledge_id, correct_count, wrong_count, mastery_level)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, knowledge_id, correct_count, wrong_count, mastery_level))

    def get_learning_progress(self, user_id):
        result = self.query("""
            SELECT * FROM learning_progress
            WHERE user_id = ? ORDER BY mastery_level ASC
        """, (user_id,))
        return [dict(row) for row in result]

    def get_weak_knowledge_points(self, user_id, threshold=60):
        result = self.query("""
            SELECT * FROM learning_progress
            WHERE user_id = ? AND mastery_level < ?
            ORDER BY mastery_level ASC
        """, (user_id, threshold))
        return [dict(row) for row in result]

    def add_answer_record(self, user_id, question_id, answer, is_correct, time_spent=None):
        return self.execute("""
            INSERT INTO answer_record (user_id, question_id, answer, is_correct, time_spent)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, question_id, answer, is_correct, time_spent))

    def get_answer_records(self, user_id, limit=100):
        result = self.query("""
            SELECT * FROM answer_record
            WHERE user_id = ? ORDER BY answered_at DESC LIMIT ?
        """, (user_id, limit))
        return [dict(row) for row in result]


user_db = UserDatabase()
