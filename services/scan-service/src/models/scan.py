import uuid
from datetime import date, datetime
from sqlalchemy import String, Date, DateTime, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from shared.python.db_utils.session import Base


class InBodyScan(Base):
    __tablename__ = "inbody_scans"
    __table_args__ = (
        UniqueConstraint("user_id", "scan_date", name="uq_user_scan_date"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    scan_date: Mapped[date] = mapped_column(Date, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
