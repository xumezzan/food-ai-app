from sqlalchemy import Column, Integer, Float, String, Boolean, Text, Index
from sqlalchemy.orm import relationship

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: int = Column(Integer, primary_key=True, index=True)
    barcode: str | None = Column(String(64), unique=True, nullable=True)   # штрихкод (опционально)
    name: str = Column(String(256), nullable=False, index=True)
    calories: float = Column(Float, nullable=False)         # ккал на 100г
    protein: float = Column(Float, nullable=False)          # белки, г
    fat: float = Column(Float, nullable=False)               # жиры, г
    carbs: float = Column(Float, nullable=False)             # углеводы, г
    composition: str | None = Column(Text, nullable=True)   # текстовый состав (с упаковки)
    is_verified: bool = Column(Boolean, default=False, nullable=False)  # прошёл модерацию

    corrections = relationship("CorrectionReport", back_populates="product")

    # Явный индекс на barcode — быстрый поиск по сканеру
    __table_args__ = (
        Index("ix_products_barcode", "barcode"),
    )

    def __repr__(self) -> str:
        verified = "✓" if self.is_verified else "?"
        return f"<Product [{verified}] '{self.name}' {self.calories} ккал>"
