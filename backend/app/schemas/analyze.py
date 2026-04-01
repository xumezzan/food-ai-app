from pydantic import BaseModel
from typing import Literal


class AnalyzeRequest(BaseModel):
    name: str       # название продукта
    user_id: int    # id пользователя


class AnalyzeResponse(BaseModel):
    name: str
    calories: float
    protein: float
    fat: float
    carbs: float
    verdict: Literal["green", "yellow", "red"] | None = None
    verdict_text: str | None = None
    verdict_is_mock: bool = False

