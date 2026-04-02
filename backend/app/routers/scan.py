import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.schemas.scan import ScanResponse
from app.services.vision import recognize_food_from_bytes

router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/scan", response_model=ScanResponse)
async def scan_food(file: UploadFile = File(...)):
    """
    Принимает фото еды → Gemini Vision → возвращает название продукта.
    Нет сохранения на диск — байты идут напрямую в API.
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Неподдерживаемый формат. Разрешены: JPEG, PNG, WebP"
        )

    contents = await file.read()
    result = await asyncio.to_thread(
        recognize_food_from_bytes,
        image_bytes=contents,
        mime_type=file.content_type or "image/jpeg",
    )

    return ScanResponse(
        detected_name=result.detected_name,
        is_mock=result.is_mock,
    )
