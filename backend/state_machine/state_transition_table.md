# AI小学数学错题订正系统 - 状态机转换表

## 一、系统状态定义

### 1.1 状态枚举

| 状态码 | 状态名称 | 描述 |
|--------|---------|------|
| START | 开始 | 系统启动，等待输入 |
| OCR_CHECK | OCR检查 | 执行图片识别 |
| PARSE_QUESTION | 题目解析 | 解析OCR结果 |
| PROCESS_CHECK | 过程批改 | 逐步批改作答 |
| ERROR_ANALYSIS | 错因分析 | 分析错误原因 |
| RAG_RETRIEVAL | 知识检索 | 检索知识点内容 |
| TEACHING_ROUTER | 教学路由 | 根据掌握度选择教学路径 |
| SELECT_OUTPUT | 输出选择 | 选择输出内容 |
| MASTERY_JUDGEMENT | 掌握度判定 | 判定知识点掌握程度 |
| STATE_UPDATE | 状态更新 | 更新学生状态 |
| GUIDE_MODE | 引导模式 | 苏格拉底式引导 |
| MARK_MASTERED | 标记已掌握 | 标记知识点为已掌握 |
| MARK_WEAK | 标记薄弱 | 标记知识点为薄弱 |
| MARK_PENDING | 标记待提升 | 标记知识点为待提升 |
| ENTER_REVIEW | 进入复习 | 进入周期复习流程 |
| DAY1_PUSH | Day1推送 | 推送Day1复习题 |
| DAY1_CHECK | Day1检查 | 检查Day1作答 |
| DAY3_PUSH | Day3推送 | 推送Day3复习题 |
| DAY3_CHECK | Day3检查 | 检查Day3作答 |
| DAY7_PUSH | Day7推送 | 推送Day7复习题 |
| DAY7_CHECK | Day7检查 | 检查Day7作答 |
| END | 结束 | 流程结束 |

### 1.2 知识点掌握状态

| 状态码 | 状态名称 | 描述 |
|--------|---------|------|
| weak | 薄弱 | 连续错误≥2次 |
| pending | 待提升 | 未达成连续2次正确/错误 |
| mastered | 已掌握 | 连续正确≥2次 |

### 1.3 复习计划状态

| 状态码 | 状态名称 | 描述 |
|--------|---------|------|
| pending | 待推送 | 等待推送 |
| pushing | 推送中 | 正在推送 |
| completed | 已完成 | 学生已作答 |
| cancelled | 已取消 | 任务已取消 |

---

## 二、主状态机转换表

### 2.1 主流程转换

