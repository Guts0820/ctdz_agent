# AI小学数学错题订正系统 - REST API 端点定义

## 基础路径
所有端点前缀: `/api/v1`

---

## 一、学生端 API

### 1.1 提交作业（核心入口）

**POST** `/api/v1/submit`

请求体:
```json
{
    "student_id": "S-0001",
    "image": "base64_encoded_image",
    "original_question": "题目文本（可选，OCR失败时使用）",
    "student_write": "学生作答文本（可选，OCR失败时使用）",
    "grade": "三年级"
}
```

响应体:
```json
{
    "status": "success",
    "data": {
        "judge_result": "correct/wrong/copy_warning",
        "step_feedback": "步骤级反馈",
        "error_step_list": ["步骤1错误", "步骤3错误"],
        "miss_step_list": ["缺少单位换算步骤"],
        "is_copy": false,
        "core_error_type": "计算失误",
        "confidence": 0.85,
        "error_tags": [
            {"error_id": "C-001", "level1": "计算", "level2": "口算与基本运算", "level3": "进位加法中十位漏加进位1"}
        ],
        "knowledge_id": "G-N-3-001",
        "knowledge_scope": "两位数加两位数进位加法",
        "explanation": "知识点讲解内容",
        "hints": ["提示1", "提示2"],
        "practice_list": [
            {"question_id": "Q-001", "question_description": "变式题1", "difficulty": "medium"}
        ],
        "master_level": 0.65,
        "next_action": "practice",
        "correct_count": 1,
        "wrong_count": 0
    }
}
```

### 1.2 获取错题列表

**GET** `/api/v1/student/{student_id}/mistakes`

查询参数:
- `status`: correcting/ mastered (可选)
- `page`: 页码，默认1
- `page_size`: 每页数量，默认10

响应体:
```json
{
    "status": "success",
    "data": {
        "total": 25,
        "list": [
            {
                "mistake_case_id": "MC-001",
                "question_id": "Q-001",
                "question_description": "题目描述",
                "knowledge_scope": "两位数加两位数",
                "current_status": "correcting",
                "created_at": "2024-01-15 10:30:00"
            }
        ]
    }
}
```

### 1.3 获取复习任务

**GET** `/api/v1/student/{student_id}/review`

查询参数:
- `stage`: day1/day3/day7/all (可选)
- `status`: pending/completed/cancelled (可选)

响应体:
```json
{
    "status": "success",
    "data": {
        "today_review_count": 3,
        "review_list": [
            {
                "review_plan_id": "RP-001",
                "knowledge_scope": "两位数乘法",
                "review_stage": "Day1",
                "status": "pending",
                "push_question_id": "Q-002",
                "push_date": "2024-01-16"
            }
        ]
    }
}
```

### 1.4 获取知识点掌握情况

**GET** `/api/v1/student/{student_id}/mastery`

查询参数:
- `knowledge_id`: 知识点ID (可选)
- `status`: weak/pending/mastered (可选)

响应体:
```json
{
    "status": "success",
    "data": {
        "total_knowledge": 50,
        "mastered_count": 20,
        "weak_count": 5,
        "mastery_list": [
            {
                "knowledge_id": "G-N-3-001",
                "knowledge_scope": "两位数加两位数",
                "mastery_status": "pending",
                "master_level": 0.65,
                "correct_count": 1,
                "wrong_count": 1
            }
        ]
    }
}
```

---

## 二、教师端 API

### 2.1 获取班级学情

**GET** `/api/v1/teacher/{teacher_id}/class/{class_id}/overview`

响应体:
```json
{
    "status": "success",
    "data": {
        "class_name": "三年级(1)班",
        "total_students": 45,
        "average_mastery": 0.68,
        "weak_knowledge_top5": [
            {"knowledge_id": "G-N-3-001", "knowledge_scope": "两位数乘法", "weak_count": 15}
        ],
        "error_distribution": [
            {"level1": "计算", "count": 45},
            {"level1": "概念", "count": 30}
        ]
    }
}
```

### 2.2 获取学生详情

**GET** `/api/v1/teacher/{teacher_id}/student/{student_id}`

响应体:
```json
{
    "status": "success",
    "data": {
        "student_id": "S-0001",
        "student_name": "张三",
        "student_grade": "三年级",
        "mastery_level": 0.72,
        "mistake_count": 12,
        "weak_knowledge_list": [
            {"knowledge_id": "G-N-3-002", "knowledge_scope": "除法竖式"}
        ],
        "recent_activity": [
            {"type": "mistake", "date": "2024-01-15", "count": 3}
        ]
    }
}
```

### 2.3 获取错因统计

**GET** `/api/v1/teacher/{teacher_id}/error-analysis`

查询参数:
- `start_date`: 开始日期
- `end_date`: 结束日期
- `class_id`: 班级ID (可选)

响应体:
```json
{
    "status": "success",
    "data": {
        "total_errors": 120,
        "error_tags_distribution": [
            {"error_id": "C-001", "level1": "计算", "level2": "口算与基本运算", "count": 25},
            {"error_id": "C-002", "level2": "退位减法", "count": 20}
        ],
        "grade_distribution": [
            {"grade": "三年级", "count": 50}
        ]
    }
}
```

### 2.4 人工复核错因

**POST** `/api/v1/teacher/{teacher_id}/review-error/{mistake_case_id}`

请求体:
```json
{
    "error_tags": [
        {"error_id": "C-001", "confidence": 0.95}
    ],
    "review_comment": "确认错因正确",
    "confirmed_by": "teacher_id"
}
```

