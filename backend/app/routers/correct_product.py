from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models.correction import CorrectionReport
from app.models.product import Product
from app.models.user import UserProfile
from app.schemas.product import ProductWithVerdict
from app.services.ai_advisor import get_ai_verdict

router = APIRouter()


class CorrectProductRequest(BaseModel):
    barcode: str          # штрихкод неверно распознанного продукта
    product_id: int       # ID правильного продукта из базы
    user_id: Optional[int] = None


@router.post("/correct-product", response_model=ProductWithVerdict)
async def correct_product(data: CorrectProductRequest, db: AsyncSession = Depends(get_db)):
    """
    POST /correct-product

    1. Находит правильный продукт по product_id
    2. Создаёт CorrectionReport для последующей модерации
    3. Если передан user_id — вычисляет новый AI-вердикт (async)
    4. Возвращает обновлённые данные продукта мгновенно
    """
    # 1. Проверяем что правильный продукт существует
    result = await db.execute(select(Product).where(Product.id == data.product_id))
    correct = result.scalar_one_or_none()
    if not correct:
        raise HTTPException(status_code=404, detail="Продукт не найден")

    # 2. Создаём запись для модерации
    report = CorrectionReport(
        user_id=data.user_id,
        product_id=correct.id,
        correct_name=correct.name,
    )
    db.add(report)
    await db.commit()

    # 3. Формируем ответ с обновлённым вердиктом
    response = ProductWithVerdict.model_validate(correct)

    if data.user_id is not None:
        user_result = await db.execute(select(UserProfile).where(UserProfile.id == data.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            verdict = await get_ai_verdict(user, correct)
            response = response.model_copy(update={
                "verdict": verdict.verdict,
                "verdict_text": verdict.explanation,
                "verdict_is_mock": verdict.is_mock,
            })

    return response
