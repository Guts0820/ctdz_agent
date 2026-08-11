import sqlite3
import os
import csv

from backend.config import DATABASE_PATH, KNOWLEDGE_CSV_PATH

DATABASE = DATABASE_PATH
KNOWLEDGE_CSV = KNOWLEDGE_CSV_PATH

SCHEMA = '''
CREATE TABLE IF NOT EXISTS students (
    student_id VARCHAR(32) PRIMARY KEY,
    student_birthdate DATE,
    student_name VARCHAR(50),
    student_gender VARCHAR(10),
    student_school VARCHAR(100),
    student_class VARCHAR(50),
    student_grade VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS knowledge (
    knowledge_id VARCHAR(32) PRIMARY KEY,
    knowledge_scope VARCHAR(200),
    knowledge_name VARCHAR(100),
    grade VARCHAR(20),
    textbook_version VARCHAR(50),
    unit VARCHAR(50),
    prerequisite VARCHAR(32),
    next_knowledge VARCHAR(32),
    difficulty VARCHAR(20),
    is_core BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS error_bank (
    error_id VARCHAR(32) PRIMARY KEY,
    level1 VARCHAR(50),
    level2 VARCHAR(50),
    level3 VARCHAR(100),
    error_description TEXT,
    error_suggestion TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS question (
    question_id VARCHAR(32) PRIMARY KEY,
    question_description TEXT,
    question_type VARCHAR(50),
    difficulty VARCHAR(20),
    grade VARCHAR(20),
    textbook_version VARCHAR(50),
    standard_solve_steps TEXT,
    answer VARCHAR(200),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS question_knowledge_mapping (
    qkm_id VARCHAR(32) PRIMARY KEY,
    question_id VARCHAR(32),
    knowledge_id VARCHAR(32),
    mapping_weight FLOAT DEFAULT 1.0,
    FOREIGN KEY (question_id) REFERENCES question(question_id),
    FOREIGN KEY (knowledge_id) REFERENCES knowledge(knowledge_id)
);

CREATE TABLE IF NOT EXISTS answer_history (
    answer_history_id VARCHAR(32) PRIMARY KEY,
    student_id VARCHAR(32),
    question_id VARCHAR(32),
    submit_type VARCHAR(50),
    submit_count INTEGER DEFAULT 1,
    ocr_question TEXT,
    student_ocr_answer TEXT,
    student_ocr_steps TEXT,
    is_correct BOOLEAN DEFAULT 0,
    judge_result VARCHAR(50),
    step_feedback TEXT,
    error_step_list TEXT,
    miss_step_list TEXT,
    is_copy BOOLEAN DEFAULT 0,
    core_error_type VARCHAR(100),
    confidence FLOAT DEFAULT 0.0,
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (question_id) REFERENCES question(question_id)
);

CREATE TABLE IF NOT EXISTS mistake_case (
    mistake_case_id VARCHAR(32) PRIMARY KEY,
    student_id VARCHAR(32),
    question_id VARCHAR(32),
    current_status VARCHAR(50) DEFAULT 'correcting',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (question_id) REFERENCES question(question_id)
);

CREATE TABLE IF NOT EXISTS mistake_case_error (
    mce_id VARCHAR(32) PRIMARY KEY,
    mistake_case_id VARCHAR(32),
    error_id VARCHAR(32),
    error_weight FLOAT DEFAULT 1.0,
    FOREIGN KEY (mistake_case_id) REFERENCES mistake_case(mistake_case_id),
    FOREIGN KEY (error_id) REFERENCES error_bank(error_id)
);

CREATE TABLE IF NOT EXISTS mistake_case_knowledge (
    mck_id VARCHAR(32) PRIMARY KEY,
    mistake_case_id VARCHAR(32),
    knowledge_id VARCHAR(32),
    knowledge_weight FLOAT DEFAULT 1.0,
    FOREIGN KEY (mistake_case_id) REFERENCES mistake_case(mistake_case_id),
    FOREIGN KEY (knowledge_id) REFERENCES knowledge(knowledge_id)
);

CREATE TABLE IF NOT EXISTS teaching_content (
    teaching_content_id VARCHAR(32) PRIMARY KEY,
    mistake_case_id VARCHAR(32),
    explanation TEXT,
    hints TEXT,
    practice_list TEXT,
    reasoning_content TEXT,
    master_level FLOAT DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (mistake_case_id) REFERENCES mistake_case(mistake_case_id)
);

CREATE TABLE IF NOT EXISTS knowledge_mastery (
    knowledge_mastery_id VARCHAR(32) PRIMARY KEY,
    student_id VARCHAR(32),
    knowledge_id VARCHAR(32),
    mastery_status VARCHAR(50) DEFAULT 'pending',
    correct_count INTEGER DEFAULT 0,
    wrong_count INTEGER DEFAULT 0,
    master_level FLOAT DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (knowledge_id) REFERENCES knowledge(knowledge_id)
);

CREATE TABLE IF NOT EXISTS review_plan (
    review_plan_id VARCHAR(32) PRIMARY KEY,
    knowledge_mastery_id VARCHAR(32),
    review_stage VARCHAR(20),
    status VARCHAR(50) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY (knowledge_mastery_id) REFERENCES knowledge_mastery(knowledge_mastery_id)
);

CREATE TABLE IF NOT EXISTS push_record (
    push_record_id VARCHAR(32) PRIMARY KEY,
    review_plan_id VARCHAR(32),
    push_date DATE,
    push_stage VARCHAR(20),
    status VARCHAR(50) DEFAULT 'pending',
    pushed_at DATETIME,
    FOREIGN KEY (review_plan_id) REFERENCES review_plan(review_plan_id)
);

CREATE TABLE IF NOT EXISTS frequency_limit (
    frequency_limit_id VARCHAR(32) PRIMARY KEY,
    student_id VARCHAR(32),
    knowledge_id VARCHAR(32),
    daily_push_count INTEGER DEFAULT 0,
    weekly_push_count INTEGER DEFAULT 0,
    last_reset_date DATE,
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (knowledge_id) REFERENCES knowledge(knowledge_id)
);

-- 作业批次表（教师端批次管理与答案放行）
CREATE TABLE IF NOT EXISTS homework_batch (
    batch_id VARCHAR(32) PRIMARY KEY,
    class_id VARCHAR(32),
    teacher_id VARCHAR(32),
    batch_date DATE,
    release_status VARCHAR(20) DEFAULT 'locked',
    release_time DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 批次题目关联表
CREATE TABLE IF NOT EXISTS homework_batch_question (
    batch_id VARCHAR(32),
    question_id VARCHAR(32),
    PRIMARY KEY (batch_id, question_id),
    FOREIGN KEY (batch_id) REFERENCES homework_batch(batch_id),
    FOREIGN KEY (question_id) REFERENCES question(question_id)
);

-- 题目发布覆盖表（精细放行）
CREATE TABLE IF NOT EXISTS question_release_override (
    batch_id VARCHAR(32),
    question_id VARCHAR(32),
    released_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (batch_id, question_id),
    FOREIGN KEY (batch_id) REFERENCES homework_batch(batch_id),
    FOREIGN KEY (question_id) REFERENCES question(question_id)
);
'''

