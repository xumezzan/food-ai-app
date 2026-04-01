from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str
    GEMINI_API_KEY: Optional[str] = None  # опционально — без него AI не работает

    class Config:
        env_file = ".env"


settings = Settings()
