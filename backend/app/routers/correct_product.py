from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
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
def correct_product(data: CorrectProductRequest, db: Session = Depends(get_db)):
    """
    POST /correct-product
    
    1. Находит правильный продукт по product_id
    2. Создаёт CorrectionReport для последующей модерации
    3. Если передан user_id — вычисляет новый AI-вердикт
    4. Возвращает обновлённые данные продукта мгновенно (без перезагрузки)
    """
    # 1. Проверяем что правильный продукт существует
    correct_product = db.query(Product).filter(Product.id == data.product_id).first()
    if not correct_product:
        raise HTTPException(status_code=404, detail="Продукт не найден")

    # 2. Создаём запись для модерации
    report = CorrectionReport(
        user_id=data.user_id,
        product_id=correct_product.id,
        correct_name=correct_product.name,
    )
    db.add(report)
    db.commit()

    # 3. Формируем ответ с обновлённым вердиктом
    result = ProductWithVerdict.model_validate(correct_product)

    if data.user_id is not None:
        user = db.query(UserProfile).filter(UserProfile.id == data.user_id).first()
        if user:
            verdict = get_ai_verdict(user, correct_product)
            result = result.model_copy(update={
                "verdict": verdict.verdict,
                "verdict_text": verdict.explanation,
                "verdict_is_mock": verdict.is_mock,
            })

    return result
