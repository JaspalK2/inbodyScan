from __future__ import annotations
from datetime import date
from pydantic import BaseModel


class MetricPoint(BaseModel):
    scan_date: date
    value: float | None


class MetricHistory(BaseModel):
    metric_key: str
    points: list[MetricPoint]


class DeltaCard(BaseModel):
    metric_key: str
    current_value: float | None
    previous_value: float | None
    delta: float | None
    delta_pct: float | None


class DashboardResponse(BaseModel):
    user_id: str
    latest_scan_date: date | None
    previous_scan_date: date | None
    deltas: list[DeltaCard]
    history: list[MetricHistory]
