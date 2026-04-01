from pydantic import BaseModel, Field
from typing import Literal


class UserCreate(BaseModel):
    weight: float = Field(..., gt=0, lt=500, description="Вес в кг")
    height: float = Field(..., gt=0, lt=300, description="Рост в см")
    age: int = Field(25, gt=0, lt=120, description="Возраст (по умолчанию 25)")
    gender: Literal["male", "female"] = "male"
    activity_level: Literal["sedentary", "light", "moderate", "active", "very_active"] = "moderate"
    goal: Literal["loss", "gain", "maintain"] = "maintain"


class UserResponse(UserCreate):
    id: int

    model_config = {"from_attributes": True}