| 当前状态 | 触发条件 | 下一状态 | 执行动作 | 输出数据 |
|---------|---------|---------|---------|---------|
| START | 用户提交作业 | OCR_CHECK | 接收输入参数 | student_id, image, grade |
| OCR_CHECK | text_status = normal | PARSE_QUESTION | OCR识别成功 | original_question, student_write, text_status |
| OCR_CHECK | text_status = empty | END | OCR识别为空 | error: OCR_EMPTY |
| OCR_CHECK | text_status = incomplete | END | OCR识别不完整 | error: OCR_INCOMPLETE |
| PARSE_QUESTION | 解析成功 | PROCESS_CHECK | 解析题目和答案 | original_question, student_write |
| PARSE_QUESTION | 解析失败 | END | 题目解析失败 | error: PARSE_ERROR |
| PROCESS_CHECK | is_copy = true | GUIDE_MODE | 检测到抄袭 | is_copy=true, skip error analysis |
| PROCESS_CHECK | is_copy = false | ERROR_ANALYSIS | 正常批改 | judge_result, step_feedback, core_error_type |
| ERROR_ANALYSIS | 分析成功 | RAG_RETRIEVAL | 错因分析完成 | error_tags, knowledge_id, knowledge_scope |
| ERROR_ANALYSIS | 置信度<0.7 | END | 低置信度需人工复核 | warning: LOW_CONFIDENCE |
| RAG_RETRIEVAL | 检索成功 | TEACHING_ROUTER | 知识检索完成 | knowledge_explanation, difficulty, standard_solution |
| RAG_RETRIEVAL | 知识点未找到 | END | 知识点不存在 | error: KNOWLEDGE_NOT_FOUND |
| TEACHING_ROUTER | master_level < 0.4 | SELECT_OUTPUT | EXPLAIN + BASIC PRACTICE | teaching_mode: BASIC |
| TEACHING_ROUTER | 0.4 ≤ master_level ≤ 0.8 | SELECT_OUTPUT | EXPLAIN + PRACTICE | teaching_mode: STANDARD |
| TEACHING_ROUTER | master_level > 0.8 | SELECT_OUTPUT | EXPLAIN + GUIDE | teaching_mode: ADVANCED |
| SELECT_OUTPUT | 内容生成成功 | MASTERY_JUDGEMENT | 选择输出内容 | explanation, hints, practice_list |
| MASTERY_JUDGEMENT | correct_count ≥ 2 | MARK_MASTERED | 连续2次正确 | mastery_status: mastered |
| MASTERY_JUDGEMENT | wrong_count ≥ 2 | MARK_WEAK | 连续2次错误 | mastery_status: weak |
| MASTERY_JUDGEMENT | 其他 | MARK_PENDING | 未达成连续 | mastery_status: pending |
| MARK_MASTERED | 状态更新成功 | STATE_UPDATE | 标记已掌握 | master_level, next_action |
| MARK_WEAK | 状态更新成功 | STATE_UPDATE | 标记薄弱 | master_level, next_action, notify_teacher |
| MARK_PENDING | 状态更新成功 | ENTER_REVIEW | 标记待提升 | master_level, next_action |
| STATE_UPDATE | 更新成功 | END | 状态持久化 | database updated |
| ENTER_REVIEW | 生成复习计划 | DAY1_PUSH | 创建复习任务 | review_plan_id, stage_dates |
| GUIDE_MODE | 引导完成 | END | 苏格拉底式引导 | hints, no exercises |

### 2.2 状态转换图

```
START → OCR_CHECK → PARSE_QUESTION → PROCESS_CHECK
                                          │
                           ┌──────────────┴──────────────┐
                           ▼                             ▼
                      is_copy=true                  is_copy=false
                           │                             │
                           ▼                             ▼
                      GUIDE_MODE                   ERROR_ANALYSIS
                           │                             │
                           ▼                             ▼
                         END                    RAG_RETRIEVAL
                                                      │
                                                      ▼
                                                TEACHING_ROUTER
                                                      │
                           ┌───────────────────────┼───────────────────────┐
                           ▼                       ▼                       ▼
                    master_level < 0.4    0.4 ≤ master_level ≤ 0.8    master_level > 0.8
                           │                       │                       │
                           └───────────────────────┼───────────────────────┘
                                                   ▼
                                            SELECT_OUTPUT
                                                   │
                                                   ▼
                                            MASTERY_JUDGEMENT
                                                   │
                           ┌───────────────────────┼───────────────────────┐
                           ▼                       ▼                       ▼
                    correct_count ≥ 2        wrong_count ≥ 2          其他情况
                           │                       │                       │
                           ▼                       ▼                       ▼
                    MARK_MASTERED            MARK_WEAK              MARK_PENDING
                           │                       │                       │
                           └───────────────────────┼───────────────────────┘
                                                   ▼
                                            STATE_UPDATE
                                                   │
                                                   ▼
                                                 END
```

---

## 三、周期复习状态机

### 3.1 周期复习转换表

