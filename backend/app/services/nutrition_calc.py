"""
Сервис расчёта суточной нормы калорий и БЖУ.

Формула: Миффлин-Сан Жеор (1990) — самая точная для большинства людей.
Архитектура модульная: достаточно заменить `_calculate_bmr()` для перехода
на другую формулу (Harris-Benedict, Кетч-МакАрдл и т.д.)
"""

from dataclasses import dataclass
from typing import Protocol


# ─────────────────────────────────────────────
# Результат расчёта
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class DailyNorms:
    """Суточные нормы пользователя."""
    calories: float       # ккал
    protein_g: float      # белки, г
    fat_g: float          # жиры, г
    carbs_g: float        # углеводы, г

    def __str__(self) -> str:
        return (
            f"Калории: {self.calories:.0f} ккал | "
            f"Б: {self.protein_g:.0f}г  "
            f"Ж: {self.fat_g:.0f}г  "
            f"У: {self.carbs_g:.0f}г"
        )


# ─────────────────────────────────────────────
# Протокол профиля (для независимости от ORM)
# ─────────────────────────────────────────────

class UserProfileProtocol(Protocol):
    """Интерфейс, которому должен соответствовать UserProfile."""
    weight: float
    height: float
    age: int
    gender: str       # "male" | "female"
    activity_level: str
    goal: str         # "loss" | "gain" | "maintain"


# ─────────────────────────────────────────────
# Коэффициенты активности
# ─────────────────────────────────────────────

_ACTIVITY_MULTIPLIERS: dict[str, float] = {
    "sedentary":   1.2,    # сидячий образ жизни
    "light":       1.375,  # 1-3 тренировки в неделю
    "moderate":    1.55,   # 3-5 тренировок в неделю
    "active":      1.725,  # 6-7 тренировок в неделю
    "very_active": 1.9,    # физический труд + тренировки
}

# Корректировка калорий под цель (ккал)
_GOAL_ADJUSTMENT: dict[str, float] = {
    "loss":     -500,  # дефицит
    "gain":     +500,  # профицит
    "maintain":    0,  # норма
}

# Распределение макронутриентов по целям (доля от калорий)
_MACRO_RATIOS: dict[str, dict[str, float]] = {
    "loss": {
        "protein": 0.35,  # высокий белок → сохраняем мышцы
        "fat":     0.25,
        "carbs":   0.40,
    },
    "gain": {
        "protein": 0.25,
        "fat":     0.25,
        "carbs":   0.50,  # больше углеводов → энергия для роста
    },
    "maintain": {
        "protein": 0.25,
        "fat":     0.30,
        "carbs":   0.45,
    },
}

# Калорий на грамм нутриента
_KCAL_PER_GRAM: dict[str, float] = {
    "protein": 4.0,
    "fat":     9.0,
    "carbs":   4.0,
}


# ─────────────────────────────────────────────
# Базовый обмен веществ (BMR)
# ─────────────────────────────────────────────

def _calculate_bmr(
    weight: float,
    height: float,
    age: int,
    gender: str,
) -> float:
    """
    Формула Миффлина-Сан Жеора (Mifflin-St Jeor, 1990).
    Мужчины:  BMR = 10·вес + 6.25·рост − 5·возраст + 5
    Женщины:  BMR = 10·вес + 6.25·рост − 5·возраст − 161
    """
    bmr = 10 * weight + 6.25 * height - 5 * age
    return bmr + 5 if gender == "male" else bmr - 161


# ─────────────────────────────────────────────
# Публичный API сервиса
# ─────────────────────────────────────────────

def calculate_daily_norms(user: UserProfileProtocol) -> DailyNorms:
    """
    Основная функция. Рассчитывает суточные нормы по профилю пользователя.

    Шаги:
    1. BMR по формуле Миффлина-Сан Жеора
    2. TDEE = BMR × коэффициент активности
    3. Целевые калории = TDEE + корректировка по цели
    4. БЖУ: распределяем калории по целевым пропорциям
    """
    # 1. Базовый обмен веществ
    bmr = _calculate_bmr(user.weight, user.height, user.age, user.gender)

    # 2. Суточные затраты с учётом активности (TDEE)
    activity_key = str(user.activity_level).split(".")[-1]  # "ActivityLevel.moderate" → "moderate"
    multiplier = _ACTIVITY_MULTIPLIERS.get(activity_key, 1.55)
    tdee = bmr * multiplier

    # 3. Корректировка под цель
    goal_key = str(user.goal).split(".")[-1]  # "Goal.loss" → "loss"
    target_calories = tdee + _GOAL_ADJUSTMENT.get(goal_key, 0)
    target_calories = max(target_calories, 1200)  # нижняя граница — безопасный минимум

    # 4. Распределение БЖУ
    ratios = _MACRO_RATIOS.get(goal_key, _MACRO_RATIOS["maintain"])
    protein_g = (target_calories * ratios["protein"]) / _KCAL_PER_GRAM["protein"]
    fat_g     = (target_calories * ratios["fat"])     / _KCAL_PER_GRAM["fat"]
    carbs_g   = (target_calories * ratios["carbs"])   / _KCAL_PER_GRAM["carbs"]

    return DailyNorms(
        calories=round(target_calories, 1),
        protein_g=round(protein_g, 1),
        fat_g=round(fat_g, 1),
        carbs_g=round(carbs_g, 1),
    )
