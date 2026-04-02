"""
Redis Cache Service

Простой async-клиент для кэширования AI-вердиктов.
Ключ кэша: "verdict:{product_id}:{user_goal}" — одна пара продукт+цель.
Время жизни: 24 часа (86400 секунд).

Почему это важно:
  - Без кэша: 10 000 сканирований Coca-Cola = 10 000 платных запросов к Gemini
  - С кэшем: 1 запрос к Gemini + 9 999 ответов из Redis за 0.001 сек
"""

import json
import logging
from typing import Optional

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

# Время жизни кэша в секундах (24 часа)
CACHE_TTL = 86_400  # 24 * 60 * 60


def _get_redis() -> aioredis.Redis:
    """Создает async-клиент Redis. Вызывается один раз при старте."""
    return aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,
    )


# Глобальный клиент (создается при импорте, переиспользуется)
_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> Optional[aioredis.Redis]:
    """
    Возвращает Redis-клиент.
    Если Redis недоступен — возвращает None (кэш просто не работает,
    приложение продолжает работать без него).
    """
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = _get_redis()
            await _redis_client.ping()
            logger.info("✅ Redis подключен успешно")
        except Exception as e:
            logger.warning(f"⚠️  Redis недоступен: {e}. Кэш отключен.")
            _redis_client = None
    return _redis_client


def _make_cache_key(product_id: int, user_goal: str) -> str:
    """
    Формирует ключ кэша.

    Пример: "verdict:42:loss"
    Это значит: AI-вердикт для продукта ID=42 при цели "loss" (похудение).
    Разные цели → разные ключи → разные вердикты.
    """
    return f"verdict:{product_id}:{user_goal}"


async def get_cached_verdict(product_id: int, user_goal: str) -> Optional[dict]:
    """
    Достает вердикт из кэша.
    Возвращает dict {"verdict": ..., "explanation": ..., "is_mock": ...}
    или None если кэша нет.
    """
    redis = await get_redis()
    if redis is None:
        return None

    try:
        key = _make_cache_key(product_id, user_goal)
        raw = await redis.get(key)
        if raw:
            logger.debug(f"🎯 Cache HIT: {key}")
            return json.loads(raw)
        logger.debug(f"💨 Cache MISS: {key}")
        return None
    except Exception as e:
        logger.warning(f"Ошибка чтения из Redis: {e}")
        return None


async def set_cached_verdict(
    product_id: int,
    user_goal: str,
    verdict: str,
    explanation: str,
    is_mock: bool,
) -> None:
    """
    Сохраняет вердикт в кэш на 24 часа.
    Не кэшируем заглушки (is_mock=True) — они неточные.
    """
    if is_mock:
        return  # Заглушки не кэшируем — они неточные

    redis = await get_redis()
    if redis is None:
        return

    try:
        key = _make_cache_key(product_id, user_goal)
        value = json.dumps({
            "verdict": verdict,
            "explanation": explanation,
            "is_mock": False,
        })
        await redis.setex(key, CACHE_TTL, value)
        logger.debug(f"💾 Cached: {key} (TTL={CACHE_TTL}s)")
    except Exception as e:
        logger.warning(f"Ошибка записи в Redis: {e}")
