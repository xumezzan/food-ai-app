from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ReportStatus(str, enum.Enum):
    pending = "pending"       # ожидает проверки
    approved = "approved"     # исправление принято
    rejected = "rejected"     # отклонено


class CorrectionReport(Base):
    __tablename__ = "correction_reports"

    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("user_profiles.id"), nullable=False)
    product_id: int = Column(Integer, ForeignKey("products.id"), nullable=False)
    correct_name: str = Column(String(256), nullable=False)   # правильное название от пользователя
    status: str = Column(
        Enum(ReportStatus),
        default=ReportStatus.pending,
        nullable=False,
    )

    user = relationship("UserProfile", back_populates="corrections")
    product = relationship("Product", back_populates="corrections")

    def __repr__(self) -> str:
        return (
            f"<CorrectionReport id={self.id} "
            f"product_id={self.product_id} "
            f"correct_name='{self.correct_name}' "
            f"status={self.status}>"
        )
