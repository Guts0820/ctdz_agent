# ctdz_agent_backend

这是一个面向小学数学错题分析、知识图谱检索与智能教学的项目，采用多服务架构，包含 API 网关、答题分析、错因分析、知识服务、教学服务、状态服务和复习调度服务。

## 项目结构

- `frontend/`：静态学生、教师和管理员端页面；拍照作业会调用 API 网关。
- `backend/api_gateway.py`：统一入口，负责提交作业后的服务编排
- `backend/services/analysis_service.py`：OCR/答题分析、判题基础结果生成
- `backend/services/error_analysis_agent.py`：错因分析与错误标签生成
- `backend/services/knowledge_service.py`：知识点检索
- `backend/services/teaching_service.py`：教学内容生成与频率控制
- `backend/services/state_service.py`：掌握度更新与复习计划生成
- `backend/services/review_scheduler.py`：复习任务调度
- `backend/insight_service.py`：Insight 服务（用户体系 / 动态复习引擎 / 成长报告 / 数据看板，端口 8010）
- `backend/review/`：动态复习引擎（优先级快照、按优先级选题、复习会话、错题订正）
- `backend/insight/`：成长报告与数据看板（五维能力、薄弱点、学习路径、统计报表）
- `backend/user_database.py`：用户账号与学习数据存储（user_data.db）
- `backend/database/init_db.py`：初始化数据库与初始数据
- `backend/start_all.py`：本地一键启动多个服务
- `backend/config.py`：统一配置读取
- `backend/services/cache_utils.py`：Redis 缓存封装
- `backend/services/llm_client.py`：LLM 调用封装
- `backend/services/observability.py`：日志与耗时统计

## 运行环境

建议使用：

- Python 3.11+
- SQLite（本地开发）
- Redis（可选，用于缓存）
- Neo4j/KG 服务（可选，若启用知识图谱服务）

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置方法

项目通过仓库根目录的 `.env` 文件统一配置。`backend/config.py` 会自动读取它。

### 主要配置项

```env
DATABASE_PATH=backend/database/example_db.db
KNOWLEDGE_CSV_PATH=backend/database/knowledge_points.csv
API_GATEWAY_HOST=0.0.0.0
API_GATEWAY_PORT=8000
ANALYSIS_SERVICE_URL=http://127.0.0.1:8081
ERROR_ANALYSIS_SERVICE_URL=http://127.0.0.1:8082
KNOWLEDGE_SERVICE_URL=http://127.0.0.1:8083
TEACHING_SERVICE_URL=http://127.0.0.1:8084
STATE_SERVICE_URL=http://127.0.0.1:8085
INSIGHT_SERVICE_URL=http://127.0.0.1:8010
KNOWLEDGE_GRAPH_URL=http://127.0.0.1:8007
OCR_SERVICE_URL=http://127.0.0.1:8087
OCR_ENABLED=true
OCR_TIMEOUT_SECONDS=600
DEFAULT_GRADE=三年级
DEFAULT_TEXTBOOK_VERSION=人教版
LLM_TIMEOUT_SECONDS=60
HTTP_TIMEOUT_SECONDS=10
SERVICE_STARTUP_WAIT_SECONDS=3
SERVICE_HEALTH_TIMEOUT_SECONDS=3
REDIS_URL=redis://localhost:6379/0
REDIS_TTL_SECONDS=3600
LLM_API_KEY=
LLM_BASE_URL=
LLM_MODEL=
LLM_SYSTEM_PROMPT=你是一个小学数学题目判题专家。你需要根据题目标准答案和学生作答判断对错，并输出严格 JSON。
```

### 配置说明

- `DATABASE_PATH`：SQLite 数据库路径
- `KNOWLEDGE_CSV_PATH`：知识点 CSV 路径
- `API_GATEWAY_PORT`：API 网关端口
- `*_SERVICE_URL`：各内部服务地址
- `KNOWLEDGE_GRAPH_URL`：知识图谱服务地址
- `OCR_SERVICE_URL` / `OCR_ENABLED`：手写 OCR 地址与开关；图片提交由分析服务转发到 OCR 服务
- `OCR_TIMEOUT_SECONDS`：OCR 推理超时；首次模型加载或复杂图片可能耗时数分钟
- `DEFAULT_GRADE` / `DEFAULT_TEXTBOOK_VERSION`：主流程默认年级与教材版本
- `LLM_*`：大模型判题配置
- `REDIS_URL`：启用缓存时填写
- `HTTP_TIMEOUT_SECONDS`：服务间 HTTP 请求超时
- `SERVICE_HEALTH_TIMEOUT_SECONDS`：健康检查超时
- `SERVICE_STARTUP_WAIT_SECONDS`：批量启动时的等待时间

## 本地初始化数据库

首次运行前先初始化数据库：

