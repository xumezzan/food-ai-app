#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# deploy.sh — Деплой Food AI API на VPS
#
# Использование:
#   chmod +x deploy.sh
#   ./deploy.sh              # старт с 3 репликами API
#   ./deploy.sh 5            # старт с 5 репликами API (пиковая нагрузка)
#   ./deploy.sh 1            # старт с 1 репликой (тест)
#
# Требования на сервере:
#   - Docker + Docker Compose
#   - Файл .env с GEMINI_API_KEY и DATABASE_URL
# ─────────────────────────────────────────────────────────────────────────────

set -e   # Прерываем скрипт при любой ошибке

REPLICAS=${1:-3}   # По умолчанию 3 реплики

echo "🚀 Starting Food AI API with $REPLICAS API replicas..."

# 1. Останавливаем старые контейнеры
echo "⏹  Stopping old containers..."
docker-compose down --remove-orphans 2>/dev/null || true

# 2. Пересобираем образ если изменился код
echo "🔨 Building API image..."
docker-compose build api

# 3. Запускаем инфраструктуру (Postgres, PgBouncer, Redis) 
echo "🗄  Starting infrastructure..."
docker-compose up -d db redis pgbouncer

# 4. Ждём пока Postgres будет готов
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5
until docker-compose exec -T db pg_isready -U whomaun -d food_ai_db; do
    echo "  PostgreSQL is not ready yet, waiting..."
    sleep 2
done

# 5. Запускаем API реплики + Nginx
echo "🌐 Starting $REPLICAS API workers + Nginx..."
docker-compose up -d --scale api=$REPLICAS nginx

# 6. Проверяем что всё работает
echo "🏥 Health check..."
sleep 3
if curl -sf http://localhost/nginx-health > /dev/null; then
    echo "✅ Nginx: OK"
else
    echo "❌ Nginx: FAILED"
    docker-compose logs nginx
    exit 1
fi

if curl -sf http://localhost/ > /dev/null; then
    echo "✅ API: OK"
else
    echo "❌ API: FAILED"
    docker-compose logs api
    exit 1
fi

echo ""
echo "════════════════════════════════════════"
echo "✅ Deployment complete!"
echo "   API replicas: $REPLICAS"
echo "   URL: http://localhost"
echo "   Docs: http://localhost/docs"
echo "════════════════════════════════════════"

# 7. Показываем запущенные контейнеры
docker-compose ps
