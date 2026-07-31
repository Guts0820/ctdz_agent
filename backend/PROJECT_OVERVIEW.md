# `backend` 目录已实现功能与代码文件整理

## 一、整体架构

项目采用**微服务架构**，共包含 **7 个后端服务** + **1 个知识图谱服务** + **1 个 API 网关**，通过 `start_all.py` 统一启动管理。

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway (8000)                       │
├─────────────────────────────────────────────────────────────────┤
│  /api/v1/submit              学生提交作业入口                    │
│  /api/v1/student/{id}/mastery  查询学生掌握度                   │
│  /health                     健康检查                           │
├─────────────────────────────────────────────────────────────────┤
│                    ┌──────────────────────────┐                 │
│                    │     服务编排流程          │                 │
│                    │  Submit → Analysis →    │                 │
│                    │  ErrorAnalysis →        │                 │
│                    │  Knowledge → Teaching → │                 │
│                    │  State → ReviewPlan      │                 │
│                    └──────────────────────────┘                 │
├─────────────────────────────────────────────────────────────────┤
│  Analysis Service      (8081)   答题分析、OCR模拟、抄袭检测     │
│  Error Analysis Agent  (8082)   错因分析、错误标签、知识点映射  │
│  Knowledge Service     (8083)   知识点检索、教学大纲验证        │
│  Teaching Service      (8084)   教学内容生成、频率限制检查      │
│  State Service         (8085)   掌握状态管理、复习计划生成      │
│  Review Scheduler      (8086)   复习任务调度、推送记录管理      │
│  Knowledge Graph       (8007)   Neo4j知识图谱服务               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、核心代码文件清单

### 2.1 服务层 (`backend/services/`)

| 文件 | 端口 | 主要功能 | 核心接口 |
|------|------|----------|----------|
| `analysis_service.py` | 8081 | 答题分析、OCR模拟、抄袭检测、步骤分析 | `/internal/api/v1/analysis/process` |
| `error_analysis_agent.py` | 8082 | 错因分析、错误标签匹配、知识点映射 | `/internal/api/v1/error-analysis/analyze` |
| `knowledge_service.py` | 8083 | 知识点检索、教学大纲验证 | `/internal/api/v1/knowledge/retrieve` |
| `teaching_service.py` | 8084 | 教学内容生成、推送频率限制检查 | `/internal/api/v1/teaching/generate` |
| `state_service.py` | 8085 | 掌握状态管理、掌握度计算、复习计划生成 | `/internal/api/v1/state/update` |
| `review_scheduler.py` | 8086 | 复习任务调度、推送记录管理 | `/internal/api/v1/review/scheduler/run` |
| `mastery_utils.py` | - | 公共函数：掌握度计算 | `calculate_mastery(correct, wrong)` |
| `id_utils.py` | - | 公共函数：全局唯一ID生成 | `generate_id(prefix)` |

### 2.2 网关与启动

| 文件 | 功能 |
|------|------|
| `api_gateway.py` | API 网关，统一入口，服务编排 |
| `start_all.py` | 一键启动所有服务（含知识图谱） |

### 2.3 数据库与数据

| 文件 | 功能 |
|------|------|
| `database/init_db.py` | SQLite 数据库初始化、建表、初始数据加载 |
| `database/example_db.db` | SQLite 数据库文件 |
| `database/schema.sql` | 数据库表结构定义（可能已合并到 init_db.py） |
| `database/knowledge_points.csv` | 知识点 CSV 数据（255+条） |
| `database/knowledge_explanations.csv` | 知识点详解（可能未使用） |
| `database/mapping_report.csv` | 映射报告（可能未使用） |

### 2.4 知识图谱服务 (`kg_service/`)

| 文件 | 功能 |
|------|------|
| `kg_service/main.py` | 知识图谱服务入口（Neo4j） |
| `kg_service/database.py` | Neo4j 数据库连接配置 |
| `kg_service/.env` | Neo4j 连接参数 |

### 2.5 文档

| 文件 | 功能 |
|------|------|
| `api/endpoints.md` | API 端点文档 |
| `contracts/service_contracts.md` | 服务契约文档 |
| `state_machine/state_transition_table.md` | 状态机转换表 |

---

## 三、已实现功能详细说明

### 3.1 答题分析流程 (`submit` 接口)

```
学生提交 → API Gateway → Analysis Service → 判断结果
                                           ↓
                              ┌─────────────┴─────────────┐
                              ↓                           ↓
                           答对                       答错/疑似抄袭
                              ↓                           ↓
                    查知识点ID → 更新掌握度         Error Analysis Agent
                              ↓                           ↓
                       返回掌握度结果            查知识点 → 获取知识详情
                                                      ↓
                                                生成教学内容
                                                      ↓
                                              更新掌握度 → 生成复习计划
```

### 3.2 各服务核心功能

**Analysis Service**
- OCR 文本识别模拟（支持图片或直接文本输入）
- 答题正确性判断
- 步骤级分析（错误步骤、缺失步骤）
- 抄袭检测（对比标准答案）
- 记录答题历史到 `answer_history` 表

**Error Analysis Agent**
- 错误标签匹配（三级分类：计算/概念/审题/粗心）
- 知识点自动映射（根据题目文本判断）
- 创建错题案例 `mistake_case` 记录
- 错误置信度校验（低于 0.7 拒绝）

