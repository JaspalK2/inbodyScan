import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from shared.python.db_utils.session import Base


class WorkoutRecommendation(Base):
    __tablename__ = "workout_recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    scan_id: Mapped[str] = mapped_column(String(36), nullable=False)
    goal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    llm_response: Mapped[str] = mapped_column(Text, nullable=False)
    structured_plan: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
