from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductSchema

router = APIRouter()


@router.get("/product/search", response_model=List[ProductSchema])
def search_products(q: str, db: Session = Depends(get_db)):
    """
    GET /product/search?q=chick → список продуктов для автодополнения.
    Возвращает до 10 совпадений.
    """
    if len(q) < 2:
        return []
    return (
        db.query(Product)
        .filter(Product.name.ilike(f"%{q}%"))
        .limit(10)
        .all()
    )


@router.get("/product", response_model=ProductSchema)
def get_product(name: str, db: Session = Depends(get_db)):
    """GET /product?name=banana — поиск по имени."""
    product = db.query(Product).filter(Product.name.ilike(name)).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Продукт '{name}' не найден")
    return product


@router.post("/product", response_model=ProductSchema, status_code=201)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    """POST /product — добавить продукт вручную."""
    existing = db.query(Product).filter(Product.name.ilike(data.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Продукт '{data.name}' уже существует")
    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

