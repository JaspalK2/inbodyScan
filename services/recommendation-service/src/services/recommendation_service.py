import json
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.diet_recommendation import DietRecommendation
from ..models.workout_recommendation import WorkoutRecommendation
from ..models.nutritional_food import NutritionalFood
from ..llm.gemini_client import get_llm_client
from .prompt_builder import build_diet_prompt, build_workout_prompt


async def _get_sample_foods(session: AsyncSession, limit: int = 50) -> list[dict]:
    result = await session.execute(
        select(NutritionalFood).order_by(NutritionalFood.food_name).limit(limit)
    )
    foods = result.scalars().all()
    return [
        {
            "food_name": f.food_name,
            "calories_kcal": f.calories_kcal,
            "protein_g": f.protein_g,
            "carbs_g": f.carbs_g,
            "fat_g": f.fat_g,
        }
        for f in foods
    ]


async def generate_diet_recommendation(
    session: AsyncSession,
    user_id: str,
    scan_id: str,
    metrics: dict,
    goal_type: str,
    restrictions: list[str],
) -> DietRecommendation:
    sample_foods = await _get_sample_foods(session)
    prompt = build_diet_prompt(metrics, goal_type, restrictions, sample_foods)

    llm = get_llm_client()
    raw_response = await llm.generate(prompt)

    # Validate JSON is parseable; store raw + structured
    try:
        structured = json.loads(raw_response)
        structured_json = json.dumps(structured)
    except json.JSONDecodeError:
        structured_json = json.dumps({"raw": raw_response, "parse_error": True})

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


async def generate_workout_recommendation(
    session: AsyncSession,
    user_id: str,
    scan_id: str,
    metrics: dict,
    goal_type: str,
) -> WorkoutRecommendation:
    prompt = build_workout_prompt(metrics, goal_type)

    llm = get_llm_client()
    raw_response = await llm.generate(prompt)

    try:
        structured = json.loads(raw_response)
        structured_json = json.dumps(structured)
    except json.JSONDecodeError:
        structured_json = json.dumps({"raw": raw_response, "parse_error": True})

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
