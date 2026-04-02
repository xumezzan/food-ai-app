from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductSchema

router = APIRouter()


@router.get("/product/search", response_model=List[ProductSchema])
async def search_products(q: str, db: AsyncSession = Depends(get_db)):
    """
    GET /product/search?q=chick → список продуктов для автодополнения.
    Возвращает до 10 совпадений.
    """
    if len(q) < 2:
        return []
    result = await db.execute(
        select(Product).where(Product.name.ilike(f"%{q}%")).limit(10)
    )
    return result.scalars().all()


@router.get("/product", response_model=ProductSchema)
async def get_product(name: str, db: AsyncSession = Depends(get_db)):
    """GET /product?name=banana — поиск по имени."""
    result = await db.execute(select(Product).where(Product.name.ilike(name)))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail=f"Продукт '{name}' не найден")
    return product


@router.post("/product", response_model=ProductSchema, status_code=201)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db)):
    """POST /product — добавить продукт вручную."""
    product = Product(**data.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product