```bash
python backend/database/init_db.py
```

该脚本会创建数据库表并写入基础知识点、题目、学生、错因等初始数据。

## 启动方式

### 方式一：一键启动所有后端服务

```bash
python backend/start_all.py
```

该方式会按顺序启动：

- Analysis Service
- Error Analysis Agent
- Knowledge Service
- Teaching Service
- State Service
- Insight Service
- Review Scheduler
- API Gateway
- Handwriting OCR Service（端口 8087，独立 Python 环境）

知识检索与错因分析已全部走 SQLite，不需要 Neo4j / 知识图谱服务。

OCR 服务依赖应按 `handwriting_ocr_service/README.md` 安装；若未创建 `handwriting_ocr_service/.venv-vl`，启动脚本会跳过 OCR 服务。

### 启动前端

另开终端运行：

```bash
cd frontend
python -m http.server 3000
```

浏览器访问 `http://127.0.0.1:3000`。

### 方式二：单独启动某个服务

例如启动 API 网关：

```bash
python backend/api_gateway.py
```

启动其他服务也类似：

```bash
python backend/services/analysis_service.py
python backend/services/error_analysis_agent.py
python backend/services/knowledge_service.py
python backend/services/teaching_service.py
python backend/services/state_service.py
python backend/services/review_scheduler.py
```

## 使用 Docker 启动

如果想使用容器化方式，可以直接用项目中的：

- `Dockerfile`
- `docker-compose.yml`
- `nginx.conf`

### 构建并启动

```bash
docker compose up --build
```

默认会启动：

- API Gateway 容器
- Redis 容器

如果你需要前面加 Nginx，可按需把 `nginx.conf` 挂载到 Nginx 容器中。

## 接口入口

- 网关地址：`http://localhost:8000`
- 健康检查：`GET /health`
- 提交入口：`POST /api/v1/submit`
- 学生掌握度：`GET /api/v1/student/{student_id}/mastery`

## 提交接口示例

```bash
curl -X POST http://127.0.0.1:8000/api/v1/submit \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "S-0001",
    "question_id": "Q-0001",
    "original_question": "小明有25颗糖果，小红有38颗糖果，他们一共有多少颗糖果？",
    "student_write": "25+38=63",
    "grade": "三年级"
  }'
```

## Insight 服务（整合同事的新能力）

合并了团队另一条线的进度，全部数据源已切换到本仓库 SQLite，不依赖 Neo4j：

### 初始化用户/演示数据

```bash
python backend/init_insight_data.py
```

会创建 `backend/user_data.db`（用户、错题本、学习进度、答题记录），并写入演示用户 `test_student / 123456` 与 S-0001 的复习演示数据。

### 启动

`backend/start_all.py` 已包含 Insight Service（8010 端口），也可单独启动：

```bash
python backend/insight_service.py
```

### 主要接口（Insight Service，8010）

- 用户：`POST /api/register`、`POST /api/login`、错题本/学习进度/答题记录增删查
- 复习引擎：`POST /api/v1/priority-runs`（优先级快照）、`POST /api/v1/review-plans`（按优先级+知识点覆盖度选题）、`POST /api/v1/review-plans/{id}/start`（会话）、`POST /api/v1/review-sessions/{id}/attempts`（答题）、`POST /api/v1/attempts/{id}/correction`（订正，答错才揭晓答案）
- 成长报告：`GET /api/growth_report/{user_id}`（五维能力/薄弱点/近期进步/学习路径/复习计划）
- 数据看板：`GET /api/datahub/statistics/overview`、`/api/datahub/statistics/class_mastery/{class_id}`、`/api/datahub/comprehensive/{student_id}`

复习计划与会话状态保存在进程内存中（与同事原实现一致），答题结果会写回 `answer_history` 并更新 `knowledge_mastery`。

## Redis 缓存

项目支持 Redis 缓存，但不是强制依赖。

如果未配置 `REDIS_URL`：

- 程序会自动退化为无缓存模式
- 不影响基础功能

建议生产环境至少配置：

```env
REDIS_URL=redis://localhost:6379/0
```

## LLM 判题

如果想启用云端大模型判题，需要配置：

```env
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://your-llm-provider.example.com/v1
LLM_MODEL=your-model-name
```

只要这些项有效，网关会在拿到标准答案后，优先调用 LLM 进行判题校正。

## OCR 识别（手写作业识别）

仓库里的 `handwriting_ocr_service/` 是独立的手写 OCR 服务（PaddleOCR-VL-1.6，端口 8087），负责把图片转录成 Markdown。主流程已接入：

### 配置

```env
OCR_ENABLED=true
OCR_SERVICE_URL=http://127.0.0.1:8087
OCR_TIMEOUT_SECONDS=600
OCR_MIN_CONFIDENCE=0.3
```

