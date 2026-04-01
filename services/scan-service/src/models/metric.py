import uuid
from sqlalchemy import String, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from shared.python.db_utils.session import Base

STANDARD_METRIC_KEYS = [
    "body_weight_kg",
    "skeletal_muscle_mass_kg",
    "body_fat_mass_kg",
    "body_fat_percentage",
    "fat_free_mass_kg",
    "total_body_water_l",
    "intracellular_water_l",
    "extracellular_water_l",
    "ecw_tbw_ratio",
    "protein_kg",
    "minerals_kg",
    "body_mass_index",
    "basal_metabolic_rate_kcal",
    "visceral_fat_level",
    "segmental_lean_right_arm_kg",
    "segmental_lean_left_arm_kg",
    "segmental_lean_trunk_kg",
    "segmental_lean_right_leg_kg",
    "segmental_lean_left_leg_kg",
    "segmental_fat_right_arm_kg",
    "segmental_fat_left_arm_kg",
    "segmental_fat_trunk_kg",
    "segmental_fat_right_leg_kg",
    "segmental_fat_left_leg_kg",
]


class ScanMetric(Base):
    __tablename__ = "scan_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scan_id: Mapped[str] = mapped_column(String(36), ForeignKey("inbody_scans.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_key: Mapped[str] = mapped_column(String(100), nullable=False)
    metric_value: Mapped[float | None] = mapped_column(Float)
