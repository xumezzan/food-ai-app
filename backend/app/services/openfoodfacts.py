import logging
import httpx
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.product import Product

logger = logging.getLogger(__name__)

OFF_BASE_URL = "https://world.openfoodfacts.org/api/v0/product"


async def fetch_and_save_from_openfoodfacts(barcode: str, db: AsyncSession) -> Optional[Product]:
    """
    Асинхронно ищет продукт в бесплатной базе Open Food Facts.
    Если находит — сохраняет в локальную БД и возвращает объект Product.

    Использует httpx вместо requests — не блокирует event loop.
    """
    try:
        url = f"{OFF_BASE_URL}/{barcode}.json"

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)

        if response.status_code != 200:
            return None

        data = response.json()
        if data.get("status") != 1:  # 1 = продукт найден
            return None

        product_info = data.get("product", {})

        # Парсим нутриенты (отдаются на 100г)
        nutriments = product_info.get("nutriments", {})

        # Название (пробуем русское, если нет — берем любое доступное)
        name = (
            product_info.get("product_name_ru")
            or product_info.get("product_name")
            or product_info.get("generic_name")
            or "Unknown Product"
        )

        if name == "Unknown Product":
            logger.warning(f"Продукт ({barcode}) найден, но название отсутствует. Пропущен.")
            return None  # Не засоряем базу

        calories = nutriments.get("energy-kcal_100g") or 0.0
        protein = nutriments.get("proteins_100g") or 0.0
        fat = nutriments.get("fat_100g") or 0.0
        carbs = nutriments.get("carbohydrates_100g") or 0.0

        composition = (
            product_info.get("ingredients_text_ru")
            or product_info.get("ingredients_text")
        )

        # Создаем новый продукт в нашей базе данных
        new_product = Product(
            barcode=barcode,
            name=name,
            calories=float(calories),
            protein=float(protein),
            fat=float(fat),
            carbs=float(carbs),
            composition=composition,
            is_verified=False,  # Импортированные продукты не верифицированы
        )

        db.add(new_product)
        await db.commit()
        await db.refresh(new_product)

        logger.info(f"Продукт '{name}' ({barcode}) успешно импортирован из Open Food Facts")
        return new_product

    except Exception as e:
        logger.error(f"Ошибка при запросе к Open Food Facts для {barcode}: {e}")
        return None
