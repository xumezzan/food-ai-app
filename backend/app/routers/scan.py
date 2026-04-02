import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Optional

from app.schemas.scan import ScanResponse
from app.services.vision import recognize_food_from_bytes
from app.services.auth import AuthUser, get_current_user
from app.services.rate_limiter import check_and_increment_scan_limit

router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/scan", response_model=ScanResponse)
async def scan_food(
    file: UploadFile = File(...),
    current_user: AuthUser = Depends(get_current_user),
):
    """
    Принимает фото еды → Gemini Vision → возвращает название продукта.

    🔒 Требует авторизацию: Authorization: Bearer <firebase_token>
    ⏱️  Rate limit: 50 сканирований/день (Free) | без лимита (Premium)
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Неподдерживаемый формат. Разрешены: JPEG, PNG, WebP"
        )

    # Проверяем лимит ПЕРЕД обращением к ИИ (экономим токены Gemini)
    if current_user.db_user_id is not None:
        await check_and_increment_scan_limit(
            user_id=current_user.db_user_id,
            is_premium=current_user.is_premium,
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
