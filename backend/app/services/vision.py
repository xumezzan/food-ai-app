"""
Сервис распознавания еды на фото через Gemini Vision.
Заменяет заглушку "chicken breast" в /scan.
"""

import base64
import logging
import re
from dataclasses import dataclass

import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class VisionResult:
    detected_name: str
    is_mock: bool = False

_PROMPT = """
You are a food recognition assistant.

Look at this image and identify the main food item or dish.

Rules:
- Return ONLY the English name of the food (e.g.: "banana", "chicken breast", "caesar salad")
- If it is a packaged product — return the product category name, not the brand
- If multiple foods are visible — return the most prominent one
- No explanations, no punctuation, just the name
- If you cannot identify any food — return exactly: unknown food
""".strip()


def recognize_food_from_bytes(image_bytes: bytes, mime_type: str = "image/jpeg") -> VisionResult:
    """
    Отправляет изображение в Gemini Vision.
    Возвращает VisionResult с названием еды и флагом is_mock.
    """
    if not settings.GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY не задан — возвращаем заглушку")
        return VisionResult(detected_name="unknown food", is_mock=True)

    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-1.5-flash")

        image_part = {
            "mime_type": mime_type,
            "data": base64.b64encode(image_bytes).decode("utf-8"),
        }

        response = model.generate_content([_PROMPT, image_part])
        raw = response.text.strip().lower()

        name = raw.splitlines()[0]
        name = re.sub(r"[^a-z0-9 \-']", "", name).strip()

        return VisionResult(detected_name=name if name else "unknown food")

    except Exception as e:
        logger.error(f"Ошибка Gemini Vision: {e}")
        return VisionResult(detected_name="unknown food", is_mock=True)

