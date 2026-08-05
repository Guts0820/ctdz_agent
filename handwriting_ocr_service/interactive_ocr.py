import json
from pathlib import Path
from typing import Callable, Protocol

from app.models import RecognitionResult


SUPPORTED_CONTENT_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "recognition_results"


class RecognitionServiceLike(Protocol):
    def recognize(self, image_bytes: bytes, content_type: str) -> RecognitionResult:
        """Return the normalized recognition result for one image."""


def validate_image_path(raw_path: str) -> Path:
    """Validate user input and return an existing absolute image path."""
    normalized = raw_path.strip()
    if (
        len(normalized) >= 2
        and normalized[0] == normalized[-1]
        and normalized[0] in {'"', "'"}
    ):
        normalized = normalized[1:-1].strip()

    if not normalized:
        raise ValueError("图片路径不能为空。")

    image_path = Path(normalized)
    if not image_path.is_absolute():
        raise ValueError("请输入图片的绝对路径。")
    if not image_path.is_file():
        raise ValueError("图片文件不存在或路径不是文件。")
    if image_path.suffix.lower() not in SUPPORTED_CONTENT_TYPES:
        supported = ", ".join(sorted(SUPPORTED_CONTENT_TYPES))
        raise ValueError(f"不支持该图片格式，支持的扩展名：{supported}。")
    return image_path


def recognize_image_to_markdown(
    image_path: Path,
    output_dir: Path,
    service: RecognitionServiceLike,
) -> Path:
    """Recognize one image and save its Markdown without overwriting old output."""
    validated_path = validate_image_path(str(image_path))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = _next_output_path(output_dir, validated_path.stem)
    content_type = SUPPORTED_CONTENT_TYPES[validated_path.suffix.lower()]

    result = service.recognize(validated_path.read_bytes(), content_type)
    output_path.write_text(result.markdown, encoding="utf-8")
    structured_path = output_path.with_suffix(".json")
    structured_path.write_text(json.dumps(result.as_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def run_interactive(
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    service_factory: Callable[[], RecognitionServiceLike] | None = None,
) -> None:
    """Run the image-path prompt until the user enters ``exit``."""
    output_dir.mkdir(parents=True, exist_ok=True)
    print_fn(f"识别结果目录：{output_dir}")
    print_fn("请输入图片绝对路径；输入 exit 退出。")

    build_service = service_factory or _build_default_service
    service: RecognitionServiceLike | None = None

    while True:
        try:
            raw_path = input_fn("图片路径> ")
        except (EOFError, KeyboardInterrupt):
            print_fn("\n已退出手写 OCR 测试。")
            return

        if raw_path.strip().lower() == "exit":
            print_fn("已退出手写 OCR 测试。")
            return

        try:
            image_path = validate_image_path(raw_path)
            if service is None:
                print_fn("正在加载识别模型，首次运行可能需要一些时间……")
                service = build_service()
            output_path = recognize_image_to_markdown(image_path, output_dir, service)
        except Exception as error:
            print_fn(f"识别失败：{error}")
            continue

        print_fn(f"识别完成：{output_path}")


def _next_output_path(output_dir: Path, image_stem: str) -> Path:
    candidate = output_dir / f"{image_stem}.md"
    suffix_number = 2
    while candidate.exists():
        candidate = output_dir / f"{image_stem}_{suffix_number}.md"
        suffix_number += 1
    return candidate


def _build_default_service() -> RecognitionServiceLike:
    from app.main import build_recognition_service

    return build_recognition_service()


if __name__ == "__main__":
    run_interactive()
