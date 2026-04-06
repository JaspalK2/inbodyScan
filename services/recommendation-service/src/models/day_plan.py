from __future__ import annotations
import uuid
from datetime import date, datetime
from sqlalchemy import String, Float, Text, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from shared.python.db_utils.session import Base


class DayPlan(Base):
    """A user's eating plan for a given day."""
    __tablename__ = "day_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    plan_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class DayPlanEntry(Base):
    """One slot in a DayPlan — references a saved CustomMeal or stores inline items as JSON."""
    __tablename__ = "day_plan_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    day_plan_id: Mapped[str] = mapped_column(String(36), ForeignKey("day_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    meal_slot: Mapped[str] = mapped_column(String(50), nullable=False)  # breakfast | lunch | dinner | snack | other
    custom_meal_id: Mapped[str | None] = mapped_column(String(36))       # optional reference to saved meal
    custom_meal_name: Mapped[str | None] = mapped_column(String(200))    # denormalised for display
    # Aggregate macros (computed from items; stored for quick display)
    calories_kcal: Mapped[float | None] = mapped_column(Float)
    protein_g: Mapped[float | None] = mapped_column(Float)
    carbs_g: Mapped[float | None] = mapped_column(Float)
    fat_g: Mapped[float | None] = mapped_column(Float)
    fiber_g: Mapped[float | None] = mapped_column(Float)
    # JSON snapshot of items at the time of adding (so editing the saved meal later doesn't break history)
    items_snapshot: Mapped[str | None] = mapped_column(Text)  # JSON list of {food_name, quantity_g, ...}
