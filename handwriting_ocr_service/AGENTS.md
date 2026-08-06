# Repository Guidelines

## 模块定位

本模块是可独立运行的手写文本识别服务，为上层错题分析后端提供图片到 Markdown 的标准化转换。它不判断答案正误、不生成教学内容；这些职责仍属于上层的分析与教学服务。

## 架构

FastAPI 接收图片后，默认通过 `PaddleOCRVLEngine` 调用完整的 PaddleOCR-VL-1.6 流程，将版面、手写正文和公式直接转换为 Markdown。适配器会为裸 LaTeX 命令补充 `$...$` 数学分隔符，并跳过已有分隔符和代码块。`RecognitionService` 负责质量检查与 Qwen 兜底；VL 不提供旧 PP-OCR 的逐行识别分数，因此 `confidence` 仅保留为版面质量兼容字段，兜底以空输出、异常重复等 `review_required` 信号为准。服务仅使用 PaddleOCR-VL（GPU 推理），已移除旧 PP-OCR 与 Pix2Text 引擎。

## 目录结构

- `app/main.py`：HTTP 入口与健康检查。
- `interactive_ocr.py`：输入图片绝对路径并将识别结果写入 Markdown 的本地交互入口。
- `app/services/paddleocr_vl.py`：PaddleOCR-VL-1.6 适配器、Markdown 提取与质量检查。
- `app/services/`：识别编排、PaddleOCR-VL 适配器、Qwen 兜底和 Markdown 格式化。
- `app/models.py`：跨层结果模型。
- `tests/`：无需模型或网络的 pytest 单元测试。
- `recognition_results/`：交互测试生成的本地结果目录，已被 Git 忽略。
- `.env.example`：OCR 路由、VL 运行设备和 Qwen 视觉模型的非敏感配置模板。
- `requirements.txt`：VL 核心依赖。

## 开发规范

使用 Python 3.12、四空格缩进、类型标注和 `snake_case`。VL 必须使用完整产线，不能用裸 VLM 请求代替版面分析；本机 CPU 服务应保持单 worker，模型初始化和推理在线程池中执行，并使用引擎锁防止并行请求耗尽内存。引擎调用应有明确异常；不得记录原始作业图片、API Key 或完整识别内容到日志。配置仅从环境变量读取，禁止提交 `.env`、模型缓存和虚拟环境。

## 常用命令

在本目录用 `py -3.12 -m venv .venv-vl` 创建环境；先从飞桨 CPU 源安装 `paddlepaddle==3.3.1`，再通过国内镜像执行 `.venv-vl\Scripts\python.exe -m pip install -r requirements.txt`。运行 `.venv-vl\Scripts\python.exe -m pytest` 测试，运行 `.venv-vl\Scripts\python.exe -m uvicorn app.main:app --port 8087 --workers 1` 启动服务。`interactive_ocr.py` 是本地图片转 Markdown 入口。

## 修改指南

修改识别分流、质量检查或 Markdown 输出前先补充失败测试。保持 API 的 `markdown`、`confidence`、`engine` 和 `fallback_used` 字段兼容；不要用版面分数宣称逐字识别置信度。更换 VL 版本时同时验证原生 Markdown、公式、空结果、Qwen 兜底、CPU 耗时和内存；保留旧引擎回滚路径直至真实数据集 A/B 验证完成。不得提交 `recognition_results/` 中可能包含学生作业内容的文件。
