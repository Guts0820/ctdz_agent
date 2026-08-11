# Handwriting OCR Service

独立的图片转 Markdown FastAPI 服务。默认使用完整的 PaddleOCR-VL-1.6 流程统一识别正文、手写内容和 LaTeX 数学公式；服务只负责忠实转录，不判断答案对错，也不修改算式。Qwen 视觉模型仍可作为异常结果的云端兜底。

## 运行环境

本机已验证 Windows 11、Python 3.12、PaddlePaddle 3.3.1 GPU 版（CUDA 12.6）和 PaddleOCR-VL-1.6。建议使用隔离环境：

```powershell
py -3.12 -m venv .venv-vl
.\.venv-vl\Scripts\python.exe -m pip install paddlepaddle-gpu==3.3.1 `
  -i https://www.paddlepaddle.org.cn/packages/stable/cu126/
.\.venv-vl\Scripts\python.exe -m pip install -r requirements.txt `
  -i https://pypi.tuna.tsinghua.edu.cn/simple
.\.venv-vl\Scripts\python.exe -m pip check
```

模型首次使用时下载到 `PADDLE_PDX_CACHE_HOME`。当前开发机缓存为 `D:\PaddleOCRCache`，PaddleOCR-VL-1.6 与版面模型共约 1.92 GB。RTX 4060 Laptop 上首次加载约 50 秒，稳态单张推理约 2 秒；实际耗时随图片内容变化。

## 配置

复制 `.env.example` 为 `.env`。默认主引擎配置为：

```env
PADDLEOCR_VL_DEVICE=gpu
PADDLEOCR_VL_PIPELINE_VERSION=v1.6
```

服务仅使用 PaddleOCR-VL（GPU 推理），已移除旧 PP-OCR 与 Pix2Text 引擎。

## 启动与调用

```powershell
.\.venv-vl\Scripts\python.exe -m pytest
.\.venv-vl\Scripts\python.exe -m uvicorn app.main:app --port 8087 --workers 1
```

上传图片：

```powershell
curl.exe -X POST "http://127.0.0.1:8087/v1/recognize" `
  -F "image=@C:\path\exercise.png;type=image/png"
```

支持 JPEG、PNG、WebP 和 BMP，默认最大 10 MB。响应保留 `markdown`、`confidence`、`engine`、`fallback_used`、`status` 字段。VL 的 `confidence` 是基于版面检测的兼容性质量评分，不是逐字准确率；空结果或异常重复会标记为 `low_confidence`，配置 Qwen 后会触发复核。

也可运行 `.\.venv-vl\Scripts\python.exe interactive_ocr.py`，连续输入图片绝对路径，将 Markdown 保存到 `recognition_results/`；输入 `exit` 退出。

## 实现说明

`app/services/paddleocr_vl.py` 封装 `PaddleOCRVL(pipeline_version="v1.6", device="gpu")`，串行化本地推理并清理临时图片。适配器会将裸 `\times`、`\frac`、`\div`、`\sqrt` 等 LaTeX 命令自动包入 `$...$`，但保留已有公式分隔符和代码块。API 将模型初始化和 GPU 推理整体放在线程池中，部署时保持单 worker，避免首次加载阻塞事件循环或并发加载模型。
