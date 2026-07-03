# AI小学数学错题订正系统 - 服务间契约定义

## 一、整体架构概览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           API Gateway                                   │
│                    /api/v1/* (对外) /internal/api/v1/* (对内)            │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
        ┌───────────┬───────────────┼───────────────┬───────────┐
        ▼           ▼               ▼               ▼           ▼
┌─────────────┐┌─────────────┐┌─────────────┐┌─────────────┐┌─────────────┐
│  Analysis   ││ Error       ││ Knowledge   ││  Teaching   ││   State     │
│   Service   ││ Analysis    ││   Service   ││   Service   ││   Service   │
└──────┬──────┘└──────┬──────┘└──────┬──────┘└──────┬──────┘└──────┬──────┘
       │              │              │              │              │
       └──────────────┴──────────────┴──────────────┴──────────────┘
                                    │
                        ┌───────────▼───────────┐
                        │       Database        │
                        └───────────────────────┘
```

---

## 二、服务间调用链

```
INPUT (学生提交作业)
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: Analysis Service                                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  OCR → Parser → ProcessChecker → is_copy检测         │    │
│  └─────────────────────┬───────────────────────────────┘    │
│                        │                                    │
│                        ▼                                    │
│  输出: judge_result, step_feedback, error_step_list,        │
│        miss_step_list, is_copy, core_error_type, confidence │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼ (is_copy=false)
┌─────────────────────────────────────────────────────────────┐
│  Step 2: Error Analysis Agent                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  三级错因标签匹配 → knowledge_id映射 → confidence评分  │    │
│  └─────────────────────┬───────────────────────────────┘    │
│                        │                                    │
│                        ▼                                    │
│  输出: error_tags, knowledge_id, knowledge_scope,           │
│        reasoning_content                                    │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: Knowledge Service                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  RAG检索 → 教材知识图谱校验 → Event Builder信息抽取     │    │
│  └─────────────────────┬───────────────────────────────┘    │
│                        │                                    │
│                        ▼                                    │
│  输出: knowledge_explanation, difficulty, standard_solution, │
│        scope_validation                                     │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 4: Teaching Service                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  频次控制检查 → 教学路径选择 → 内容生成                │    │
│  │  (master_level决定EXPLAIN/PRACTICE/GUIDE)            │    │
│  └─────────────────────┬───────────────────────────────┘    │
│                        │                                    │
│                        ▼                                    │
│  输出: explanation, hints, practice_list,                  │
│        reasoning_content                                    │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 5: State Service                                    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  掌握度计算 → 状态更新 → 周期复习计划生成             │    │
│  └─────────────────────┬───────────────────────────────┘    │
│                        │                                    │
│                        ▼                                    │
│  输出: master_level, next_action, correct_count,           │
│        wrong_count                                          │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
                        DATABASE UPDATE
                              │
                              ▼
                        OUTPUT (返回前端)
```

---

## 三、服务接口契约

### 3.1 Analysis Service 契约

**服务名称**: Analysis Service  
**服务端口**: 8081  
**基础路径**: `/internal/api/v1/analysis`

#### 接口定义

| 接口 | HTTP方法 | 路径 | 描述 |
|------|---------|------|------|
| OCR识别 | POST | `/ocr` | 将图片转换为文本 |
| 题目解析 | POST | `/parse` | 解析题目和学生答案 |
| 过程批改 | POST | `/process-check` | 逐步批改学生作答 |
| 完整分析 | POST | `/process` | 执行完整分析流程 |

#### 完整分析接口

**请求**:
```json
{
    "image": "base64_encoded_image_string",
    "original_question": "题目文本（可选）",
    "student_write": "学生作答（可选）",
    "standard_solve_steps": "标准解题步骤",
    "text_status": "normal"
}
```

**响应**:
```json
{
    "status": "success",
    "data": {
        "judge_result": "correct/wrong/copy_warning/unknown",
        "step_feedback": "详细的步骤级反馈",
        "error_step_list": ["步骤1：列式错误", "步骤3：计算错误"],
        "miss_step_list": ["缺少单位换算步骤"],
        "is_copy": false,
        "core_error_type": "计算失误",
        "confidence": 0.85,
        "original_question": "解析后的题目",
        "student_write": "解析后的学生作答",
        "text_status": "normal/incomplete/empty"
    }
}
```

---

### 3.2 Error Analysis Agent 契约

**服务名称**: Error Analysis Agent  
**服务端口**: 8082  
**基础路径**: `/internal/api/v1/error-analysis`

#### 接口定义

| 接口 | HTTP方法 | 路径 | 描述 |
|------|---------|------|------|
| 错因分析 | POST | `/analyze` | 分析错题原因 |
| 标签查询 | GET | `/tags` | 查询错因标签 |
| 标签匹配 | POST | `/match` | 匹配错因标签 |

#### 错因分析接口

**请求**:
```json
{
    "original_question": "题目文本",
    "student_write": "学生作答",
    "judge_result": "wrong",
    "core_error_type": "计算失误",
    "step_feedback": "步骤反馈",
    "error_step_list": ["步骤1错误"],
    "miss_step_list": ["缺少步骤"],
    "confidence": 0.85
}
```

**响应**:
```json
{
    "status": "success",
    "data": {
        "error_tags": [
            {
                "error_id": "C-001",
                "level1": "计算",
                "level2": "口算与基本运算",
                "level3": "进位加法中十位漏加进位1",
                "confidence": 0.92,
                "judgment_criteria": "判定标准描述"
            }
        ],
        "knowledge_id": "G-N-3-001",
        "knowledge_scope": "两位数加两位数进位加法",
        "reasoning_content": "推理过程说明",
        "total_confidence": 0.88
    }
}
```

---

### 3.3 Knowledge Service 契约

**服务名称**: Knowledge Service  
**服务端口**: 8083  
**基础路径**: `/internal/api/v1/knowledge`

#### 接口定义

| 接口 | HTTP方法 | 路径 | 描述 |
|------|---------|------|------|
| 知识检索 | POST | `/retrieve` | 根据知识点ID检索内容 |
| RAG查询 | POST | `/rag` | 基于知识图谱查询 |
| 范围校验 | POST | `/validate` | 校验知识点范围 |
| 标准解法 | GET | `/solution/{knowledge_id}` | 获取标准解法 |

#### 知识检索接口

**请求**:
```json
{
    "knowledge_id": "G-N-3-001",
    "knowledge_scope": "两位数加两位数进位加法",
    "grade": "三年级",
    "textbook_version": "人教版"
}
```

**响应**:
```json
{
    "status": "success",
    "data": {
        "knowledge_explanation": "详细的知识点解释",
        "difficulty": "medium",
        "standard_solution": "标准解题步骤",
        "scope_validation": true,
        "prerequisite": "G-N-2-001",
        "next_knowledge": "G-N-3-002",
        "textbook_version": "人教版",
        "unit": "第2单元",
        "common_errors": "常见错误列表",
        "forbidden_explanation": "禁止讲解内容",
        "example": "示例题目",
        "teaching_tips": "教学提示"
    }
}
```

---

### 3.4 Teaching Service 契约

**服务名称**: Teaching Service  
**服务端口**: 8084  
**基础路径**: `/internal/api/v1/teaching`

#### 接口定义

| 接口 | HTTP方法 | 路径 | 描述 |
|------|---------|------|------|
| 教学内容生成 | POST | `/generate` | 生成教学内容 |
| 变式题生成 | POST | `/variant` | 生成变式题 |
| 基础讲解 | POST | `/explain` | 生成基础讲解 |
| 引导提示 | POST | `/guide` | 生成引导式提示 |
| 频次检查 | POST | `/frequency-check` | 检查推送频次 |

#### 教学内容生成接口

**请求**:
```json
{
    "error_tags": [
        {"error_id": "C-001", "level1": "计算", "level2": "口算", "level3": "进位错误"}
    ],
    "knowledge_scope": "两位数加两位数进位加法",
    "master_level": 0.65,
    "original_question": "题目文本",
    "student_write": "学生作答",
    "difficulty": "medium",
    "grade": "三年级"
}
```

**响应**:
```json
{
    "status": "success",
    "data": {
        "explanation": "详细的知识点讲解",
        "hints": ["提示1", "提示2", "提示3"],
        "practice_list": [
            {
                "question_id": "Q-001",
                "question_description": "变式题1描述",
                "difficulty": "medium",
                "answer": "标准答案",
                "solution": "解题步骤"
            },
            {
                "question_id": "Q-002",
                "question_description": "变式题2描述",
                "difficulty": "medium",
                "answer": "标准答案",
                "solution": "解题步骤"
            }
        ],
        "reasoning_content": "教学内容生成推理过程",
        "teaching_mode": "EXPLAIN+PRACTICE"
    }
}
```

#### 频次检查接口

**请求**:
```json
{
    "student_id": "S-0001",
    "knowledge_id": "G-N-3-001",
    "current_time": "2024-01-15 10:30:00"
}
```

**响应**:
```json
{
    "status": "success",
    "data": {
        "push_permission": true,
        "daily_push_count": 3,
        "daily_limit": 5,
        "weekly_push_count": 2,
        "weekly_limit": 3,
        "remaining_daily": 2,
        "remaining_weekly": 1
    }
}
```

---

### 3.5 State Service 契约

**服务名称**: State Service  
**服务端口**: 8085  
**基础路径**: `/internal/api/v1/state`

#### 接口定义

| 接口 | HTTP方法 | 路径 | 描述 |
|------|---------|------|------|
| 状态更新 | POST | `/update` | 更新掌握状态 |
| 掌握度判定 | POST | `/judge` | 判定掌握度 |
| 复习计划生成 | POST | `/generate-review` | 生成周期复习计划 |
| 复习任务推送 | POST | `/push-review` | 推送复习任务 |
| 掌握度查询 | GET | `/mastery/{student_id}` | 查询学生掌握度 |

#### 状态更新接口

**请求**:
```json
{
    "student_id": "S-0001",
    "knowledge_id": "G-N-3-001",
    "is_correct": true,
    "confidence": 0.85,
    "mistake_case_id": "MC-001",
    "answer_history_id": "AH-001"
}
```

**响应**:
```json
{
    "status": "success",
    "data": {
        "master_level": 0.65,
        "next_action": "practice",
        "correct_count": 1,
        "wrong_count": 0,
        "mastery_status": "pending",
        "knowledge_mastery_id": "KM-001",
        "should_generate_review": true
    }
}
```

#### 复习计划生成接口

**请求**:
```json
{
    "student_id": "S-0001",
    "knowledge_id": "G-N-3-001",
    "knowledge_mastery_id": "KM-001",
    "master_level": 0.5
}
```

**响应**:
```json
{
    "status": "success",
    "data": {
        "review_plan_id": "RP-001",
        "review_stages": ["Day1", "Day3", "Day7"],
        "stage_dates": {
            "Day1": "2024-01-16",
            "Day3": "2024-01-18",
            "Day7": "2024-01-22"
        },
        "status": "generated",
        "push_records": [
            {"push_record_id": "PR-001", "stage": "Day1", "status": "pending"},
            {"push_record_id": "PR-002", "stage": "Day3", "status": "pending"},
            {"push_record_id": "PR-003", "stage": "Day7", "status": "pending"}
        ]
    }
}
```

---

## 四、数据流转契约

### 4.1 数据流转矩阵

| 数据字段 | Analysis Service | Error Analysis Agent | Knowledge Service | Teaching Service | State Service |
|----------|------------------|---------------------|-------------------|------------------|---------------|
| image | 输入 | - | - | - | - |
| original_question | 输出 | 输入 | - | 输入 | - |
| student_write | 输出 | 输入 | - | 输入 | - |
| judge_result | 输出 | 输入 | - | - | - |
| step_feedback | 输出 | 输入 | - | - | - |
| error_step_list | 输出 | 输入 | - | - | - |
| miss_step_list | 输出 | 输入 | - | - | - |
| is_copy | 输出 | - | - | - | - |
| core_error_type | 输出 | 输入 | - | - | - |
| confidence | 输出 | 输入/输出 | - | - | 输入 |
| error_tags | - | 输出 | - | 输入 | - |
| knowledge_id | - | 输出 | 输入 | - | 输入 |
| knowledge_scope | - | 输出 | 输入 | 输入 | - |
| reasoning_content | - | 输出 | - | 输出 | - |
| knowledge_explanation | - | - | 输出 | - | - |
| difficulty | - | - | 输出 | 输入 | - |
| standard_solution | - | - | 输出 | - | - |
| scope_validation | - | - | 输出 | - | - |
| explanation | - | - | - | 输出 | - |
| hints | - | - | - | 输出 | - |
| practice_list | - | - | - | 输出 | - |
| master_level | - | - | - | 输入/输出 | 输出 |
| next_action | - | - | - | - | 输出 |
| correct_count | - | - | - | - | 输出 |
| wrong_count | - | - | - | - | 输出 |
| student_id | - | - | - | - | 输入 |

### 4.2 数据库写入契约

| 服务 | 写入表 | 触发时机 |
|------|--------|---------|
| Analysis Service | answer_history | 每次提交分析完成后 |
| Error Analysis Agent | mistake_case, mistake_case_knowledge, mistake_case_error | 首次错因分析完成后 |
| Teaching Service | teaching_content | 教学内容生成完成后 |
| State Service | knowledge_mastery, review_plan, push_record, frequency_limit | 状态更新时 |

---

## 五、错误处理契约

### 5.1 错误响应格式

所有服务统一错误响应格式:

```json
{
    "status": "error",
    "code": "ERROR_CODE",
    "message": "错误描述",
    "details": {
        "field": "字段名（如果适用）",
        "value": "字段值",
        "reason": "详细原因"
    },
    "timestamp": "2024-01-15 10:30:00"
}
```

### 5.2 错误码定义

| 错误码 | 描述 | 触发服务 |
|--------|------|---------|
| OCR_EMPTY | OCR识别结果为空 | Analysis Service |
| OCR_INCOMPLETE | OCR识别结果不完整 | Analysis Service |
| PARSE_ERROR | 题目解析失败 | Analysis Service |
| COPY_DETECTED | 检测到抄袭 | Analysis Service |
| ANALYSIS_TIMEOUT | 分析超时 | Analysis Service |
| ERROR_TAG_LOW_CONFIDENCE | 错因标签置信度低 | Error Analysis Agent |
| KNOWLEDGE_NOT_FOUND | 知识点未找到 | Knowledge Service |
| SCOPE_INVALID | 知识点范围无效（超纲） | Knowledge Service |
| FREQUENCY_LIMIT_EXCEEDED | 推送频次超限 | Teaching Service |
| GENERATION_ERROR | 教学内容生成失败 | Teaching Service |
| STATE_UPDATE_FAILED | 状态更新失败 | State Service |
| REVIEW_GENERATION_FAILED | 复习计划生成失败 | State Service |

---

## 六、超时与重试契约

### 6.1 超时配置

| 服务 | 接口 | 超时时间 |
|------|------|---------|
| Analysis Service | /process | 30秒 |
| Error Analysis Agent | /analyze | 20秒 |
| Knowledge Service | /retrieve | 15秒 |
| Teaching Service | /generate | 25秒 |
| State Service | /update | 10秒 |

### 6.2 重试策略

- **OCR失败**: 最多重试2次
- **网络超时**: 最多重试3次，指数退避
- **低置信度错因**: 不重试，标记为待人工复核
- **数据库写入失败**: 最多重试2次

---

## 七、安全契约

### 7.1 认证与授权

- 对外API: JWT Token认证
- 内部服务调用: API Key认证
- 教师端操作: 角色权限校验

### 7.2 数据加密

- 传输层: HTTPS/TLS 1.2+
- 敏感数据: AES-256加密存储
- 日志脱敏: 学生姓名、学号等敏感信息脱敏

### 7.3 访问控制

- 学生只能访问自己的数据
- 教师只能访问本班学生数据
- 管理端需要管理员权限

---

## 八、日志契约

### 8.1 日志格式

```json
{
    "timestamp": "2024-01-15 10:30:00",
    "service": "AnalysisService",
    "level": "INFO",
    "trace_id": "abc-123",
    "span_id": "span-001",
    "student_id": "S-0001",
    "question_id": "Q-001",
    "operation": "process_check",
    "status": "success",
    "duration_ms": 1250,
    "data": {
        "judge_result": "wrong",
        "is_copy": false
    }
}
```

### 8.2 日志等级

| 等级 | 使用场景 |
|------|---------|
| DEBUG | 开发调试信息 |
| INFO | 正常业务流程 |
| WARN | 异常但可恢复 |
| ERROR | 不可恢复错误 |
| FATAL | 系统级故障 |