| 当前状态 | 触发条件 | 下一状态 | 执行动作 | 输出数据 |
|---------|---------|---------|---------|---------|
| ENTER_REVIEW | 创建复习计划 | DAY1_PUSH | 生成Day1/Day3/Day7任务 | review_plan_id, push_records |
| DAY1_PUSH | 推送成功 | DAY1_CHECK | 推送Day1复习题 | push_record_id, push_question_id |
| DAY1_CHECK | 作答正确 | DAY3_PUSH | Day1作答正确 | is_correct=true |
| DAY1_CHECK | 作答错误 | MARK_WEAK | Day1作答错误 | is_correct=false, notify_teacher |
| DAY3_PUSH | 推送成功 | DAY3_CHECK | 推送Day3复习题 | push_record_id, push_question_id |
| DAY3_CHECK | 作答正确 | DAY7_PUSH | Day3作答正确 | is_correct=true |
| DAY3_CHECK | 作答错误 | MARK_WEAK | Day3作答错误 | is_correct=false, notify_teacher |
| DAY7_PUSH | 推送成功 | DAY7_CHECK | 推送Day7复习题 | push_record_id, push_question_id |
| DAY7_CHECK | 作答正确 | MARK_MASTERED | Day7作答正确，通关 | is_correct=true, mastery_status: mastered |
| DAY7_CHECK | 作答错误 | MARK_WEAK | Day7作答错误 | is_correct=false, notify_teacher |
| MARK_MASTERED | 状态更新 | END | 标记已掌握 | state updated |
| MARK_WEAK | 状态更新 | END | 标记薄弱，教师干预 | state updated, teacher_notification |

### 3.2 周期复习转换图

```
ENTER_REVIEW → DAY1_PUSH → DAY1_CHECK
                                │
                     ┌──────────┴──────────┐
                     ▼                     ▼
                 正确                  错误
                     │                     │
                     ▼                     ▼
              DAY3_PUSH              MARK_WEAK → END
                     │
                     ▼
              DAY3_CHECK
                     │
              ┌──────┴──────┐
              ▼             ▼
          正确           错误
              │             │
              ▼             ▼
       DAY7_PUSH      MARK_WEAK → END
              │
              ▼
       DAY7_CHECK
              │
       ┌──────┴──────┐
       ▼             ▼
   正确           错误
       │             │
       ▼             ▼
MARK_MASTERED    MARK_WEAK
       │             │
       └──────┬──────┘
              ▼
            END
```

---

## 四、掌握度计算状态机

### 4.1 掌握度计算规则

| 条件 | correct_count | wrong_count | 掌握度 | 状态 |
|------|--------------|-------------|--------|------|
| 首次作答正确 | 1 | 0 | 0.33 | pending |
| 首次作答错误 | 0 | 1 | 0.00 | pending |
| 连续2次正确 | 2 | 0 | 1.00 | mastered |
| 连续2次错误 | 0 | 2 | 0.00 | weak |
| 先错后对 | 1 | 1 | 0.50 | pending |
| 先对后错 | 1 | 1 | 0.50 | pending |
| 3次正确1次错误 | 3 | 1 | 0.75 | pending |
| 1次正确3次错误 | 1 | 3 | 0.25 | weak |

### 4.2 掌握度计算公式

```
master_level = (correct_count * 0.5) / (correct_count + wrong_count)

特殊规则:
- correct_count ≥ 2 → master_level = 1.00, status = mastered
- wrong_count ≥ 2 → master_level = 0.00, status = weak
- 其他情况 → status = pending
```

### 4.3 掌握度状态转换

```
                    ┌──────────────────┐
                    │   pending (待提升) │
                    └────────┬─────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
   correct_count ≥ 2    wrong_count ≥ 2    其他情况
          │                  │                  │
          ▼                  ▼                  ▼
   mastered (已掌握)    weak (薄弱)       pending (保持)
          │                  │                  │
          │                  ▼                  │
          │          教师干预/重新学习           │
          │                  │                  │
          │                  ▼                  │
          └────────────── 重置计数器 ◄───────────┘
```

---

## 五、教学路径状态机

### 5.1 教学路径选择规则

