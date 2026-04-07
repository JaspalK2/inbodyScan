from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, Float, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from shared.python.db_utils.session import Base


class CustomMeal(Base):
    """A user-saved named meal (e.g. 'My Post-Workout Shake')."""
    __tablename__ = "custom_meals"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CustomMealItem(Base):
    """A single food item inside a CustomMeal."""
    __tablename__ = "custom_meal_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    meal_id: Mapped[str] = mapped_column(String(36), ForeignKey("custom_meals.id", ondelete="CASCADE"), nullable=False, index=True)
    fdc_id: Mapped[int | None] = mapped_column()          # nullable for manual entries
    food_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity_g: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    entered_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    entered_unit: Mapped[str | None] = mapped_column(String(10), nullable=True)
    calories_kcal: Mapped[float | None] = mapped_column(Float)
    protein_g: Mapped[float | None] = mapped_column(Float)
    carbs_g: Mapped[float | None] = mapped_column(Float)
    fat_g: Mapped[float | None] = mapped_column(Float)
    fiber_g: Mapped[float | None] = mapped_column(Float)
    sodium_mg: Mapped[float | None] = mapped_column(Float)
