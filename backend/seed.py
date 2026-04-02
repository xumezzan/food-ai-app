"""
Скрипт для заполнения базы тестовыми продуктами.
Запуск: python seed.py
"""
import sys
import os

sys.path.append(os.path.dirname(__file__))

from app.database import SessionLocal, engine, Base
from app.models.product import Product
from app.models.user import UserProfile

Base.metadata.create_all(bind=engine)

PRODUCTS = [
    {"name": "chicken breast",   "calories": 165, "protein": 31.0, "fat": 3.6,  "carbs": 0.0},
    {"name": "banana",           "calories": 89,  "protein": 1.1,  "fat": 0.3,  "carbs": 23.0},
    {"name": "apple",            "calories": 52,  "protein": 0.3,  "fat": 0.2,  "carbs": 14.0},
    {"name": "egg",              "calories": 155, "protein": 13.0, "fat": 11.0, "carbs": 1.1},
    {"name": "rice",             "calories": 130, "protein": 2.7,  "fat": 0.3,  "carbs": 28.0},
    {"name": "salmon",           "calories": 208, "protein": 20.0, "fat": 13.0, "carbs": 0.0},
    {"name": "broccoli",         "calories": 34,  "protein": 2.8,  "fat": 0.4,  "carbs": 7.0},
    {"name": "oatmeal",          "calories": 389, "protein": 17.0, "fat": 7.0,  "carbs": 66.0},
    {"name": "greek yogurt",     "calories": 59,  "protein": 10.0, "fat": 0.4,  "carbs": 3.6},
    {"name": "cheese",           "calories": 402, "protein": 25.0, "fat": 33.0, "carbs": 1.3},
    {"name": "pizza",            "calories": 266, "protein": 11.0, "fat": 10.0, "carbs": 33.0},
    {"name": "burger",           "calories": 295, "protein": 17.0, "fat": 14.0, "carbs": 24.0},
    {"name": "french fries",     "calories": 365, "protein": 3.4,  "fat": 17.0, "carbs": 48.0},
    {"name": "chocolate",        "calories": 546, "protein": 4.9,  "fat": 31.0, "carbs": 60.0},
    {"name": "avocado",          "calories": 160, "protein": 2.0,  "fat": 15.0, "carbs": 9.0},
]

TEST_USER = {"weight": 75.0, "height": 178.0, "age": 30, "gender": "male", "goal": "loss"}


def seed():
    db = SessionLocal()
    try:
        added = 0
        for p in PRODUCTS:
            exists = db.query(Product).filter(Product.name == p["name"]).first()
            if not exists:
                db.add(Product(**p))
                added += 1

        # Тестовый пользователь с id=1
        user = db.query(UserProfile).filter(UserProfile.id == 1).first()
        if not user:
            db.add(UserProfile(**TEST_USER))

        db.commit()
        print(f"✅ Добавлено продуктов: {added}")
        print(f"✅ Тестовый пользователь (id=1, goal=loss) — готов")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
