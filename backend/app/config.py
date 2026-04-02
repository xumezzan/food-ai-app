from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str
    GEMINI_API_KEY: Optional[str] = None
    REDIS_URL: str = "redis://localhost:6379/0"
    # Путь к JSON-ключу Firebase Service Account
    # Скачивается из: Firebase Console → Project Settings → Service Accounts
    FIREBASE_SERVICE_ACCOUNT_PATH: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()