INITIAL_DATA = {
    # knowledge 主表统一由 knowledge_points.csv（K-* 编号）填充，
    # 此处不再提供旧 G-* 编号的种子数据，避免两套编号并存。
    'knowledge': [],
    'error_bank': [
        ('C-001', '计算', '口算与基本运算', '进位加法中十位漏加进位1', '在进位加法中，个位相加满十后，十位计算时忘记加上进位的1', '提醒学生标记进位，十位计算时先加进位'),
        ('C-002', '计算', '口算与基本运算', '退位减法中十位漏减退位1', '在退位减法中，个位不够减向十位借1后，十位计算时忘记减去借走的1', '提醒学生标记退位，十位计算时先减退位'),
        ('C-003', '计算', '口算与基本运算', '乘法口诀记忆错误或混淆', '乘法口诀记错或混淆了相近的口诀', '通过反复练习巩固乘法口诀，对比易混淆的口诀'),
        ('C-004', '计算', '口算与基本运算', '20以内加减法不熟练', '20以内加减法口算速度慢或正确率低', '加强20以内加减法口算练习，提高熟练度'),
        ('C-005', '计算', '竖式计算', '加法进位标记遗漏', '竖式加法中，个位满十后没有标记进位', '要求学生在竖式中清晰标记进位小1'),
        ('C-006', '计算', '竖式计算', '减法借位标记遗漏', '竖式减法中，个位不够减时没有标记借位', '要求学生在竖式中清晰标记借位点'),
        ('C-007', '计算', '竖式计算', '乘法竖式对齐错误', '乘法竖式中，部分积的数位对齐不正确', '强调数位对齐原则，多做竖式练习'),
        ('K-001', '概念', '定义混淆', '周长与面积混淆', '将周长和面积的概念混淆，误用公式', '通过实物操作区分周长和面积，明确公式适用场景'),
        ('K-002', '概念', '定义混淆', '因数与倍数混淆', '混淆因数和倍数的概念', '通过举例说明因数和倍数的关系'),
        ('K-003', '概念', '单位混淆', '长度单位换算错误', '长度单位之间换算时出错', '熟记长度单位换算关系，加强换算练习'),
        ('K-004', '概念', '单位混淆', '面积单位换算错误', '面积单位之间换算时出错', '熟记面积单位换算关系，注意平方关系'),
        ('R-001', '审题', '遗漏条件', '忽略单位换算', '题目中需要单位换算但没有进行换算', '提醒学生审题时注意单位是否统一'),
        ('R-002', '审题', '遗漏条件', '遗漏关键数字', '审题时漏掉了题目中的关键数字', '要求学生圈出题目中的关键数字'),
        ('R-003', '审题', '理解偏差', '多步问题只做一步', '需要多步计算的问题只完成了第一步', '引导学生分析题目要求，列出解题步骤'),
        ('R-004', '审题', '理解偏差', '问题理解错误', '对题目要求理解有误', '引导学生复述题目，确认理解正确'),
        ('M-001', '粗心', '抄错数字', '抄错数字', '将题目中的数字抄错', '要求学生检查抄写的数字是否与原题一致'),
        ('M-002', '粗心', '符号错误', '符号错误', '运算符号使用错误', '提醒学生看清运算符号')
    ],
    'students': [
        ('S-0001', '2018-09-01', '小明', '男', '阳光小学', '三年级(1)班', '三年级'),
        ('S-0002', '2018-06-15', '小红', '女', '阳光小学', '三年级(1)班', '三年级'),
        ('S-0003', '2017-12-20', '小刚', '男', '阳光小学', '四年级(2)班', '四年级')
    ],
    'question': [
        ('Q-0001', '小明有25颗糖果，小红有38颗糖果，他们一共有多少颗糖果？', '计算题', 'medium', '三年级', '人教版', '1. 相同数位对齐：25+38\n2. 个位相加：5+8=13，写3进1\n3. 十位相加：2+3+1=6\n4. 结果：63', '63'),
        ('Q-0002', '书架上有52本书，借出去28本，还剩多少本？', '计算题', 'medium', '三年级', '人教版', '1. 相同数位对齐：52-28\n2. 个位不够减：2-8不够减，借1得12-8=4\n3. 十位相减：5-1-2=2\n4. 结果：24', '24'),
        ('Q-0003', '一个长方形的长是8厘米，宽是5厘米，它的周长是多少厘米？', '应用题', 'medium', '三年级', '人教版', '1. 长方形周长公式：(长+宽)×2\n2. 代入数值：(8+5)×2\n3. 计算：13×2=26\n4. 结果：26厘米', '26厘米'),
        ('Q-0004', '一个正方形的边长是6分米，它的面积是多少平方分米？', '应用题', 'hard', '三年级', '人教版', '1. 正方形面积公式：边长×边长\n2. 代入数值：6×6\n3. 计算：36\n4. 结果：36平方分米', '36平方分米'),
        ('Q-0005', '学校买了24箱矿泉水，每箱有3瓶，一共买了多少瓶？', '计算题', 'hard', '三年级', '人教版', '1. 分析题目：求24个3是多少\n2. 乘法计算：24×3\n3. 分解计算：20×3=60，4×3=12\n4. 合并结果：60+12=72', '72')
    ],
    'question_knowledge_mapping': [
        ('QKM-001', 'Q-0001', 'K035', 1.0),  # 25+38 两位数加两位数（进位）
        ('QKM-002', 'Q-0002', 'K037', 1.0),  # 52-28 两位数减两位数（退位）
        ('QKM-003', 'Q-0003', 'K087', 1.0),  # 长方形周长
        ('QKM-004', 'Q-0004', 'K105', 1.0),  # 长方形/正方形面积
        ('QKM-005', 'Q-0005', 'K082', 1.0)   # 24×3 多位数乘一位数（进位）
    ]
}

