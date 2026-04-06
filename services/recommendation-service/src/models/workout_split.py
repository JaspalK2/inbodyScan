from __future__ import annotations
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from shared.python.db_utils.session import Base


class WorkoutSplit(Base):
    """A user's named weekly workout split definition (e.g. 'PPL Split')."""
    __tablename__ = "workout_splits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WorkoutSplitDay(Base):
    """One training day within a WorkoutSplit."""
    __tablename__ = "workout_split_days"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    split_id: Mapped[str] = mapped_column(String(36), ForeignKey("workout_splits.id", ondelete="CASCADE"), nullable=False, index=True)
    day_label: Mapped[str] = mapped_column(String(50), nullable=False)   # e.g. "Monday" or "Day 1"
    focus: Mapped[str | None] = mapped_column(String(200))               # e.g. "Push", "Back + Biceps"
    is_rest: Mapped[bool] = mapped_column(default=False)


class WorkoutExercise(Base):
    """An exercise entry within a WorkoutSplitDay, including user-logged sets/reps/weight."""
    __tablename__ = "workout_exercises"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    day_id: Mapped[str] = mapped_column(String(36), ForeignKey("workout_split_days.id", ondelete="CASCADE"), nullable=False, index=True)
    exercise_name: Mapped[str] = mapped_column(String(200), nullable=False)
    sets: Mapped[int | None] = mapped_column(Integer)
    reps: Mapped[str | None] = mapped_column(String(50))       # e.g. "8-12" or "10"
    weight_kg: Mapped[float | None] = mapped_column(Float)
    rest_seconds: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
