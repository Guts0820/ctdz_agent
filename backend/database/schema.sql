CREATE TABLE students (
    student_id VARCHAR(32) PRIMARY KEY COMMENT '学生id',
    student_birthdate DATE COMMENT '学生出生年月日',
    student_name VARCHAR(50) COMMENT '学生名字',
    student_gender VARCHAR(10) COMMENT '学生性别',
    student_school VARCHAR(100) COMMENT '学生就读学校',
    student_class VARCHAR(50) COMMENT '学生就读班级',
    student_grade VARCHAR(20) COMMENT '学生年级',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建日期',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日期'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生表';

CREATE TABLE knowledge (
    knowledge_id VARCHAR(32) PRIMARY KEY COMMENT '知识点id',
    parent_id VARCHAR(32) COMMENT '父知识点id',
    knowledge_scope VARCHAR(200) COMMENT '知识点描述',
    knowledge_grade VARCHAR(20) COMMENT '知识点年级',
    textbook_version VARCHAR(50) COMMENT '教材版本',
    unit VARCHAR(100) COMMENT '单元',
    prerequisite VARCHAR(32) COMMENT '先修知识点',
    next_knowledge VARCHAR(32) COMMENT '后续知识点',
    explanation TEXT COMMENT '知识点解释',
    common_errors TEXT COMMENT '常见错误',
    forbidden_explanation TEXT COMMENT '禁止讲解内容',
    example TEXT COMMENT '示例',
    teaching_tips TEXT COMMENT '教学提示',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建日期',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日期'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识点表';

CREATE TABLE error_bank (
    error_id VARCHAR(32) PRIMARY KEY COMMENT '错因id',
    level1 VARCHAR(50) COMMENT '一级描述',
    level2 VARCHAR(100) COMMENT '二级描述',
    level3 VARCHAR(200) COMMENT '三级描述',
    typical_example TEXT COMMENT '典型错误示例',
    ai_prompt TEXT COMMENT 'AI识别提示（Prompt）',
    applicable_grade VARCHAR(50) COMMENT '适用学段',
    knowledge_scope VARCHAR(200) COMMENT '知识点范围',
    judgment_criteria TEXT COMMENT '判定标准',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建日期',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新日期'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='错因库';

CREATE TABLE question (
    question_id VARCHAR(32) PRIMARY KEY COMMENT '题目id',
    question_description TEXT COMMENT '题目描述',
    question_answer TEXT COMMENT '题目答案',
    question_difficulty VARCHAR(20) COMMENT '题目难度',
    question_grade VARCHAR(20) COMMENT '题目年级',
    standard_solve_steps TEXT COMMENT '标准解题步骤',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '题目上传日期'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='题目表';

CREATE TABLE question_knowledge_mapping (
    question_id VARCHAR(32) COMMENT '题目id',
    knowledge_id VARCHAR(32) COMMENT '知识点id',
    knowledge_weight DECIMAL(5,2) DEFAULT 1.00 COMMENT '知识点占比',
    PRIMARY KEY (question_id, knowledge_id),
    FOREIGN KEY (question_id) REFERENCES question(question_id),
    FOREIGN KEY (knowledge_id) REFERENCES knowledge(knowledge_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='题目知识点关系表';

CREATE TABLE mistake_case (
    mistake_case_id VARCHAR(32) PRIMARY KEY COMMENT '错题案例id',
    student_id VARCHAR(32) COMMENT '学生id',
    question_id VARCHAR(32) COMMENT '题目id',
    current_status VARCHAR(20) DEFAULT 'correcting' COMMENT '当前状态（订正中/已掌握）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (question_id) REFERENCES question(question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='错题案例表';

CREATE TABLE mistake_case_knowledge (
    mistake_case_id VARCHAR(32) COMMENT '错题案例id',
    knowledge_id VARCHAR(32) COMMENT '做错知识点id',
    knowledge_weight DECIMAL(5,2) DEFAULT 1.00 COMMENT '知识点权重',
    PRIMARY KEY (mistake_case_id, knowledge_id),
    FOREIGN KEY (mistake_case_id) REFERENCES mistake_case(mistake_case_id),
    FOREIGN KEY (knowledge_id) REFERENCES knowledge(knowledge_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='错题案例知识点关联表';

CREATE TABLE mistake_case_error (
    mistake_case_id VARCHAR(32) COMMENT '错题案例id',
    error_id VARCHAR(32) COMMENT '错因id',
    error_weight DECIMAL(5,2) DEFAULT 1.00 COMMENT '错因权重',
    PRIMARY KEY (mistake_case_id, error_id),
    FOREIGN KEY (mistake_case_id) REFERENCES mistake_case(mistake_case_id),
    FOREIGN KEY (error_id) REFERENCES error_bank(error_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='错题案例错因关联表';

CREATE TABLE answer_history (
    answer_history_id VARCHAR(32) PRIMARY KEY COMMENT '作答历史id',
    student_id VARCHAR(32) COMMENT '学生id',
    question_id VARCHAR(32) COMMENT '题目id',
    mistake_case_id VARCHAR(32) COMMENT '错题案例id',
    review_plan_id VARCHAR(32) COMMENT '复习计划id',
    submit_type VARCHAR(30) COMMENT '提交类型（首次错题/错题订正/平台推送/Day1/Day3/Day7）',
    submit_count INT DEFAULT 1 COMMENT '第几次提交',
    original_image_url VARCHAR(500) COMMENT '原始图片URL',
    ocr_question TEXT COMMENT 'OCR题目',
    student_ocr_answer TEXT COMMENT '学生ocr答案',
    student_ocr_steps TEXT COMMENT '学生ocr步骤',
    is_correct TINYINT(1) DEFAULT 0 COMMENT '是否正确',
    judge_result VARCHAR(30) COMMENT '判定结果',
    step_feedback TEXT COMMENT '步骤反馈',
    error_step_list TEXT COMMENT '错误步骤列表',
    miss_step_list TEXT COMMENT '缺失步骤列表',
    is_copy TINYINT(1) DEFAULT 0 COMMENT '是否抄袭',
    core_error_type VARCHAR(100) COMMENT '核心错误类型',
    confidence DECIMAL(5,2) DEFAULT 0.00 COMMENT '置信度',
    error_tags TEXT COMMENT '错因标签',
    reasoning_content TEXT COMMENT '推理内容',
    submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '提交时间',
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (question_id) REFERENCES question(question_id),
    FOREIGN KEY (mistake_case_id) REFERENCES mistake_case(mistake_case_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='作答历史表';

CREATE TABLE knowledge_mastery (
    knowledge_mastery_id VARCHAR(32) PRIMARY KEY COMMENT '知识点掌握id',
    student_id VARCHAR(32) COMMENT '学生id',
    knowledge_id VARCHAR(32) COMMENT '知识点id',
    mastery_status VARCHAR(20) DEFAULT 'pending' COMMENT '掌握情况（薄弱/待提高/已掌握）',
    correct_count INT DEFAULT 0 COMMENT '连续答对次数',
    wrong_count INT DEFAULT 0 COMMENT '连续答错次数',
    master_level DECIMAL(5,2) DEFAULT 0.00 COMMENT '掌握度',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创造日期',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (knowledge_id) REFERENCES knowledge(knowledge_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='知识点掌握表';

CREATE TABLE review_plan (
    review_plan_id VARCHAR(32) PRIMARY KEY COMMENT '复习计划id',
    knowledge_mastery_id VARCHAR(32) COMMENT '知识点掌握id',
    review_stage VARCHAR(20) COMMENT '复习阶段（Day1/Day3/Day7）',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态（待推送/推送中/已完成/已取消）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创造日期',
    completed_at DATETIME COMMENT '完成日期',
    FOREIGN KEY (knowledge_mastery_id) REFERENCES knowledge_mastery(knowledge_mastery_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='复习计划表';

CREATE TABLE push_record (
    push_record_id VARCHAR(32) PRIMARY KEY COMMENT '推送记录id',
    review_plan_id VARCHAR(32) COMMENT '复习计划id',
    push_date DATE COMMENT '推送日期',
    push_stage VARCHAR(20) COMMENT '推送阶段(day1/3/7)',
    push_question_id VARCHAR(32) COMMENT '推送题目id',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '状态（待推送/已推送/已完成/已取消）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建日期',
    FOREIGN KEY (review_plan_id) REFERENCES review_plan(review_plan_id),
    FOREIGN KEY (push_question_id) REFERENCES question(question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='推送记录表';

CREATE TABLE teaching_content (
    teaching_content_id VARCHAR(32) PRIMARY KEY COMMENT '教学内容id',
    mistake_case_id VARCHAR(32) COMMENT '错题案例id',
    explanation TEXT COMMENT '讲解内容',
    hints TEXT COMMENT '引导提示',
    practice_list TEXT COMMENT '练习题列表',
    reasoning_content TEXT COMMENT '推理内容',
    master_level DECIMAL(5,2) COMMENT '掌握度',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建日期',
    FOREIGN KEY (mistake_case_id) REFERENCES mistake_case(mistake_case_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教学内容表';

CREATE TABLE frequency_limit (
    frequency_limit_id VARCHAR(32) PRIMARY KEY COMMENT '频次限制id',
    student_id VARCHAR(32) COMMENT '学生id',
    knowledge_id VARCHAR(32) COMMENT '知识点id',
    daily_push_count INT DEFAULT 0 COMMENT '当日推送次数',
    weekly_push_count INT DEFAULT 0 COMMENT '本周推送次数',
    daily_limit INT DEFAULT 5 COMMENT '单日推送上限',
    weekly_limit INT DEFAULT 3 COMMENT '单知识点周推送上限',
    last_reset_date DATE COMMENT '上次重置日期',
    FOREIGN KEY (student_id) REFERENCES students(student_id),
    FOREIGN KEY (knowledge_id) REFERENCES knowledge(knowledge_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='频次限制表';