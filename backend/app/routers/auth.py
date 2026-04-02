from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.user import UserProfile
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import AuthUser, get_current_user
from app.services.rate_limiter import get_scan_usage

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthMeResponse(BaseModel):
    firebase_uid: str
    email: Optional[str]
    has_profile: bool
    is_premium: bool
    db_user_id: Optional[int]


class ScanUsageResponse(BaseModel):
    count: int
    limit: int
    remaining: int
    is_premium: bool
    resets_in_seconds: int


@router.get("/me", response_model=AuthMeResponse)
async def get_me(current_user: AuthUser = Depends(get_current_user)):
    """
    GET /auth/me — Возвращает данные текущего авторизованного пользователя.

    Используется Flutter-приложением после Sign-In чтобы проверить:
    - создан ли профиль (has_profile)
    - активен ли Premium
    """
    return AuthMeResponse(
        firebase_uid=current_user.firebase_uid,
        email=current_user.email,
        has_profile=current_user.db_user_id is not None,
        is_premium=current_user.is_premium,
        db_user_id=current_user.db_user_id,
    )


@router.post("/register", response_model=UserResponse, status_code=201)
async def register_or_update_profile(
    data: UserCreate,
    current_user: AuthUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    POST /auth/register — Создаёт или обновляет физический профиль.

    Вызывается один раз после Sign-In, когда пользователь вводит:
    вес, рост, цель. Привязывает профиль к firebase_uid.
    """
    # Проверяем есть ли уже профиль
    result = await db.execute(
        select(UserProfile).where(UserProfile.firebase_uid == current_user.firebase_uid)
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Обновляем существующий профиль
        for field, value in data.model_dump().items():
            setattr(existing, field, value)
        await db.commit()
        await db.refresh(existing)
        return existing

    # Создаём новый профиль
    user = UserProfile(
        **data.model_dump(),
        firebase_uid=current_user.firebase_uid,
        email=current_user.email,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/usage", response_model=ScanUsageResponse)
async def get_usage(current_user: AuthUser = Depends(get_current_user)):
    """
    GET /auth/usage — Показывает сколько сканирований осталось сегодня.
    Отображается в профиле как "12 / 50 сканирований сегодня".
    """
    if current_user.db_user_id is None:
        return ScanUsageResponse(
            count=0,
            limit=50,
            remaining=50,
            is_premium=False,
            resets_in_seconds=86400,
        )

    usage = await get_scan_usage(
        user_id=current_user.db_user_id,
        is_premium=current_user.is_premium,
    )
    return ScanUsageResponse(**usage)
