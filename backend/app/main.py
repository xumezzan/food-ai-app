from fastapi import FastAPI

from app.routers import products, analyze, scan, users, barcode, correct_product



app = FastAPI(title="Food AI API", version="0.1.0")

# Подключаем роутеры
app.include_router(products.router)
app.include_router(analyze.router)
app.include_router(scan.router)
app.include_router(users.router)
app.include_router(barcode.router)
app.include_router(correct_product.router)




@app.get("/")
def root():
    return {"status": "ok", "message": "Food AI API is running"}