响应体:
```json
{
    "status": "success",
    "message": "复核完成"
}
```

---

## 三、管理端 API

### 3.1 知识点管理

**GET** `/api/v1/admin/knowledge`

**POST** `/api/v1/admin/knowledge`

**PUT** `/api/v1/admin/knowledge/{knowledge_id}`

**DELETE** `/api/v1/admin/knowledge/{knowledge_id}`

### 3.2 错因库管理

**GET** `/api/v1/admin/error-bank`

**POST** `/api/v1/admin/error-bank`

**PUT** `/api/v1/admin/error-bank/{error_id}`

**DELETE** `/api/v1/admin/error-bank/{error_id}`

### 3.3 题目管理

**GET** `/api/v1/admin/question`

**POST** `/api/v1/admin/question`

**PUT** `/api/v1/admin/question/{question_id}`

**DELETE** `/api/v1/admin/question/{question_id}`

### 3.4 频次限制配置

**GET** `/api/v1/admin/frequency-limit`

**PUT** `/api/v1/admin/frequency-limit`

请求体:
```json
{
    "daily_limit": 5,
    "weekly_limit": 3
}
```

---

## 四、服务间 API（内部调用）

### 4.1 Analysis Service

**POST** `/internal/api/v1/analysis/process`

请求体:
```json
{
    "image": "base64_encoded_image",
    "original_question": "题目文本",
    "student_write": "学生作答",
    "standard_solve_steps": "标准步骤"
}
```

响应体:
```json
{
    "judge_result": "correct/wrong/copy_warning",
    "step_feedback": "步骤反馈",
    "error_step_list": [],
    "miss_step_list": [],
    "is_copy": false,
    "core_error_type": "计算失误",
    "confidence": 0.85
}
```

### 4.2 Error Analysis Agent

**POST** `/internal/api/v1/error-analysis/analyze`

请求体:
```json
{
    "original_question": "题目文本",
    "student_write": "学生作答",
    "judge_result": "wrong",
    "core_error_type": "计算失误",
    "step_feedback": "步骤反馈"
}
```

响应体:
```json
{
    "error_tags": [
        {"error_id": "C-001", "level1": "计算", "level2": "口算", "level3": "进位错误", "confidence": 0.9}
    ],
    "knowledge_id": "G-N-3-001",
    "knowledge_scope": "两位数进位加法",
    "reasoning_content": "推理过程"
}
```

### 4.3 Knowledge Service

**POST** `/internal/api/v1/knowledge/retrieve`

请求体:
```json
{
    "knowledge_id": "G-N-3-001",
    "knowledge_scope": "两位数进位加法",
    "grade": "三年级"
}
```

响应体:
```json
{
    "knowledge_explanation": "知识点详细解释",
    "difficulty": "medium",
    "standard_solution": "标准解法",
    "scope_validation": true,
    "prerequisite": "G-N-2-001",
    "textbook_version": "人教版"
}
```

### 4.4 Teaching Service

**POST** `/internal/api/v1/teaching/generate`

请求体:
```json
{
    "error_tags": [...],
    "knowledge_scope": "两位数进位加法",
    "master_level": 0.65,
    "original_question": "题目文本",
    "student_write": "学生作答"
}
```

响应体:
```json
{
    "explanation": "知识点讲解",
    "hints": ["提示1", "提示2"],
    "practice_list": [
        {"question_id": "Q-001", "question_description": "变式题", "difficulty": "medium"}
    ],
    "reasoning_content": "推理过程"
}
```

### 4.5 State Service

**POST** `/internal/api/v1/state/update`

请求体:
```json
{
    "student_id": "S-0001",
    "knowledge_id": "G-N-3-001",
    "is_correct": true,
    "confidence": 0.85,
    "mistake_case_id": "MC-001"
}
```

响应体:
```json
{
    "master_level": 0.65,
    "next_action": "practice",
    "correct_count": 1,
    "wrong_count": 0,
    "mastery_status": "pending"
}
```

**POST** `/internal/api/v1/state/generate-review`

请求体:
```json
{
    "student_id": "S-0001",
    "knowledge_id": "G-N-3-001",
    "knowledge_mastery_id": "KM-001"
}
```

响应体:
```json
{
    "review_plan_id": "RP-001",
    "review_stages": ["Day1", "Day3", "Day7"],
    "status": "generated"
}
```

---

## 五、Webhook 事件

### 5.1 薄弱知识点通知

**POST** `/webhook/v1/weak-knowledge`

请求体:
```json
{
    "event_type": "weak_knowledge_detected",
    "student_id": "S-0001",
    "student_name": "张三",
    "knowledge_id": "G-N-3-001",
    "knowledge_scope": "两位数乘法",
    "wrong_count": 2,
    "timestamp": "2024-01-15 10:30:00"
}
```

### 5.2 复习任务推送

**POST** `/webhook/v1/review-push`

请求体:
```json
{
    "event_type": "review_task_pushed",
    "student_id": "S-0001",
    "review_plan_id": "RP-001",
    "review_stage": "Day1",
    "push_question_id": "Q-002",
    "push_date": "2024-01-16"
}
```

### 5.3 频次超限通知

**POST** `/webhook/v1/frequency-limit-exceeded`

请求体:
```json
{
    "event_type": "frequency_limit_exceeded",
    "student_id": "S-0001",
    "knowledge_id": "G-N-3-001",
    "daily_push_count": 5,
    "daily_limit": 5,
    "timestamp": "2024-01-15 10:30:00"
}
```