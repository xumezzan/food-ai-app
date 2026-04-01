import logging
import requests
from typing import Optional
from sqlalchemy.orm import Session
from app.models.product import Product

logger = logging.getLogger(__name__)

OFF_BASE_URL = "https://world.openfoodfacts.org/api/v0/product"


def fetch_and_save_from_openfoodfacts(barcode: str, db: Session) -> Optional[Product]:
    """
    Ищет продукт в бесплатной базе Open Food Facts.
    Если находит — сохраняет в локальную БД и возвращает объект Product.
    """
    try:
        url = f"{OFF_BASE_URL}/{barcode}.json"
        response = requests.get(url, timeout=5.0)
        
        if response.status_code != 200:
            return None
            
        data = response.json()
        if data.get("status") != 1:  # 1 = продукт найден
            return None
            
        product_info = data.get("product", {})
        
        # Парсим нутриенты (отдаются на 100г)
        nutriments = product_info.get("nutriments", {})
        
        # Название (пробуем русское, если нет - берем любое доступное)
        name = product_info.get("product_name_ru") or product_info.get("product_name") or product_info.get("generic_name") or "Unknown Product"
        
        if name == "Unknown Product":
            logger.warning(f"Продукт ({barcode}) найден, но название отсутствует. Пропущен.")
            return None # Слишком мало данных, не засоряем базу
            
        calories = nutriments.get("energy-kcal_100g") or 0.0
        protein = nutriments.get("proteins_100g") or 0.0
        fat = nutriments.get("fat_100g") or 0.0
        carbs = nutriments.get("carbohydrates_100g") or 0.0
        
        composition = product_info.get("ingredients_text_ru") or product_info.get("ingredients_text")
        
        # Создаем новый продукт в нашей базе данных
        new_product = Product(
            barcode=barcode,
            name=name,
            calories=float(calories),
            protein=float(protein),
            fat=float(fat),
            carbs=float(carbs),
            composition=composition,
            is_verified=False  # Импортированные продукты по умолчанию не верифицированы
        )
        
        db.add(new_product)
        db.commit()
        db.refresh(new_product)
        
        logger.info(f"Продукт '{name}' ({barcode}) успешно импортирован из Open Food Facts")
        return new_product
        
    except Exception as e:
        logger.error(f"Ошибка при запросе к Open Food Facts для {barcode}: {e}")
        return None
