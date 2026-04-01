from __future__ import annotations
from datetime import date, datetime
from pydantic import BaseModel


class ScanOut(BaseModel):
    id: str
    user_id: str
    scan_date: date
    storage_path: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MetricOut(BaseModel):
    metric_key: str
    metric_value: float | None

    model_config = {"from_attributes": True}


class ScanWithMetrics(BaseModel):
    scan: ScanOut
    metrics: list[MetricOut]