注意：PaddleOCR-VL 返回的 `confidence` 是"版面检测兼容性质量评分"，不是逐字识别准确率（实测完美识别的图片约 0.49）。因此阈值默认设得较低（0.3），OCR 服务侧的 `OCR_CONFIDENCE_THRESHOLD`（handwriting_ocr_service/.env）同理设为 0.3，避免把正常结果误判为低置信度。

### 工作方式

- `POST /api/v1/submit` 携带 `image`（base64）时，Analysis Service 会先调用 OCR 服务识别；
- 识别出的整段文字再做"题目 / 学生作答"分离：配置了 LLM 时用 LLM 分离，否则走规则兜底（优先取 OCR 返回的题目块）；
- 识别置信度低于 `OCR_MIN_CONFIDENCE` 或返回 `low_confidence` 时：如果请求同时带了文本（`original_question`/`student_write`）则回退文本，否则返回 `OCR failed: low_confidence` 提示人工处理；
- OCR 服务未启动/不可用时：有文本输入则自动回退文本，不影响主链路；
- 没传 `image` 或 `OCR_ENABLED=false`：直接走文本输入。

### 启动 OCR 服务

OCR 服务需要独立的 Python 3.12 + PaddlePaddle 环境（与主后端隔离），按 `handwriting_ocr_service/README.md` 安装：

```powershell
cd handwriting_ocr_service
py -3.12 -m venv .venv-vl
.\.venv-vl\Scripts\python.exe -m pip install paddlepaddle==3.3.1 -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
.\.venv-vl\Scripts\python.exe -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
.\.venv-vl\Scripts\python.exe -m uvicorn app.main:app --port 8087
```

检测到 `.venv-vl` 后，`python backend/start_all.py` 会自动一并启动 OCR 服务（首次启动会下载约 1.9GB 模型，日志在 `backend/logs/OCR_Service.log`）。没装环境时 start_all 会跳过 OCR，主流程自动回退，不影响其他功能。

模型下载源和缓存目录在 `handwriting_ocr_service/.env` 配置（参考 `.env.example`）：

```env
PADDLE_PDX_MODEL_SOURCE=modelscope   # bos / modelscope / huggingface，bos 卡住时可换 modelscope
PADDLE_PDX_CACHE_HOME=D:\PaddleOCRCache  # 建议放非系统盘
```

## 部署建议

- 生产环境建议使用 PostgreSQL/MySQL 替代 SQLite
- 网关前建议使用 Nginx 反向代理
- 服务建议使用多个 worker 运行
- Redis 建议独立部署，用于缓存标准答案、知识点和频率限制
- 外部 LLM 调用建议配置超时与重试

## 当前仓库说明

本仓库已经完成：

- 统一配置读取
- Redis 缓存接入
- LLM 判题接入与降级
- 基础部署容器文件
- 基础日志与健康检查增强
- 用户账号体系（注册/登录/错题本/学习进度/答题记录）
- 动态复习引擎（优先级排序选题 + 复习会话 + 集中订正）
- 成长报告与数据看板（五维能力、薄弱点、学习路径、统计）
- 知识图谱依赖移除：知识检索与错因候选全部走 SQLite，不再需要 Neo4j

已知事项：

- 知识点编号存在两套体系（K-* 与 G-N-*），知识服务已做名称模糊回退兜底，后续建议统一编号。
- 防抄袭检测按会议决定暂缓，接口保留但已禁用（避免"63"这类正确答案被误判）。

## 为什么数据库统一用 SQLite 而不是知识图谱（Neo4j）

这是个有意的架构取舍，不是简单降级：

1. **可独立运行、零外部依赖**：Neo4j 需要单独部署服务器和账号；当前仓库没有 `kg_service/`，之前微服务强依赖 8007 端口导致"知识图谱服务不存在就整条链路 500"。全部走 SQLite 后，`start_all.py` 一键就能把整套服务跑起来。
2. **当前功能用到的关系深度很浅**：现在的关系最多 1–2 跳（题目→知识点、错题→错因、知识点先修/后续），用关联表 + JOIN 完全够，图数据库的多跳/变长路径优势暂时用不上。
3. **数据分层与会议方向一致**：会议定的方向是"账号等基础信息拆到关系型数据库，题目/知识点做向量化放图/向量库"。现在账号（user_data.db）和业务数据（example_db.db）都落在关系库，正是这个方向的前半段；知识点/题目关系后续真正要做学习路径、易混推荐、相似题向量检索时，再迁到 Neo4j/向量库，SQLite 保持为唯一真源，加一层同步即可。
4. **成本**：图库的运维、备份、导入成本更高，在核心链路还没跑通前引入属于过早优化。

如果后续要接回 Neo4j，`backend/config.py` 里的 `KNOWLEDGE_GRAPH_URL` 已作为占位保留。
