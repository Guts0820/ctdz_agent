# Repository Guidelines

## 模块定位与架构

本仓库是数学错题分析系统的完整项目。`frontend/` 是静态浏览器前端；`backend/api_gateway.py`（8000）接收其作业请求，依次协调分析、错因、知识、教学、状态和复习服务；各服务通过本地 HTTP 调用，并使用 SQLite 保存业务数据。`backend/all_in_one.py` 是单进程演示入口；`backend/start_all.py` 负责多进程启动，若不存在 `kg_service/` 会跳过知识图谱服务。根目录的 `handwriting_ocr_service/` 是独立的图片转 Markdown OCR 服务；分析服务会将前端 Data URL 转发给它（默认 8087）。

## 项目结构

- `backend/services/`：各 FastAPI 服务及共享工具；新增服务使用 `<domain>_service.py` 命名。
- `backend/database/`：建库脚本、SQLite 示例库和知识点 CSV；`init_db.py` 是数据库初始化入口。
- `backend/api_gateway.py`：对外路由与服务编排；`backend/contracts/`、`api/` 和 `state_machine/` 存放契约、接口和状态转换说明。
- `backend/logs/`：运行日志，不应手工提交其生成内容。
- `frontend/`：无构建步骤的静态前端；其自身 `AGENTS.md` 说明页面与 API 调用约束。
- `handwriting_ocr_service/`：独立 FastAPI OCR 子项目，详见其自身 `AGENTS.md` 与 `README.md`。

## 开发与运行

仓库未提供依赖锁定文件；根据导入可安装 `fastapi`、`uvicorn`、`pydantic` 和 `requests`（其他依赖待确认）。从仓库根目录执行：

```powershell
python backend/database/init_db.py   # 初始化 SQLite 数据
python backend/all_in_one.py        # 启动单进程 API，端口 8000
python backend/start_all.py         # 启动多服务和 OCR；缺少 kg_service 时自动跳过
cd frontend; python -m http.server 3000  # 启动静态前端
```

服务代码可单独运行，例如 `python backend/services/analysis_service.py`（8081）。

## 编码与测试规范

使用 Python，遵循现有四空格缩进、`snake_case` 函数/变量和 `PascalCase` Pydantic 模型。为请求模型添加类型标注；跨服务请求应设置超时并调用 `raise_for_status()`；OCR 请求使用 `OCR_SERVICE_URL` 和独立的 `OCR_TIMEOUT_SECONDS`，不得将图片内容写入日志；SQL 均使用参数化查询。配置应来自环境变量或非提交的本地文件，勿提交密钥、数据库副本或日志。

当前未发现测试框架或覆盖率门槛。新增行为时，在新建的 `tests/test_<功能>.py` 中补充 pytest 测试，至少覆盖成功路径和服务/数据库失败路径；测试命令为 `pytest`（安装 pytest 后）。

## 提交与修改指南

现有历史只使用 “Add files via upload”，未形成提交规范。请改用简短祈使句，例如 `Fix state update for missing knowledge ID`。提交前初始化独立测试数据库并手动检查 `/health` 与受影响接口；更新契约或返回字段时同步修改 `backend/api/endpoints.md` 和 `backend/contracts/service_contracts.md`。PR 应说明影响服务、验证命令和兼容性；接口响应变化附示例。
