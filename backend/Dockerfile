FROM python:3.12-slim

WORKDIR /app

# Устанавливаем зависимости сборки (нужны для asyncpg)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Зависимости — отдельным слоем (кэшируются Docker'ом если requirements не менялся)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код приложения
COPY . .

# ─── Запуск ─────────────────────────────────────────────────────────────────
# 1. alembic upgrade head  — применяем SQL-миграции (только первая реплика сделает,
#    остальные просто проверят что схема актуальна)
# 2. uvicorn --workers 2   — 2 async-воркера на 1 контейнер
#    (итого: 3 реплики × 2 воркера = 6 параллельных процессов)
CMD alembic upgrade head && \
    uvicorn app.main:app \
      --host 0.0.0.0 \
      --port 8000 \
      --workers 2 \
      --loop uvloop \
      --http h11
