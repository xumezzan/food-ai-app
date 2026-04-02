from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


# Для async нужен драйвер asyncpg — меняем postgresql:// → postgresql+asyncpg://
ASYNC_DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://"
)

# Async engine (НЕ блокирует event loop)
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,          # True — SQL печатается в консоль (только для дебага)
    pool_size=10,        # 10 постоянных соединений в пуле
    max_overflow=20,     # + 20 временных при пиковой нагрузке
)

# Фабрика async-сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,   # объекты не сбрасываются после commit
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    pass


# Dependency для роутеров (async)
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
