import uuid
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.scan import InBodyScan
from ..models.metric import ScanMetric


async def create_scan(session: AsyncSession, user_id: str, scan_date: date, storage_path: str) -> InBodyScan:
    scan = InBodyScan(
        id=str(uuid.uuid4()),
        user_id=user_id,
        scan_date=scan_date,
        storage_path=storage_path,
    )
    session.add(scan)
    await session.commit()
    await session.refresh(scan)
    return scan


async def save_metrics(session: AsyncSession, scan_id: str, metrics: dict) -> list[ScanMetric]:
    records = [
        ScanMetric(id=str(uuid.uuid4()), scan_id=scan_id, metric_key=k, metric_value=v)
        for k, v in metrics.items()
    ]
    session.add_all(records)
    await session.commit()
    return records


async def get_scan_by_id(session: AsyncSession, scan_id: str, user_id: str) -> InBodyScan | None:
    result = await session.execute(
        select(InBodyScan).where(InBodyScan.id == scan_id, InBodyScan.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_scans_for_user(session: AsyncSession, user_id: str) -> list[InBodyScan]:
    result = await session.execute(
        select(InBodyScan).where(InBodyScan.user_id == user_id).order_by(InBodyScan.scan_date.desc())
    )
    return list(result.scalars().all())


async def get_metrics_for_scan(session: AsyncSession, scan_id: str) -> list[ScanMetric]:
    result = await session.execute(
        select(ScanMetric).where(ScanMetric.scan_id == scan_id)
    )
    return list(result.scalars().all())


async def scan_date_exists(session: AsyncSession, user_id: str, scan_date: date) -> bool:
    result = await session.execute(
        select(InBodyScan).where(InBodyScan.user_id == user_id, InBodyScan.scan_date == scan_date)
    )
    return result.scalar_one_or_none() is not None
