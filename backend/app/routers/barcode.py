from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

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
def get_product_by_barcode(
    code: str,
    user_id: Optional[int] = None,     # если передан — добавляем AI-вердикт
    db: Session = Depends(get_db),
):
    """
    GET /barcode?code=4607001854           → продукт без вердикта
    GET /barcode?code=4607001854&user_id=1 → продукт + AI-вердикт диетолога

    Логика:
      1. Ищем в локальной БД по barcode.
      2. Не нашли → ищем в Open Food Facts и сохраняем локально.
      3. Опять не нашли → 404.
      4. Если передан user_id — вызываем Gemini AI-советника.
    """
    product = db.query(Product).filter(Product.barcode == code).first()

    if not product:
        # Интеграция с внешним бесплатным API
        product = fetch_and_save_from_openfoodfacts(code, db)
        
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Продукт со штрихкодом '{code}' не найден ни у нас, ни в Open Food Facts",
            )

    # Базовый ответ
    result = ProductWithVerdict.model_validate(product)

    # AI-вердикт — только если передан user_id
    if user_id is not None:
        user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
        if user:
            verdict = get_ai_verdict(user, product)
            result = result.model_copy(update={
                "verdict": verdict.verdict,
                "verdict_text": verdict.explanation,
                "verdict_is_mock": verdict.is_mock,
            })

    return result
