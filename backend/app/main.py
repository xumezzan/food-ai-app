from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import products, analyze, scan, users, barcode, correct_product, auth


app = FastAPI(
    title="Food AI API",
    version="1.0.0",
    description="AI-powered food nutrition scanner with Firebase Auth",
)

# CORS — разрешаем Flutter-приложению обращаться к API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # На проде заменить на конкретный домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Роутеры ─────────────────────────────────────────────────────────────────
app.include_router(auth.router)           # 🔑 Авторизация (/auth/me, /auth/register)
app.include_router(scan.router)           # 📷 Сканирование (защищён JWT + rate limit)
app.include_router(analyze.router)        # 🤖 AI-анализ
app.include_router(barcode.router)        # 🔍 Штрихкод
app.include_router(products.router)       # 📦 Продукты
app.include_router(users.router)          # 👤 Профиль пользователя
app.include_router(correct_product.router) # ✏️ Исправление


@app.get("/")
async def root():
    return {"status": "ok", "message": "Food AI API v1.0.0 is running"}

