from __future__ import annotations
from datetime import date
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.food_log import DailyFoodLogEntry


async def create_log_entries(
    session: AsyncSession,
    user_id: str,
    log_date: date,
    entries: list[dict],
) -> list[DailyFoodLogEntry]:
    records = []
    for e in entries:
        record = DailyFoodLogEntry(
            user_id=user_id,
            log_date=log_date,
            fdc_id=e.get("fdc_id"),
            food_name=e["food_name"],
            brand=e.get("brand"),
            source=e.get("source", "manual"),
            source_ref_id=e.get("source_ref_id"),
            quantity_g=e["quantity_g"],
            calories_kcal=e.get("calories_kcal"),
            protein_g=e.get("protein_g"),
            carbs_g=e.get("carbs_g"),
            fat_g=e.get("fat_g"),
            fiber_g=e.get("fiber_g"),
        )
        session.add(record)
        records.append(record)
    await session.commit()
    for r in records:
        await session.refresh(r)
    return records


async def get_entries_for_date(
    session: AsyncSession,
    user_id: str,
    log_date: date,
) -> list[DailyFoodLogEntry]:
    result = await session.execute(
        select(DailyFoodLogEntry)
        .where(
            DailyFoodLogEntry.user_id == user_id,
            DailyFoodLogEntry.log_date == log_date,
        )
        .order_by(DailyFoodLogEntry.created_at)
    )
    return list(result.scalars().all())


async def delete_entry(
    session: AsyncSession,
    entry_id: str,
    user_id: str,
) -> bool:
    result = await session.execute(
        select(DailyFoodLogEntry).where(
            DailyFoodLogEntry.id == entry_id,
            DailyFoodLogEntry.user_id == user_id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        return False
    await session.delete(entry)
    await session.commit()
    return True


async def get_logged_dates(
    session: AsyncSession,
    user_id: str,
) -> list[date]:
    result = await session.execute(
        select(DailyFoodLogEntry.log_date)
        .where(DailyFoodLogEntry.user_id == user_id)
        .distinct()
        .order_by(DailyFoodLogEntry.log_date.desc())
    )
    return [row[0] for row in result.all()]
