from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.product import Product
from app.models.user import UserProfile
from app.schemas.product import ProductWithVerdict
from app.services.ai_advisor import get_ai_verdict
from app.services.openfoodfacts import fetch_and_save_from_openfoodfacts

router = APIRouter()


@router.get(
    "/barcode",
    response_model=ProductWithVerdict,
    summary="Поиск продукта по штрихкоду",
    responses={
        200: {"description": "Продукт найден"},
        404: {"description": "Продукт не найден в базе"},
    },
)
async def get_product_by_barcode(
    code: str,
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    GET /barcode?code=4607001854           → продукт без вердикта
    GET /barcode?code=4607001854&user_id=1 → продукт + AI-вердикт

    Логика:
      1. Ищем в локальной БД по barcode.
      2. Не нашли → ищем в Open Food Facts (async httpx) и сохраняем.
      3. Опять не нашли → 404.
      4. Если передан user_id — вызываем Gemini AI-советника (async).
    """
    # Async select
    result = await db.execute(select(Product).where(Product.barcode == code))
    product = result.scalar_one_or_none()

    if not product:
        # Async-интеграция с Open Food Facts
        product = await fetch_and_save_from_openfoodfacts(code, db)

        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Продукт со штрихкодом '{code}' не найден ни у нас, ни в Open Food Facts",
            )

    # Базовый ответ
    response = ProductWithVerdict.model_validate(product)

    # AI-вердикт — только если передан user_id
    if user_id is not None:
        user_result = await db.execute(select(UserProfile).where(UserProfile.id == user_id))
        user = user_result.scalar_one_or_none()
        if user:
            verdict = await get_ai_verdict(user, product)
            response = response.model_copy(update={
                "verdict": verdict.verdict,
                "verdict_text": verdict.explanation,
                "verdict_is_mock": verdict.is_mock,
            })

    return response
