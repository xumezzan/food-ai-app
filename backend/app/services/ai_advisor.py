"""
AI-советник: формирует промпт и получает вердикт от LLM.

Используется: Google Gemini (gemini-1.5-flash — быстрый и дешёвый).
Замена на OpenAI: достаточно поменять функцию `_call_llm()`.
"""

import json
import re
import logging
from dataclasses import dataclass
from typing import Literal

import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)

# Тип светофора
Verdict = Literal["green", "yellow", "red"]


# ─────────────────────────────────────────────
# Результат
# ─────────────────────────────────────────────

@dataclass(frozen=True)
class AiVerdict:
    verdict: Verdict        # "green" | "yellow" | "red"
    explanation: str        # одно предложение от AI
    is_mock: bool = False   # True если API недоступен и вернули заглушку


# ─────────────────────────────────────────────
# Формирование промпта
# ─────────────────────────────────────────────

def _build_prompt(user_profile, product, norms) -> str:
    """
    Строит промпт для диетолога-LLM.
    Принимает объекты UserProfile, Product и DailyNorms.
    """
    goal_labels = {
        "loss":     "похудение",
        "gain":     "набор мышечной массы",
        "maintain": "поддержание веса",
    }
    goal = str(user_profile.goal).split(".")[-1]
    goal_label = goal_labels.get(goal, goal)

    composition = product.composition or "не указан"

    return f"""
Действуй как строгий диетолог. Дай короткий вердикт о продукте для пользователя.

ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ:
- Цель: {goal_label}
- Суточная норма: {norms.calories:.0f} ккал
- Нормы БЖУ: белки {norms.protein_g:.0f}г | жиры {norms.fat_g:.0f}г | углеводы {norms.carbs_g:.0f}г

ПРОДУКТ (на 100г):
- Название: {product.name}
- Калории: {product.calories} ккал
- Белки: {product.protein}г
- Жиры: {product.fat}г
- Углеводы: {product.carbs}г
- Состав: {composition}

ЗАДАЧА: Верни ответ строго в JSON-формате, без markdown, без пояснений вне JSON:
{{
  "verdict": "green" | "yellow" | "red",
  "explanation": "Одно предложение — почему продукт подходит или не подходит под цель."
}}

Критерии:
- green  = идеально соответствует цели пользователя
- yellow = можно употреблять с осторожностью или в небольшом количестве
- red    = вредно или сильно противоречит цели
""".strip()


# ─────────────────────────────────────────────
# Вызов LLM
# ─────────────────────────────────────────────

def _call_llm(prompt: str) -> str:
    """
    Отправляет промпт в Gemini и возвращает сырой текст ответа.

    Чтобы переключиться на OpenAI — замени эту функцию:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content
    """
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text


def _parse_response(raw: str) -> AiVerdict:
    """Извлекает JSON из ответа LLM (защита от лишнего текста вокруг)."""
    # Ищем JSON-блок даже если LLM добавил текст вокруг
    match = re.search(r'\{.*?\}', raw, re.DOTALL)
    if not match:
        raise ValueError(f"Не удалось найти JSON в ответе LLM: {raw!r}")

    data = json.loads(match.group())
    verdict = data.get("verdict", "yellow")
    explanation = data.get("explanation", "Нет объяснения.")

    if verdict not in ("green", "yellow", "red"):
        verdict = "yellow"

    return AiVerdict(verdict=verdict, explanation=explanation)


# ─────────────────────────────────────────────
# Публичный API сервиса
# ─────────────────────────────────────────────

def get_ai_verdict(user_profile, product) -> AiVerdict:
    """
    Основная функция. Вызывается из роутера.

    Если GEMINI_API_KEY не задан или произошла ошибка —
    возвращает заглушку (is_mock=True) без падения сервера.
    """
    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY не задан — возвращаем mock-вердикт")
        return AiVerdict(
            verdict="yellow",
            explanation="AI-анализ недоступен. Добавьте GEMINI_API_KEY в .env.",
            is_mock=True,
        )

    try:
        norms = user_profile.get_daily_norms()
        prompt = _build_prompt(user_profile, product, norms)
        raw = _call_llm(prompt)
        return _parse_response(raw)

    except Exception as e:
        logger.error(f"Ошибка AI-вердикта: {e}")
        return AiVerdict(
            verdict="yellow",
            explanation="Не удалось получить AI-анализ. Попробуйте позже.",
            is_mock=True,
        )
