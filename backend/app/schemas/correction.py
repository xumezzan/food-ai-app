from pydantic import BaseModel


class CorrectionCreate(BaseModel):
    predicted_name: str
    corrected_name: str


class CorrectionResponse(CorrectionCreate):
    id: int

    model_config = {"from_attributes": True}
