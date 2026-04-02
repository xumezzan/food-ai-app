from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str
    GEMINI_API_KEY: Optional[str] = None  # опционально — без него AI не работает
    REDIS_URL: str = "redis://localhost:6379/0"  # по умолчанию локальный Redis

    class Config:
        env_file = ".env"


settings = Settings()
