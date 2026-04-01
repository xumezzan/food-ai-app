from pydantic import BaseModel


class ScanResponse(BaseModel):
    detected_name: str
    is_mock: bool = False  # True если Gemini недоступен и вернул заглушку
