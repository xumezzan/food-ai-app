FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Предзапуск скрипта (миграции + сервер)
CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
