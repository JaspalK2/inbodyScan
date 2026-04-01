"""
Analytics aggregation service.
Reads scan and metric data from the scan-service DB (same Supabase project,
tables inbody_scans + scan_metrics) and computes dashboard deltas + history.
"""
from datetime import date
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.analytics import DashboardResponse, DeltaCard, MetricHistory, MetricPoint

# These tables live in the Supabase DB (created by scan-service)
SCANS_TABLE = "inbody_scans"
METRICS_TABLE = "scan_metrics"

KEY_METRICS = [
    "body_weight_kg",
    "body_fat_percentage",
    "skeletal_muscle_mass_kg",
    "fat_free_mass_kg",
    "body_mass_index",
    "visceral_fat_level",
    "basal_metabolic_rate_kcal",
    "total_body_water_l",
]


async def build_dashboard(session: AsyncSession, user_id: str) -> DashboardResponse:
    # Fetch all scans ordered by date desc
    scans_result = await session.execute(
        text(f"SELECT id, scan_date FROM {SCANS_TABLE} WHERE user_id = :uid ORDER BY scan_date DESC"),
        {"uid": user_id},
    )
    scans = scans_result.fetchall()

    if not scans:
        return DashboardResponse(
            user_id=user_id,
            latest_scan_date=None,
            previous_scan_date=None,
            deltas=[],
            history=[],
        )

    latest_scan_id, latest_date = scans[0]
    previous_scan_id = scans[1][0] if len(scans) > 1 else None
    previous_date = scans[1][1] if len(scans) > 1 else None

    # Fetch metrics for latest scan
    latest_metrics = await _fetch_metrics(session, latest_scan_id)
    previous_metrics = await _fetch_metrics(session, previous_scan_id) if previous_scan_id else {}

    # Build delta cards for key metrics
    deltas = []
    for key in KEY_METRICS:
        cur = latest_metrics.get(key)
        prev = previous_metrics.get(key)
        delta = (cur - prev) if cur is not None and prev is not None else None
        delta_pct = (delta / prev * 100) if delta is not None and prev else None
        deltas.append(DeltaCard(
            metric_key=key,
            current_value=cur,
            previous_value=prev,
            delta=delta,
            delta_pct=round(delta_pct, 2) if delta_pct is not None else None,
        ))

    # Build history for all key metrics across all scans
    history = await _build_history(session, user_id, scans, KEY_METRICS)

    return DashboardResponse(
        user_id=user_id,
        latest_scan_date=latest_date,
        previous_scan_date=previous_date,
        deltas=deltas,
        history=history,
    )


async def _fetch_metrics(session: AsyncSession, scan_id: str) -> dict[str, float | None]:
    result = await session.execute(
        text(f"SELECT metric_key, metric_value FROM {METRICS_TABLE} WHERE scan_id = :sid"),
        {"sid": scan_id},
    )
    return {row[0]: row[1] for row in result.fetchall()}


async def _build_history(session: AsyncSession, user_id: str, scans: list, keys: list[str]) -> list[MetricHistory]:
    scan_ids = [s[0] for s in scans]
    if not scan_ids:
        return []

    placeholders = ", ".join(f":id{i}" for i in range(len(scan_ids)))
    params = {f"id{i}": sid for i, sid in enumerate(scan_ids)}
    params["uid"] = user_id

    result = await session.execute(
        text(f"""
            SELECT m.metric_key, s.scan_date, m.metric_value
            FROM {METRICS_TABLE} m
            JOIN {SCANS_TABLE} s ON s.id = m.scan_id
            WHERE s.user_id = :uid AND m.scan_id IN ({placeholders})
            ORDER BY s.scan_date ASC
        """),
        params,
    )
    rows = result.fetchall()

    # Group by metric_key
    grouped: dict[str, list[MetricPoint]] = {k: [] for k in keys}
    for metric_key, scan_date, metric_value in rows:
        if metric_key in grouped:
            grouped[metric_key].append(MetricPoint(scan_date=scan_date, value=metric_value))

    return [MetricHistory(metric_key=k, points=v) for k, v in grouped.items()]
