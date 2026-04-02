from sqlalchemy import Column, Integer, Float, String, Enum, Boolean
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ActivityLevel(str, enum.Enum):
    sedentary = "sedentary"
    light = "light"
    moderate = "moderate"
    active = "active"
    very_active = "very_active"


class Goal(str, enum.Enum):
    loss = "loss"
    gain = "gain"
    maintain = "maintain"


class Gender(str, enum.Enum):
    male = "male"
    female = "female"


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: int = Column(Integer, primary_key=True, index=True)

    # ── Firebase Auth (Google / Apple Sign-In) ─────────────────────────────
    firebase_uid: str = Column(String(128), unique=True, nullable=True, index=True)
    email: str = Column(String(256), nullable=True)
    is_premium: bool = Column(Boolean, default=False, nullable=False)

    # ── Физические параметры ───────────────────────────────────────────────
    height: float = Column(Float, nullable=False)
    weight: float = Column(Float, nullable=False)
    age: int = Column(Integer, nullable=False)
    gender: str = Column(Enum(Gender), nullable=False)
    activity_level: str = Column(Enum(ActivityLevel), nullable=False, default=ActivityLevel.moderate)
    goal: str = Column(Enum(Goal), nullable=False, default=Goal.maintain)

    corrections = relationship("CorrectionReport", back_populates="user")

    def get_daily_norms(self):
        """
        Рассчитывает суточную норму калорий и БЖУ для данного пользователя.
        Делегирует вычисления в services/nutrition_calc.py.

        Пример:
            norms = user.get_daily_norms()
            print(norms.calories)   # 1850.0
            print(norms.protein_g)  # 144.0
        """
        from app.services.nutrition_calc import calculate_daily_norms
        return calculate_daily_norms(self)

    def __repr__(self) -> str:
        return f"<UserProfile id={self.id} goal={self.goal} weight={self.weight}kg>"

