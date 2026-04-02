"""
Auth Service — верификация Firebase JWT-токенов

Схема работы:
  1. Flutter: Google/Apple Sign-In → Firebase выдаёт ID Token (JWT)
  2. Flutter отправляет запрос: Authorization: Bearer <firebase_token>
  3. FastAPI вызывает Firebase Admin SDK → проверяет подпись токена
  4. Получаем firebase_uid → ищем/создаём пользователя в нашей БД
  5. Возвращаем объект AuthUser для использования в роутерах

Почему Firebase, а не свой JWT:
  - Apple Sign-In и Google Sign-In управляются Firebase — это стандарт
  - Не нужно хранить пароли
  - Ротация ключей, защита от брутфорса — всё на стороне Google
"""

import logging
from typing import Optional
from dataclasses import dataclass

import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db

logger = logging.getLogger(__name__)

# HTTP Bearer схема — FastAPI автоматически вытаскивает токен из заголовка
# Authorization: Bearer <token>
bearer_scheme = HTTPBearer(auto_error=False)


# ─── Инициализация Firebase Admin SDK ────────────────────────────────────────

def _init_firebase():
    """
    Инициализирует Firebase Admin SDK один раз при старте приложения.
    Если FIREBASE_SERVICE_ACCOUNT_PATH не задан — аутентификация не работает
    (возвращаем None как признак неконфигурированного Firebase).
    """
    if not settings.FIREBASE_SERVICE_ACCOUNT_PATH:
        logger.warning("FIREBASE_SERVICE_ACCOUNT_PATH не задан — авторизация через Firebase отключена")
        return None

    if firebase_admin._apps:
        return firebase_admin.get_app()

    try:
        cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
        return firebase_admin.initialize_app(cred)
    except Exception as e:
        logger.error(f"Ошибка инициализации Firebase: {e}")
        return None


firebase_app = _init_firebase()


# ─── Результат авторизации ────────────────────────────────────────────────────

@dataclass
class AuthUser:
    """Авторизованный пользователь. Передаётся в роутеры через Depends."""
    firebase_uid: str
    email: Optional[str]
    db_user_id: Optional[int]   # ID в нашей БД (None если ещё не создавали профиль)
    is_premium: bool = False


# ─── Dependency: get_current_user ─────────────────────────────────────────────

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> AuthUser:
    """
    Dependency для защищённых эндпоинтов.

    Использование в роутере:
        @router.post("/scan")
        async def scan(user: AuthUser = Depends(get_current_user)):
            ...

    Raises:
        401 — токен отсутствует или невалиден
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходима авторизация. Передайте токен в заголовке: Authorization: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Верифицируем токен через Firebase
    try:
        if firebase_app is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Firebase не сконфигурирован на сервере. Добавьте FIREBASE_SERVICE_ACCOUNT_PATH в .env",
            )

        decoded = firebase_auth.verify_id_token(token, app=firebase_app, check_revoked=True)
        firebase_uid: str = decoded["uid"]
        email: Optional[str] = decoded.get("email")

    except firebase_auth.RevokedIdTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия отозвана. Войдите снова.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.warning(f"Невалидный Firebase токен: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный или просроченный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Ищем или создаём пользователя в нашей БД
    from app.models.user import UserProfile
    result = await db.execute(
        select(UserProfile).where(UserProfile.firebase_uid == firebase_uid)
    )
    db_user = result.scalar_one_or_none()

    return AuthUser(
        firebase_uid=firebase_uid,
        email=email,
        db_user_id=db_user.id if db_user else None,
        is_premium=db_user.is_premium if db_user else False,
    )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Optional[AuthUser]:
    """
    Опциональная авторизация — не кидает 401 если токена нет.
    Используется для эндпоинтов, которые работают и без авторизации.
    """
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None
