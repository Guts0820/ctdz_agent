# Handwriting OCR Service

独立的图片转 Markdown FastAPI 服务。默认使用完整的 PaddleOCR-VL-1.6 流程统一识别正文、手写内容和 LaTeX 数学公式；服务只负责忠实转录，不判断答案对错，也不修改算式。Qwen 视觉模型仍可作为异常结果的云端兜底。

## 运行环境

本机已验证 Windows 11、Python 3.12、PaddlePaddle 3.3.1 CPU 版和 PaddleOCR 3.7.0。建议使用隔离环境，避免旧 Pix2Text/PyTorch 依赖影响 VL：

```powershell
py -3.12 -m venv .venv-vl
.\.venv-vl\Scripts\python.exe -m pip install paddlepaddle==3.3.1 `
  -i https://www.paddlepaddle.org.cn/packages/stable/cpu/
.\.venv-vl\Scripts\python.exe -m pip install -r requirements.txt `
  -i https://pypi.tuna.tsinghua.edu.cn/simple
.\.venv-vl\Scripts\python.exe -m pip check
```

模型首次使用时下载到 `PADDLE_PDX_CACHE_HOME`。当前 Windows 默认缓存为 `C:\PaddleOCRCache`，PaddleOCR-VL-1.6 与版面模型共约 1.92 GB。当前开发机首次下载并初始化约 321 秒，单张复杂练习图片 CPU 推理约 264 秒；实际耗时随图片内容变化。

## 配置

复制 `.env.example` 为 `.env`。默认主引擎配置为：

```env
OCR_ENGINE=paddleocr_vl
PADDLEOCR_VL_DEVICE=cpu
PADDLEOCR_VL_PIPELINE_VERSION=v1.6
PIX2TEXT_ENABLED=false
```

VL 已支持公式 Markdown，因此不会再调用 Pix2Text。若需要回滚到旧 PP-OCR，将 `OCR_ENGINE` 改为 `paddleocr_legacy`。仅在旧引擎下需要 Pix2Text 时，执行 `python -m pip install -r requirements-pix2text.txt` 后再显式启用。

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

支持 JPEG、PNG、WebP 和 BMP，默认最大 10 MB。响应保留 `markdown`、`confidence`、`engine`、`fallback_used`、`status`、`formula_engine` 和 `formula_confidence` 字段。VL 的 `confidence` 是基于版面检测的兼容性质量评分，不是逐字准确率；空结果或异常重复会标记为 `low_confidence`，配置 Qwen 后会触发复核。

也可运行 `.\.venv-vl\Scripts\python.exe interactive_ocr.py`，连续输入图片绝对路径，将 Markdown 保存到 `recognition_results/`；输入 `exit` 退出。

## 实现说明

`app/services/paddleocr_vl.py` 封装 `PaddleOCRVL(pipeline_version="v1.6", device="cpu")`，串行化本地推理并清理临时图片。适配器会将裸 `\times`、`\frac`、`\div`、`\sqrt` 等 LaTeX 命令自动包入 `$...$`，但保留已有公式分隔符和代码块。VL 原生 Markdown 会直接进入响应，公式不会被 Pix2Text 重复附加。API 将模型初始化和 CPU 推理整体放在线程池中，部署时保持单 worker，避免首次加载阻塞事件循环或并发加载模型。
