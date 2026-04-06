from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.workout_split import WorkoutSplit, WorkoutSplitDay, WorkoutExercise
from .workout_scorer import score_workout_split, WorkoutScore


async def create_split(session: AsyncSession, user_id: str, name: str, description: str | None, days: list[dict]) -> tuple[WorkoutSplit, WorkoutScore]:
    split = WorkoutSplit(id=str(uuid.uuid4()), user_id=user_id, name=name, description=description)
    session.add(split)
    await session.flush()

    day_objects = []
    for day_data in days:
        day = WorkoutSplitDay(
            id=str(uuid.uuid4()),
            split_id=split.id,
            day_label=day_data.get("day_label", "Day"),
            focus=day_data.get("focus"),
            is_rest=day_data.get("is_rest", False),
        )
        session.add(day)
        await session.flush()
        exercises = day_data.get("exercises") or []
        ex_objects = []
        for i, ex in enumerate(exercises):
            e = WorkoutExercise(
                id=str(uuid.uuid4()),
                day_id=day.id,
                exercise_name=ex.get("exercise_name", ""),
                sets=ex.get("sets"),
                reps=ex.get("reps"),
                weight_kg=ex.get("weight_kg"),
                rest_seconds=ex.get("rest_seconds"),
                notes=ex.get("notes"),
                sort_order=i,
            )
            session.add(e)
            ex_objects.append({"exercise_name": e.exercise_name, "sets": e.sets})
        day_objects.append({"day_label": day.day_label, "is_rest": day.is_rest, "exercises": ex_objects})

    await session.commit()
    await session.refresh(split)
    score = score_workout_split(day_objects)
    return split, score


async def get_splits(session: AsyncSession, user_id: str) -> list[WorkoutSplit]:
    r = await session.execute(select(WorkoutSplit).where(WorkoutSplit.user_id == user_id).order_by(WorkoutSplit.created_at.desc()))
    return list(r.scalars().all())


async def get_split(session: AsyncSession, split_id: str, user_id: str) -> WorkoutSplit | None:
    r = await session.execute(select(WorkoutSplit).where(WorkoutSplit.id == split_id, WorkoutSplit.user_id == user_id))
    return r.scalar_one_or_none()


async def get_split_days(session: AsyncSession, split_id: str) -> list[WorkoutSplitDay]:
    r = await session.execute(select(WorkoutSplitDay).where(WorkoutSplitDay.split_id == split_id))
    return list(r.scalars().all())


async def get_day_exercises(session: AsyncSession, day_id: str) -> list[WorkoutExercise]:
    r = await session.execute(select(WorkoutExercise).where(WorkoutExercise.day_id == day_id).order_by(WorkoutExercise.sort_order))
    return list(r.scalars().all())


async def get_split_with_score(session: AsyncSession, split_id: str, user_id: str) -> tuple[WorkoutSplit, list[dict], WorkoutScore] | None:
    split = await get_split(session, split_id, user_id)
    if not split:
        return None
    days = await get_split_days(session, split_id)
    day_dicts = []
    for d in days:
        exercises = await get_day_exercises(session, d.id)
        day_dicts.append({
            "day_label": d.day_label,
            "focus": d.focus,
            "is_rest": d.is_rest,
            "exercises": [{"exercise_name": e.exercise_name, "sets": e.sets, "reps": e.reps, "weight_kg": e.weight_kg, "rest_seconds": e.rest_seconds, "notes": e.notes} for e in exercises],
        })
    score = score_workout_split(day_dicts)
    return split, day_dicts, score


async def delete_split(session: AsyncSession, split_id: str, user_id: str) -> bool:
    split = await get_split(session, split_id, user_id)
    if not split:
        return False
    await session.delete(split)
    await session.commit()
    return True
