from functools import lru_cache

from fastapi import FastAPI, File, HTTPException, UploadFile
from dotenv import load_dotenv
from starlette.concurrency import run_in_threadpool

from app.config import Settings
from app.models import RecognitionResult
from app.services.paddleocr_vl import PaddleOCRVLEngine
from app.services.qwen_vision import QwenVisionEngine
from app.services.recognition_service import RecognitionService

load_dotenv()

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/bmp"}
settings = Settings.from_env()


@lru_cache
def build_recognition_service() -> RecognitionService:
    fallback_engine = QwenVisionEngine(settings) if settings.qwen_is_configured else None
    return RecognitionService(
        primary_engine=PaddleOCRVLEngine(
            device=settings.paddleocr_vl_device,
            pipeline_version=settings.paddleocr_vl_pipeline_version,
        ),
        fallback_engine=fallback_engine,
        confidence_threshold=settings.confidence_threshold,
    )


def _recognize_image(image_bytes: bytes, content_type: str) -> RecognitionResult:
    """Initialize the cached model and run inference in the worker thread."""
    return build_recognition_service().recognize(image_bytes, content_type)


app = FastAPI(title="Handwriting OCR Service", version="0.1.0")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/v1/recognize")
async def recognize_handwriting(image: UploadFile = File(...)) -> dict[str, object]:
    content_type = image.content_type or ""
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG, WebP, and BMP images are supported.")

    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="The uploaded image is empty.")
    if len(image_bytes) > settings.max_image_bytes:
        raise HTTPException(status_code=413, detail="The uploaded image exceeds the configured size limit.")

    try:
        result = await run_in_threadpool(
            _recognize_image,
            image_bytes,
            content_type,
        )
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail="Image recognition failed.") from error

    return result.as_dict()