| master_level | 教学模式 | 讲解类型 | 练习类型 | 引导类型 |
|--------------|---------|---------|---------|---------|
| < 0.4 | BASIC | EXPLAIN (基础讲解) | BASIC_PRACTICE (基础题) | 无 |
| 0.4 ~ 0.8 | STANDARD | EXPLAIN (标准讲解) | PRACTICE (变式题) | 无 |
| > 0.8 | ADVANCED | EXPLAIN (简要讲解) | 无 | GUIDE (弱引导) |

### 5.2 教学路径转换图

```
master_level输入
        │
        ▼
   ┌─────────────────────────────────────┐
   │           TEACHING_ROUTER           │
   └────────────────┬────────────────────┘
                    │
    ┌───────────────┼───────────────┬───────────────┐
    ▼               ▼               ▼               ▼
master_level < 0.4 0.4-0.8      > 0.8         is_copy=true
    │               │               │               │
    ▼               ▼               ▼               ▼
BASIC_MODE     STANDARD_MODE  ADVANCED_MODE   GUIDE_ONLY_MODE
    │               │               │               │
    ├─→ EXPLAIN     ├─→ EXPLAIN     ├─→ EXPLAIN     └─→ GUIDE
    │               │               │                       │
    └─→ BASIC_      └─→ PRACTICE    └─→ GUIDE             END
        PRACTICE
```

---

## 六、频次控制状态机

### 6.1 频次控制规则

| 控制维度 | 限制值 | 检查时机 |
|---------|-------|---------|
| 单日推送总量 | ≤ 5题 | 每次推送前 |
| 单知识点周推送 | ≤ 3次 | 每次推送前 |

### 6.2 频次控制转换表

| 当前状态 | 触发条件 | 下一状态 | 执行动作 |
|---------|---------|---------|---------|
| FREQUENCY_CHECK | daily_count < daily_limit AND weekly_count < weekly_limit | PUSH_ALLOWED | 允许推送 |
| FREQUENCY_CHECK | daily_count >= daily_limit | PUSH_DENIED | 单日超限 |
| FREQUENCY_CHECK | weekly_count >= weekly_limit | PUSH_DENIED | 单知识点周超限 |
| PUSH_ALLOWED | 推送成功 | UPDATE_COUNT | 更新计数器 |
| PUSH_DENIED | 记录日志 | NOTIFY_TEACHER | 通知教师 |
| UPDATE_COUNT | 更新成功 | END | 计数器+1 |
| NOTIFY_TEACHER | 通知成功 | END | 生成通知 |

---

## 七、防抄袭检测状态机

### 7.1 抄袭检测规则

| 检测项 | 阈值 | 判定结果 |
|--------|------|---------|
| 文本相似度 | ≥ 0.9 | 疑似抄袭 |
| 步骤完整性 | < 30% | 疑似抄袭 |
| 答案完全一致 | 是 | 疑似抄袭 |
| 思路表述缺失 | 是 | 疑似抄袭 |

### 7.2 抄袭检测转换表

| 当前状态 | 触发条件 | 下一状态 | 执行动作 |
|---------|---------|---------|---------|
| COPY_CHECK | 相似度≥0.9 AND 步骤完整性<30% | COPY_CONFIRMED | is_copy=true |
| COPY_CHECK | 其他 | COPY_NOT_DETECTED | is_copy=false |
| COPY_CONFIRMED | 确认抄袭 | GUIDE_MODE | 进入引导模式 |
| COPY_NOT_DETECTED | 无抄袭 | ERROR_ANALYSIS | 正常流程 |

---

## 八、完整状态机矩阵

### 8.1 状态转换总表