def load_knowledge_from_csv():
    knowledge_data = []
    if os.path.exists(KNOWLEDGE_CSV):
        with open(KNOWLEDGE_CSV, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                semester = row.get('semester', '')
                unit = f"{row['grade']}年级{semester}" if semester else ''
                knowledge_data.append((
                    row['knowledge_point_id'],
                    row['description'],
                    row['description'],
                    row['grade'],
                    '人教版',
                    unit,
                    '',
                    '',
                    'medium',
                    1
                ))
    return knowledge_data

def init_database():
    os.makedirs(os.path.dirname(DATABASE), exist_ok=True)
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.executescript(SCHEMA)
    
    column_mappings = {
        'knowledge': '(knowledge_id, knowledge_scope, knowledge_name, grade, textbook_version, unit, prerequisite, next_knowledge, difficulty, is_core)',
        'error_bank': '(error_id, level1, level2, level3, error_description, error_suggestion)',
        'students': '(student_id, student_birthdate, student_name, student_gender, student_school, student_class, student_grade)',
        'question': '(question_id, question_description, question_type, difficulty, grade, textbook_version, standard_solve_steps, answer)',
        'question_knowledge_mapping': '(qkm_id, question_id, knowledge_id, mapping_weight)'
    }
    
    for table, data in INITIAL_DATA.items():
        if table == 'knowledge':
            csv_data = load_knowledge_from_csv()
            if csv_data:
                data = csv_data
                print(f"Loading knowledge from CSV: {len(data)} records")
        
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        if count == 0 and data:
            placeholders = ','.join(['?' for _ in data[0]])
            columns = column_mappings.get(table, '')
            cursor.executemany(f'INSERT INTO {table} {columns} VALUES ({placeholders})', data)
    
    conn.commit()
    conn.close()
    
    print(f"Database initialized successfully at {DATABASE}")
    print("Tables created: students, knowledge, error_bank, question, question_knowledge_mapping, answer_history, mistake_case, mistake_case_error, mistake_case_knowledge, teaching_content, knowledge_mastery, review_plan, push_record, frequency_limit")
    print("Initial data loaded for: knowledge(255+), error_bank(17), students(3), question(5), question_knowledge_mapping(5)")

if __name__ == "__main__":
    init_database()
