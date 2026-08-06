# 手写数学公式识别测试报告

> 注：本文为历史测试记录。旧 PP-OCR（paddleocr_legacy）与 Pix2Text 引擎已移除，
> 当前服务仅使用 PaddleOCR-VL（GPU 推理）。

## 结论摘要

初始测试因 PaddleOCR 2.x/3.x API 不兼容而失败；该问题现已修复。修复后的 PaddleOCR 主引擎已成功加载模型并完成真实图片冒烟识别。当前仍未完成 939 张图片的全量准确率评估，因为文件名真值编码规则尚未确认。

## 测试对象与数据集

- 测试服务：`handwriting_ocr_service` 当前工作区版本。
- 数据集：`TAL_OCR_MATH`，共 **939** 张 JPG，合计 **2,388,364 bytes**（约 2.28 MiB）。
- 内容：小学算术/公式手写图片。
- 标注情况：未发现独立标注文件；文件名包含多段相似字符串和编码字符，无法在未确认标签规则的情况下作为可靠真值。因此本报告不计算字符错误率（CER）、公式完全匹配率或准确率。

## 环境

- Python 3.12.9
- PaddlePaddle 3.3.1
- PaddleOCR 3.7.0
- Pix2Text 1.1.6（服务默认关闭，需显式启用）
- PyTorch 2.13.0

依赖安装使用了阿里云 PyPI 镜像。基础单元测试可运行：3 个测试文件共 7 项通过；这些测试验证配置读取、服务分流、Markdown 格式化和 PaddleOCR 3.x 适配，不加载真实 OCR 模型。

## 实际执行结果

### 初始失败记录

当前主识别器在 `app/services/paddle_ocr.py` 中执行：

```python
PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)
```

初始化立即抛出：

```text
ValueError: Unknown argument: show_log
```

因此：

| 指标 | 结果 |
| --- | --- |
| 已尝试初始化主 OCR 引擎 | 是 |
| 成功初始化 | 否 |
| 实际送入模型的图片数 | 0 / 939 |
| 成功输出 Markdown 的图片数 | 0 |
| Pix2Text 公式识别 | 未执行（主引擎初始化先失败） |
| Qwen 视觉兜底 | 未执行（未配置且主流程未进入识别阶段） |

## 修复后复测

适配器已更新为 PaddleOCR 3.x 的 `predict()` 接口，并关闭不必要的文档预处理与 Windows CPU oneDNN 默认加速；模型源固定为 BOS，模型缓存改为 ASCII 路径 `C:\\PaddleOCRCache`。

### 单元测试

`python -m pytest -q` 共 **7 项全部通过**（包含 `tests/test_config.py`）。测试不依赖外部模型或网络。

### 真实图片冒烟测试

从数据集按文件名排序抽取前 10 张图片，使用同一个 PaddleOCR 引擎实例逐张识别：

| 指标 | 结果 |
| --- | --- |
| 样本数 | 10 |
| 非空输出 | 9 / 10 |
| 平均耗时 | 0.519 秒/张 |
| 平均置信度 | 0.8306 |
| 识别成功示例 | `-(9+1)=1`（置信度 0.9426） |

单张完整验证使用模块虚拟环境 `.venv\Scripts\python.exe` 执行，PaddleOCR 检测模型与识别模型均从 `C:\PaddleOCRCache` 命中缓存；未再出现 `Unknown argument: show_log` 或 Windows CPU 推理器初始化错误。

抽样中出现了空输出、数字粘连和算式误读，例如 `(28.22)=Z2_...` 被识别为多行数字，说明当前通用模型可以运行，但还不能代表小学手写算术公式的可靠识别率。

## 原因与影响

初版项目实现基于 PaddleOCR 2.x 的经典 `ocr()` 调用方式，而依赖安装到了 PaddleOCR 3.7.0。3.x 不接受 `show_log` 参数，且结果需从 `predict()` 的 `rec_texts`/`rec_scores` 字段读取。修复后该兼容性问题已解除。

## 建议的后续步骤

1. 对 939 张图片做全量测试并记录成功率、平均耗时、CER 和公式 LaTeX 完全匹配率。
2. 确认数据集文件名中真值文本的编码规则，或补充标准标注文件；否则只能报告可用性和人工抽样质量，不能报告准确率。
3. 独立记录 PaddleOCR 正文、Pix2Text 公式和 Qwen 兜底的输出，以比较各层对手写算术符号的贡献。

## 当前运行约束

- `PIX2TEXT_ENABLED=false` 是默认值；Pix2Text 首次加载会下载较大模型，完成缓存后再设置为 `true`。
- Qwen 仅在 `.env` 同时提供 API Key、Base URL、模型名并设置 `QWEN_VISION_FALLBACK_ENABLED=true` 时启用；`.env` 不得提交。
- `.gitignore` 已忽略 `.venv/`、缓存、字节码和 `.env`，不会把虚拟环境依赖上传到仓库。
