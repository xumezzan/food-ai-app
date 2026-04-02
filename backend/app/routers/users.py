from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.database import get_db
from app.models.user import UserProfile
from app.schemas.user import UserCreate, UserResponse

router = APIRouter()


class DailyNormsResponse(BaseModel):
    calories: float
    protein_g: float
    fat_g: float
    carbs_g: float


@router.post("/user", response_model=UserResponse, status_code=201)
async def create_user(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Создаёт профиль пользователя. Возвращает id."""
    user = UserProfile(**data.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/user/{user_id}/norms", response_model=DailyNormsResponse)
async def get_user_norms(user_id: int, db: AsyncSession = Depends(get_db)):
    """
    Возвращает суточную норму калорий и БЖУ для пользователя.
    Пример: GET /user/1/norms
    """
    result = await db.execute(select(UserProfile).where(UserProfile.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    norms = user.get_daily_norms()
    return DailyNormsResponse(
        calories=norms.calories,
        protein_g=norms.protein_g,
        fat_g=norms.fat_g,
        carbs_g=norms.carbs_g,
    )
