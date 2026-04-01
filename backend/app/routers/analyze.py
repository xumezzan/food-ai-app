from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product
from app.models.user import UserProfile
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.services.ai_advisor import get_ai_verdict

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(data: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    Анализирует продукт с учётом цели пользователя.
    Использует Gemini AI (единый советник для всего приложения).
    """
    user = db.query(UserProfile).filter(UserProfile.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    product = db.query(Product).filter(Product.name.ilike(data.name)).first()

    if not product:
        return AnalyzeResponse(
            name=data.name,
            calories=0, protein=0, fat=0, carbs=0,
            verdict="yellow",
            verdict_text=f"Продукт '{data.name}' не найден в базе. Оценка недоступна.",
            verdict_is_mock=True
        )

    verdict = get_ai_verdict(user, product)

    return AnalyzeResponse(
        name=product.name,
        calories=product.calories,
        protein=product.protein,
        fat=product.fat,
        carbs=product.carbs,
        verdict=verdict.verdict,
        verdict_text=verdict.explanation,
        verdict_is_mock=verdict.is_mock,
    )

