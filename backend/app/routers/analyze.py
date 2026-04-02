from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.product import Product
from app.models.user import UserProfile
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse
from app.services.ai_advisor import get_ai_verdict

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(data: AnalyzeRequest, db: AsyncSession = Depends(get_db)):
    """
    Анализирует продукт с учётом цели пользователя.
    Использует Gemini AI (единый советник для всего приложения).
    """
    # Async поиск пользователя
    user_result = await db.execute(select(UserProfile).where(UserProfile.id == data.user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    # Async поиск продукта по имени (ilike)
    product_result = await db.execute(
        select(Product).where(Product.name.ilike(data.name))
    )
    product = product_result.scalar_one_or_none()

    if not product:
        return AnalyzeResponse(
            name=data.name,
            calories=0, protein=0, fat=0, carbs=0,
            verdict="yellow",
            verdict_text=f"Продукт '{data.name}' не найден в базе. Оценка недоступна.",
            verdict_is_mock=True
        )

    # Async вердикт от AI
    verdict = await get_ai_verdict(user, product)

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
