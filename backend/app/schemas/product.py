from typing import Optional
from pydantic import BaseModel


class ProductSchema(BaseModel):
    id: int
    barcode: str | None
    name: str
    calories: float
    protein: float
    fat: float
    carbs: float
    composition: str | None
    is_verified: bool

    model_config = {"from_attributes": True}


class ProductWithVerdict(ProductSchema):
    """ProductSchema + опциональный AI-вердикт (используется в /barcode и /correct-product)."""
    verdict: Optional[str] = None
    verdict_text: Optional[str] = None
    verdict_is_mock: bool = False


class ProductCreate(BaseModel):
    name: str
    barcode: str | None = None
    calories: float
    protein: float
    fat: float
    carbs: float
    composition: str | None = None
