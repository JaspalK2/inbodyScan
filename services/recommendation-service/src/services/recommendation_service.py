from __future__ import annotations
import json
import logging
import uuid
from dataclasses import asdict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.diet_recommendation import DietRecommendation
from ..models.workout_recommendation import WorkoutRecommendation
from .macro_calculator import calculate_macros
from .diet_engine import generate_diet_plan
from .workout_engine import generate_workout_plan
from .workout_scorer import score_workout_split

logger = logging.getLogger(__name__)


def _validate_diet_macros(plan: dict, macro_targets) -> bool:
    """Return True if every day's totals are within ±10% of macro targets."""
    targets = {
        "calories": macro_targets.calories,
        "protein_g": macro_targets.protein_g,
        "carbs_g": macro_targets.carbs_g,
        "fat_g": macro_targets.fat_g,
    }
    for day in plan.get("days", []):
        totals = day.get("day_totals", {})
        for key, target in targets.items():
            if not target:
                continue
            actual = totals.get(key, 0)
            if abs(actual - target) / target > 0.10:
                return False
    return True


async def generate_diet_recommendation(
    session: AsyncSession,
    user_id: str,
    scan_id: str,
    metrics: dict,
    goal_type: str,
    restrictions: list[str],
    age: int | None = None,
    height_cm: float | None = None,
    gender: str | None = None,
    activity_level: str = "moderate",
) -> DietRecommendation:
    macro_targets = calculate_macros(
        body_weight_kg=metrics.get("weight") or metrics.get("body_weight_kg"),
        fat_free_mass_kg=metrics.get("fat_free_mass") or metrics.get("fat_free_mass_kg"),
        body_fat_percentage=metrics.get("body_fat_percentage") or metrics.get("pbf"),
        age=age,
        height_cm=height_cm,
        gender=gender,
        goal_type=goal_type,
        activity_level=activity_level,
    )

    structured = generate_diet_plan(macro_targets, restrictions, goal_type)
    structured["macro_targets"] = asdict(macro_targets)
    raw_response = json.dumps(structured)
    structured_json = raw_response

    rec = DietRecommendation(
        id=str(uuid.uuid4()),
        user_id=user_id,
        scan_id=scan_id,
        goal_type=goal_type,
        llm_response=raw_response,
        structured_plan=structured_json,
    )
    session.add(rec)
    await session.commit()
    await session.refresh(rec)
    return rec


def _score_generated_plan(structured: dict) -> int:
    """Compute overall score for a generated plan (single-week {days:[...]} format)."""
    days = structured.get("days") or []
    # Convert AI plan format to scorer format
    scorer_days = [
        {
            "day_label": str(d.get("day", i + 1)),
            "focus": d.get("focus"),
            "is_rest": d.get("is_rest", False),
            "exercises": [
                {"exercise_name": ex.get("name", ""), "sets": ex.get("sets")}
                for ex in (d.get("exercises") or [])
            ],
        }
        for i, d in enumerate(days)
    ]
    return score_workout_split(scorer_days).overall


async def generate_workout_recommendation(
    session: AsyncSession,
    user_id: str,
    scan_id: str,
    metrics: dict,
    goal_type: str,
) -> WorkoutRecommendation:
    structured = generate_workout_plan(metrics, goal_type)
    raw_response = json.dumps(structured)
    structured_json = raw_response

    rec = WorkoutRecommendation(
        id=str(uuid.uuid4()),
        user_id=user_id,
        scan_id=scan_id,
        goal_type=goal_type,
        llm_response=raw_response,
        structured_plan=structured_json,
    )
    session.add(rec)
    await session.commit()
    await session.refresh(rec)
    return rec


async def get_diet_recommendations(session: AsyncSession, user_id: str) -> list[DietRecommendation]:
    result = await session.execute(
        select(DietRecommendation).where(DietRecommendation.user_id == user_id).order_by(DietRecommendation.created_at.desc())
    )
    return list(result.scalars().all())


async def get_workout_recommendations(session: AsyncSession, user_id: str) -> list[WorkoutRecommendation]:
    result = await session.execute(
        select(WorkoutRecommendation).where(WorkoutRecommendation.user_id == user_id).order_by(WorkoutRecommendation.created_at.desc())
    )
    return list(result.scalars().all())
