from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
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
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    """Создаёт профиль пользователя. Возвращает id."""
    user = UserProfile(**data.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/user/{user_id}/norms", response_model=DailyNormsResponse)
def get_user_norms(user_id: int, db: Session = Depends(get_db)):
    """
    Возвращает суточную норму калорий и БЖУ для пользователя.
    Пример: GET /user/1/norms
    """
    user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    norms = user.get_daily_norms()
    return DailyNormsResponse(
        calories=norms.calories,
        protein_g=norms.protein_g,
        fat_g=norms.fat_g,
        carbs_g=norms.carbs_g,
    )
