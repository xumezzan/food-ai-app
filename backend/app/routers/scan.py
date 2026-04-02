import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException, Request

from app.schemas.scan import ScanResponse
from app.services.vision import recognize_food_from_bytes
from app.services.rate_limiter import check_ip_scan_limit

router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/scan", response_model=ScanResponse)
async def scan_food(
    request: Request,
    file: UploadFile = File(...),
):
    """
    Принимает фото еды → Gemini Vision → возвращает название продукта.

    ⏱️  Rate limit: 50 сканирований/день с одного IP (без авторизации).
    🔮 После добавления Firebase Auth — лимит привяжется к пользователю.
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Неподдерживаемый формат. Разрешены: JPEG, PNG, WebP"
        )

    # Rate limit по IP-адресу
    client_ip = request.client.host if request.client else "unknown"
    await check_ip_scan_limit(client_ip)

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