**Knowledge Service**
- 知识点详情检索（解释、难度、标准解法、常见错误等）
- 教学大纲验证（根据年级过滤超出范围的知识点）
- 知识点前置/后续关系查询

**Teaching Service**
- 三档教学模式：BASIC（<0.4）、STANDARD（0.4-0.8）、ADVANCED（>0.8）
- 生成解释、提示问题、练习题列表
- 推送频率限制检查（每日5次、每周3次）
- 记录教学内容到 `teaching_content` 表

**State Service**
- 学生知识点掌握状态管理
- 掌握度计算（基于正确/错误次数）
- 复习计划生成（Day1/Day3/Day7 三阶段）
- 掌握度查询接口

**Review Scheduler**
- 定时任务调度（每小时检查）
- 当日推送任务查询
- 学生复习任务查询
- 复习完成后更新掌握度

### 3.3 公共工具模块

**mastery_utils.py**
```python
def calculate_mastery(correct_count: int, wrong_count: int) -> tuple:
    # 返回 (master_level: float, mastery_status: str)
```

**id_utils.py**
```python
def generate_id(prefix: str) -> str:
    # 使用 uuid.uuid4() 生成全局唯一ID
    # 格式：{prefix}-{8位十六进制大写}
```

### 3.4 数据库表结构（14张表）

| 表名 | 用途 |
|------|------|
| `students` | 学生基本信息 |
| `knowledge` | 知识点定义 |
| `error_bank` | 错误类型库（三级分类） |
| `question` | 题目库 |
| `question_knowledge_mapping` | 题目-知识点映射 |
| `answer_history` | 答题历史 |
| `mistake_case` | 错题案例 |
| `mistake_case_error` | 错题-错误标签关联 |
| `mistake_case_knowledge` | 错题-知识点关联 |
| `teaching_content` | 教学内容记录 |
| `knowledge_mastery` | 学生知识点掌握状态 |
| `review_plan` | 复习计划 |
| `push_record` | 推送记录 |
| `frequency_limit` | 推送频率限制 |

---

## 四、已完成的关键修复/优化

| 序号 | 任务 | 状态 | 影响文件 |
|------|------|------|----------|
| 1 | 修复 `answer_history`/`mistake_case` 表 `student_id`/`question_id` 写空问题 | ✅ 完成 | analysis_service.py, error_analysis_agent.py, api_gateway.py, all_in_one.py |
| 2 | 修正 API Gateway 编排逻辑（去重 state_service 调用、真实知识点关联） | ✅ 完成 | api_gateway.py, all_in_one.py |
| 3 | 抽离 `calculate_mastery` 公共模块 | ✅ 完成 | mastery_utils.py, state_service.py, review_scheduler.py |
| 4 | 抽离 `generate_id` 公共模块（修复短时间连续调用重复问题） | ✅ 完成 | id_utils.py, 6个服务文件 |
| 5 | 整合 kg_service 进 start_all.py（修复 .env 路径问题） | ✅ 完成 | kg_service/main.py, start_all.py |

---

## 五、下一步分工建议

### 5.1 待开发功能

| 功能 | 优先级 | 涉及文件 | 说明 |
|------|--------|----------|------|
| **知识图谱转接层** | 高 | knowledge_service.py, kg_service/ | 让 knowledge_service 调用 kg_service 获取知识点（目前用本地字典） |
| **真实 OCR 集成** | 高 | analysis_service.py | 替换模拟 OCR，接入真实 OCR 服务 |
| **AI 分析引擎集成** | 高 | analysis_service.py, error_analysis_agent.py | 替换规则引擎，接入大模型 |
| **前端对接** | 中 | api_gateway.py | 根据前端需求调整 API 接口 |
| **掌握度算法升级** | 中 | mastery_utils.py | 引入 EF 系数、五档掌握度 |
| **多轮对话教学** | 中 | teaching_service.py | 支持学生追问、交互式辅导 |
| **作业批量提交** | 低 | api_gateway.py | 支持一次提交多道题目 |
| **教师端管理后台** | 低 | 新建文件 | 教师查看学生进度、调整教学策略 |

### 5.2 技术债务清理

| 项目 | 说明 |
|------|------|
| 测试覆盖 | 目前无单元测试，需补充核心逻辑测试 |
| 日志完善 | 各服务缺少结构化日志 |
| 配置管理 | .env 文件分散，需统一配置管理 |
| 异常处理 | 部分服务异常处理不够完善 |
| 代码文档 | 部分函数缺少 docstring |

### 5.3 分工建议

**后端开发**
- 服务 A：知识图谱转接层 + 知识点检索优化
- 服务 B：OCR 集成 + AI 分析引擎对接
- 服务 C：掌握度算法升级 + 复习计划优化

**测试与运维**
- 服务 D：单元测试编写 + API 文档维护
- 服务 E：部署脚本优化 + 监控告警

**前端对接**
- 服务 F：API 接口调整 + 数据格式适配

---

## 六、启动方式

```bash
# 开发环境一键启动所有服务
python backend/start_all.py

# 单独启动某个服务
python backend/services/analysis_service.py    # 8081
python backend/services/state_service.py       # 8085
python kg_service/main.py                      # 8007

# 访问 API 网关
http://localhost:8000/api/v1/submit
http://localhost:8000/health
```