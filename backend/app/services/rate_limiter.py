"""
Rate Limiter — ограничение сканирований на пользователя

Бизнес-правила:
  - Бесплатный аккаунт: 50 сканирований в день
  - Премиум аккаунт: без ограничений

Реализация через Redis:
  - Ключ: "scan_limit:{user_id}:{YYYY-MM-DD}"
  - Значение: счётчик (инкрементируется на каждом скане)
  - TTL: до конца дня (сбрасывается в полночь)

Почему Redis, а не PostgreSQL:
  - INCR в Redis — атомарная операция (нет race condition при 1000 запросов/сек)
  - Запись в БД на каждом скане = узкое место при высокой нагрузке
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import HTTPException, status

from app.services.cache import get_redis

logger = logging.getLogger(__name__)

# Лимиты
FREE_DAILY_LIMIT = 50
PREMIUM_DAILY_LIMIT = 999_999


def _today_key(user_id: int) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"scan_limit:{user_id}:{today}"


def _ip_today_key(ip: str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"scan_limit:ip:{ip}:{today}"


def _seconds_until_midnight() -> int:
    """
    Вычисляет секунды до полуночи UTC.
    Именно столько будет жить счётчик Redis — он сбросится сам.
    """
    now = datetime.now(timezone.utc)
    tomorrow = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return int((tomorrow - now).total_seconds())


async def check_and_increment_scan_limit(
    user_id: int,
    is_premium: bool = False,
) -> dict:
    """
    Проверяет лимит сканирований и увеличивает счётчик.

    Returns:
        {"count": 12, "limit": 50, "remaining": 38}

    Raises:
        HTTP 429 — лимит исчерпан (только для бесплатных аккаунтов)
    """
    redis = await get_redis()

    # Если Redis недоступен — пропускаем ограничение (graceful degradation)
    if redis is None:
        logger.warning("Redis недоступен — rate limiting отключен")
        return {"count": 0, "limit": FREE_DAILY_LIMIT, "remaining": FREE_DAILY_LIMIT}

    limit = PREMIUM_DAILY_LIMIT if is_premium else FREE_DAILY_LIMIT
    key = _today_key(user_id)

    try:
        # INCR — атомарно увеличивает счётчик (thread-safe даже при 10 000 rps)
        count = await redis.incr(key)

        # Устанавливаем TTL только при первом сканировании
        if count == 1:
            ttl = _seconds_until_midnight()
            await redis.expire(key, ttl)
            logger.debug(f"Новый счётчик для user {user_id}, TTL={ttl}s")

        remaining = max(0, limit - count)

        # Проверяем лимит (только для бесплатных)
        if not is_premium and count > FREE_DAILY_LIMIT:
            logger.info(f"Rate limit exceeded for user {user_id}: {count}/{FREE_DAILY_LIMIT}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "daily_limit_exceeded",
                    "message": f"Лимит {FREE_DAILY_LIMIT} сканирований в день исчерпан. "
                               "Обновитесь до Premium для неограниченного доступа.",
                    "count": count,
                    "limit": FREE_DAILY_LIMIT,
                    "premium_required": True,
                },
                headers={"Retry-After": str(_seconds_until_midnight())},
            )

        return {"count": count, "limit": limit, "remaining": remaining}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка Rate Limiter для user {user_id}: {e}")
        # Не блокируем сканирование при ошибке Redis
        return {"count": 0, "limit": limit, "remaining": limit}


async def get_scan_usage(user_id: int, is_premium: bool = False) -> dict:
    """
    Возвращает текущий статус использования (без инкремента).
    Используется для отображения в профиле пользователя.
    """
    redis = await get_redis()
    if redis is None:
        return {"count": 0, "limit": FREE_DAILY_LIMIT, "remaining": FREE_DAILY_LIMIT}

    limit = PREMIUM_DAILY_LIMIT if is_premium else FREE_DAILY_LIMIT
    key = _today_key(user_id)

    try:
        raw = await redis.get(key)
        count = int(raw) if raw else 0
        return {
            "count": count,
            "limit": limit,
            "remaining": max(0, limit - count),
            "is_premium": is_premium,
            "resets_in_seconds": _seconds_until_midnight(),
        }
    except Exception as e:
        logger.error(f"Ошибка чтения rate limit: {e}")
        return {"count": 0, "limit": limit, "remaining": limit}


async def check_ip_scan_limit(ip: str) -> None:
    """
    Rate limit по IP-адресу — для работы без авторизации (MVP mode).
    50 сканирований в день с одного IP. Сбрасывается в полночь.
    Если Redis недоступен — пропускает без блокировки.
    """
    redis = await get_redis()
    if redis is None:
        return  # graceful degradation

    key = _ip_today_key(ip)
    try:
        count = await redis.incr(key)
        if count == 1:
            await redis.expire(key, _seconds_until_midnight())

        if count > FREE_DAILY_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "daily_limit_exceeded",
                    "message": f"Лимит {FREE_DAILY_LIMIT} сканирований в день исчерпан. Попробуйте завтра.",
                    "count": count,
                    "limit": FREE_DAILY_LIMIT,
                },
                headers={"Retry-After": str(_seconds_until_midnight())},
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка IP rate limit для {ip}: {e}")