| # | 当前状态 | 触发条件 | 下一状态 | 服务 | 数据库操作 |
|---|---------|---------|---------|------|-----------|
| 1 | START | 用户提交 | OCR_CHECK | Analysis | - |
| 2 | OCR_CHECK | normal | PARSE_QUESTION | Analysis | - |
| 3 | OCR_CHECK | empty | END | - | - |
| 4 | OCR_CHECK | incomplete | END | - | - |
| 5 | PARSE_QUESTION | 成功 | PROCESS_CHECK | Analysis | - |
| 6 | PARSE_QUESTION | 失败 | END | - | - |
| 7 | PROCESS_CHECK | is_copy=true | GUIDE_MODE | Analysis | write answer_history |
| 8 | PROCESS_CHECK | is_copy=false | ERROR_ANALYSIS | Analysis | write answer_history |
| 9 | ERROR_ANALYSIS | 成功 | RAG_RETRIEVAL | ErrorAnalysis | write mistake_case |
| 10 | ERROR_ANALYSIS | 低置信度 | END | - | - |
| 11 | RAG_RETRIEVAL | 成功 | TEACHING_ROUTER | Knowledge | - |
| 12 | RAG_RETRIEVAL | 失败 | END | - | - |
| 13 | TEACHING_ROUTER | <0.4 | SELECT_OUTPUT | Teaching | - |
| 14 | TEACHING_ROUTER | 0.4-0.8 | SELECT_OUTPUT | Teaching | - |
| 15 | TEACHING_ROUTER | >0.8 | SELECT_OUTPUT | Teaching | - |
| 16 | SELECT_OUTPUT | 成功 | MASTERY_JUDGEMENT | Teaching | write teaching_content |
| 17 | MASTERY_JUDGEMENT | correct≥2 | MARK_MASTERED | State | - |
| 18 | MASTERY_JUDGEMENT | wrong≥2 | MARK_WEAK | State | - |
| 19 | MASTERY_JUDGEMENT | 其他 | MARK_PENDING | State | - |
| 20 | MARK_MASTERED | 更新成功 | STATE_UPDATE | State | update knowledge_mastery |
| 21 | MARK_WEAK | 更新成功 | STATE_UPDATE | State | update knowledge_mastery |
| 22 | MARK_PENDING | 更新成功 | ENTER_REVIEW | State | update knowledge_mastery |
| 23 | STATE_UPDATE | 成功 | END | State | write review_plan |
| 24 | ENTER_REVIEW | 生成计划 | DAY1_PUSH | State | write push_record |
| 25 | DAY1_PUSH | 推送成功 | DAY1_CHECK | State | update push_record |
| 26 | DAY1_CHECK | 正确 | DAY3_PUSH | Analysis | write answer_history |
| 27 | DAY1_CHECK | 错误 | MARK_WEAK | State | - |
| 28 | DAY3_PUSH | 推送成功 | DAY3_CHECK | State | update push_record |
| 29 | DAY3_CHECK | 正确 | DAY7_PUSH | Analysis | write answer_history |
| 30 | DAY3_CHECK | 错误 | MARK_WEAK | State | - |
| 31 | DAY7_PUSH | 推送成功 | DAY7_CHECK | State | update push_record |
| 32 | DAY7_CHECK | 正确 | MARK_MASTERED | Analysis | write answer_history |
| 33 | DAY7_CHECK | 错误 | MARK_WEAK | State | - |
| 34 | GUIDE_MODE | 完成 | END | Teaching | - |

---

## 九、错误回流机制

### 9.1 错误回流规则

| 错误类型 | 回流目标 | 处理方式 |
|---------|---------|---------|
| 连续2次错误 | 教师端 | 标记薄弱知识点，通知教师 |
| OCR失败 | 学生端 | 提示重新拍照 |
| 低置信度错因 | 教师端 | 推送人工复核 |
| 频次超限 | 教师端 | 通知教师，可放宽限制 |
| 知识点未找到 | 管理员端 | 提示补充知识点 |

### 9.2 回流流程

```
错误检测
    │
    ├─→ 连续错误 → 教师端干预 → 重新学习 → 重置计数器
    │
    ├─→ OCR失败 → 学生端重试 → 重新提交
    │
    ├─→ 低置信度 → 教师复核 → 更新错因
    │
    ├─→ 频次超限 → 教师审批 → 放宽限制/暂停推送
    │
    └─→ 知识点缺失 → 管理员补充 → 重新处理
```