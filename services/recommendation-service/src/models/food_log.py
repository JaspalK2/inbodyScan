import uuid
from datetime import date, datetime
from sqlalchemy import String, Float, Integer, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from shared.python.db_utils.session import Base


class DailyFoodLogEntry(Base):
    __tablename__ = "daily_food_log_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    log_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    fdc_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    food_name: Mapped[str] = mapped_column(String(255), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="manual")
    source_ref_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    quantity_g: Mapped[float] = mapped_column(Float, nullable=False)
    entered_quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    entered_unit: Mapped[str | None] = mapped_column(String(10), nullable=True)
    calories_kcal: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    fiber_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
