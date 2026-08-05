# ctdz_agent_backend

这是一个面向小学数学错题分析、知识图谱检索与智能教学的后端项目，采用多服务架构，包含 API 网关、答题分析、错因分析、知识服务、教学服务、状态服务和复习调度服务。

## 项目结构

- `backend/api_gateway.py`：统一入口，负责提交作业后的服务编排
- `backend/services/analysis_service.py`：OCR/答题分析、判题基础结果生成
- `backend/services/error_analysis_agent.py`：错因分析与错误标签生成
- `backend/services/knowledge_service.py`：知识点检索
- `backend/services/teaching_service.py`：教学内容生成与频率控制
- `backend/services/state_service.py`：掌握度更新与复习计划生成
- `backend/services/review_scheduler.py`：复习任务调度
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
KNOWLEDGE_GRAPH_URL=http://127.0.0.1:8007
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

- 知识图谱服务（如果仓库中存在 `kg_service/`）
- Analysis Service
- Error Analysis Agent
- Knowledge Service
- Teaching Service
- State Service
- Review Scheduler
- API Gateway

注意：当前仓库中未包含 `kg_service/` 目录，因此如果你没有单独补齐该服务，`start_all.py` 里启动知识图谱服务这一步会失败。其余服务仍可单独启动。

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

如果你准备继续扩展知识图谱服务，请补齐 `kg_service/` 目录及其 Neo4j 配置。
