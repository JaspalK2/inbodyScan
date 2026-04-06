from __future__ import annotations
import json, uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.custom_meal import CustomMeal, CustomMealItem
from ..models.day_plan import DayPlan, DayPlanEntry


# ── Custom Meals ─────────────────────────────────────────────────────────────

async def create_custom_meal(session: AsyncSession, user_id: str, name: str, description: str | None, items: list[dict]) -> CustomMeal:
    meal = CustomMeal(id=str(uuid.uuid4()), user_id=user_id, name=name, description=description)
    session.add(meal)
    await session.flush()
    for item in items:
        session.add(CustomMealItem(id=str(uuid.uuid4()), meal_id=meal.id, **_item_fields(item)))
    await session.commit()
    await session.refresh(meal)
    return meal


async def get_custom_meals(session: AsyncSession, user_id: str) -> list[CustomMeal]:
    r = await session.execute(select(CustomMeal).where(CustomMeal.user_id == user_id).order_by(CustomMeal.created_at.desc()))
    return list(r.scalars().all())


async def get_custom_meal(session: AsyncSession, meal_id: str, user_id: str) -> CustomMeal | None:
    r = await session.execute(select(CustomMeal).where(CustomMeal.id == meal_id, CustomMeal.user_id == user_id))
    return r.scalar_one_or_none()


async def get_meal_items(session: AsyncSession, meal_id: str) -> list[CustomMealItem]:
    r = await session.execute(select(CustomMealItem).where(CustomMealItem.meal_id == meal_id))
    return list(r.scalars().all())


async def delete_custom_meal(session: AsyncSession, meal_id: str, user_id: str) -> bool:
    meal = await get_custom_meal(session, meal_id, user_id)
    if not meal:
        return False
    await session.delete(meal)
    await session.commit()
    return True


async def update_custom_meal(session: AsyncSession, meal_id: str, user_id: str, name: str | None, description: str | None, items: list[dict] | None) -> CustomMeal | None:
    meal = await get_custom_meal(session, meal_id, user_id)
    if not meal:
        return None
    if name is not None:
        meal.name = name
    if description is not None:
        meal.description = description
    if items is not None:
        existing = await get_meal_items(session, meal_id)
        for e in existing:
            await session.delete(e)
        for item in items:
            session.add(CustomMealItem(id=str(uuid.uuid4()), meal_id=meal_id, **_item_fields(item)))
    await session.commit()
    await session.refresh(meal)
    return meal


# ── Day Plans ────────────────────────────────────────────────────────────────

async def create_day_plan(session: AsyncSession, user_id: str, name: str, plan_date, notes: str | None, entries: list[dict]) -> DayPlan:
    plan = DayPlan(id=str(uuid.uuid4()), user_id=user_id, name=name, plan_date=plan_date, notes=notes)
    session.add(plan)
    await session.flush()
    for entry in entries:
        items_snap = entry.get("items_snapshot")
        session.add(DayPlanEntry(
            id=str(uuid.uuid4()),
            day_plan_id=plan.id,
            meal_slot=entry.get("meal_slot", "other"),
            custom_meal_id=entry.get("custom_meal_id"),
            custom_meal_name=entry.get("custom_meal_name"),
            calories_kcal=entry.get("calories_kcal"),
            protein_g=entry.get("protein_g"),
            carbs_g=entry.get("carbs_g"),
            fat_g=entry.get("fat_g"),
            fiber_g=entry.get("fiber_g"),
            items_snapshot=json.dumps(items_snap) if isinstance(items_snap, list) else items_snap,
        ))
    await session.commit()
    await session.refresh(plan)
    return plan


async def get_day_plans(session: AsyncSession, user_id: str) -> list[DayPlan]:
    r = await session.execute(select(DayPlan).where(DayPlan.user_id == user_id).order_by(DayPlan.created_at.desc()))
    return list(r.scalars().all())


async def get_day_plan(session: AsyncSession, plan_id: str, user_id: str) -> DayPlan | None:
    r = await session.execute(select(DayPlan).where(DayPlan.id == plan_id, DayPlan.user_id == user_id))
    return r.scalar_one_or_none()


async def get_day_plan_entries(session: AsyncSession, plan_id: str) -> list[DayPlanEntry]:
    r = await session.execute(select(DayPlanEntry).where(DayPlanEntry.day_plan_id == plan_id))
    return list(r.scalars().all())


async def delete_day_plan(session: AsyncSession, plan_id: str, user_id: str) -> bool:
    plan = await get_day_plan(session, plan_id, user_id)
    if not plan:
        return False
    await session.delete(plan)
    await session.commit()
    return True


# ── Helpers ──────────────────────────────────────────────────────────────────

def _item_fields(item: dict) -> dict:
    return {k: item.get(k) for k in ("fdc_id","food_name","quantity_g","calories_kcal","protein_g","carbs_g","fat_g","fiber_g","sodium_mg")}
