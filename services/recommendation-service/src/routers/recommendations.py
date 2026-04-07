from __future__ import annotations
from dataclasses import asdict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
import json

from ..schemas.recommendation import (
    MacroRequest, MacroTargetsOut,
    FoodResultOut,
    CustomMealCreate, CustomMealUpdate, CustomMealOut, MealItemOut,
    DayPlanCreate, DayPlanOut, DayPlanEntryOut,
    WorkoutSplitCreate, WorkoutSplitOut, SplitDayOut, ExerciseOut, WorkoutScoreOut,
    GenerateDietRequest, GenerateWorkoutRequest, PlanEditRequest, WorkoutScorePlanRequest,
    DietRecommendationOut, WorkoutRecommendationOut,
    ExerciseSearchResult,
)
from ..services.macro_calculator import calculate_macros
from ..services.food_search import search_foods, get_food_detail
from ..services.meal_service import (
    create_custom_meal, get_custom_meals, get_custom_meal, get_meal_items,
    delete_custom_meal, update_custom_meal,
    create_day_plan, get_day_plans, get_day_plan, get_day_plan_entries, delete_day_plan,
)
from ..services.split_service import (
    create_split, get_splits, get_split_with_score, delete_split,
)
from ..services.workout_scorer import score_workout_split
from ..services.recommendation_service import (
    generate_diet_recommendation, generate_workout_recommendation,
    get_diet_recommendations, get_workout_recommendations,
)
from ..services.exercise_search import search_exercises
from ..services.food_log_service import (
    create_log_entries, get_entries_for_date, delete_entry, get_logged_dates,
)
from ..schemas.recommendation import FoodLogBatchCreate, FoodLogEntryOut
from ..db.session import get_db
from shared.python.auth_utils.dependencies import get_current_user_id

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


# ── Macros ────────────────────────────────────────────────────────────────────

@router.post("/diet/macros", response_model=MacroTargetsOut)
async def calculate_diet_macros(body: MacroRequest):
    targets = calculate_macros(
        body_weight_kg=body.metrics.get("body_weight_kg"),
        fat_free_mass_kg=body.metrics.get("fat_free_mass_kg"),
        body_fat_percentage=body.metrics.get("body_fat_percentage"),
        age=body.age, height_cm=body.height_cm, gender=body.gender,
        goal_type=body.goal_type, activity_level=body.activity_level,
    )
    return MacroTargetsOut(**asdict(targets))


# ── Exercise Search ───────────────────────────────────────────────────────────

@router.get("/exercises/search", response_model=list[ExerciseSearchResult])
async def search_exercises_endpoint(
    q: str = Query(..., min_length=2, description="Search term (min 2 characters)"),
    limit: int = Query(20, le=50),
    user_id: str = Depends(get_current_user_id),
):
    """Search the CC0 exercise dataset by name (case-insensitive substring match)."""
    return search_exercises(q, limit)


# ── Food Search ───────────────────────────────────────────────────────────────

@router.get("/food/search", response_model=list[FoodResultOut])
async def search_food(q: str = Query(..., min_length=2), page_size: int = Query(25, le=50), user_id: str = Depends(get_current_user_id)):
    results = await search_foods(q, page_size)
    return [FoodResultOut(**r.__dict__) for r in results]


@router.get("/food/{fdc_id}", response_model=FoodResultOut)
async def get_food(fdc_id: int, user_id: str = Depends(get_current_user_id)):
    result = await get_food_detail(fdc_id)
    if not result:
        raise HTTPException(status_code=404, detail="Food not found")
    return FoodResultOut(**result.__dict__)


# ── Custom Meals ──────────────────────────────────────────────────────────────

@router.post("/meals", response_model=CustomMealOut, status_code=status.HTTP_201_CREATED)
async def create_meal(body: CustomMealCreate, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    meal = await create_custom_meal(session, user_id, body.name, body.description, [i.model_dump() for i in body.items])
    items = await get_meal_items(session, meal.id)
    return CustomMealOut(
        id=meal.id, user_id=meal.user_id, name=meal.name, description=meal.description,
        items=[MealItemOut.model_validate(i) for i in items],
        created_at=meal.created_at, updated_at=meal.updated_at,
    )


@router.get("/meals", response_model=list[CustomMealOut])
async def list_meals(user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    meals = await get_custom_meals(session, user_id)
    result = []
    for meal in meals:
        items = await get_meal_items(session, meal.id)
        result.append(CustomMealOut(
            id=meal.id, user_id=meal.user_id, name=meal.name, description=meal.description,
            items=[MealItemOut.model_validate(i) for i in items],
            created_at=meal.created_at, updated_at=meal.updated_at,
        ))
    return result


@router.get("/meals/{meal_id}", response_model=CustomMealOut)
async def get_meal(meal_id: str, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    meal = await get_custom_meal(session, meal_id, user_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    items = await get_meal_items(session, meal.id)
    return CustomMealOut(
        id=meal.id, user_id=meal.user_id, name=meal.name, description=meal.description,
        items=[MealItemOut.model_validate(i) for i in items],
        created_at=meal.created_at, updated_at=meal.updated_at,
    )


@router.patch("/meals/{meal_id}", response_model=CustomMealOut)
async def update_meal(meal_id: str, body: CustomMealUpdate, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    meal = await update_custom_meal(session, meal_id, user_id, body.name, body.description, [i.model_dump() for i in body.items] if body.items is not None else None)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    items = await get_meal_items(session, meal.id)
    return CustomMealOut(
        id=meal.id, user_id=meal.user_id, name=meal.name, description=meal.description,
        items=[MealItemOut.model_validate(i) for i in items],
        created_at=meal.created_at, updated_at=meal.updated_at,
    )


@router.delete("/meals/{meal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal(meal_id: str, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    if not await delete_custom_meal(session, meal_id, user_id):
        raise HTTPException(status_code=404, detail="Meal not found")


# ── Day Plans ─────────────────────────────────────────────────────────────────

@router.post("/day-plans", response_model=DayPlanOut, status_code=status.HTTP_201_CREATED)
async def create_plan(body: DayPlanCreate, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    plan = await create_day_plan(session, user_id, body.name, body.plan_date, body.notes, [e.model_dump() for e in body.entries])
    entries = await get_day_plan_entries(session, plan.id)
    return DayPlanOut(
        id=plan.id, user_id=plan.user_id, name=plan.name, plan_date=plan.plan_date, notes=plan.notes,
        entries=[DayPlanEntryOut.model_validate(e) for e in entries],
        created_at=plan.created_at, updated_at=plan.updated_at,
    )


@router.get("/day-plans", response_model=list[DayPlanOut])
async def list_plans(user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    plans = await get_day_plans(session, user_id)
    result = []
    for plan in plans:
        entries = await get_day_plan_entries(session, plan.id)
        result.append(DayPlanOut(
            id=plan.id, user_id=plan.user_id, name=plan.name, plan_date=plan.plan_date, notes=plan.notes,
            entries=[DayPlanEntryOut.model_validate(e) for e in entries],
            created_at=plan.created_at, updated_at=plan.updated_at,
        ))
    return result


@router.delete("/day-plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(plan_id: str, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    if not await delete_day_plan(session, plan_id, user_id):
        raise HTTPException(status_code=404, detail="Day plan not found")


# ── Workout Splits ────────────────────────────────────────────────────────────

@router.post("/splits", response_model=WorkoutSplitOut, status_code=status.HTTP_201_CREATED)
async def create_workout_split(body: WorkoutSplitCreate, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    split, score = await create_split(session, user_id, body.name, body.description, [d.model_dump() for d in body.days])
    full = await get_split_with_score(session, split.id, user_id)
    if not full:
        raise HTTPException(status_code=500, detail="Failed to retrieve split")
    s, days, sc = full
    return _build_split_out(s, days, sc)


@router.get("/splits", response_model=list[WorkoutSplitOut])
async def list_splits(user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    splits = await get_splits(session, user_id)
    result = []
    for sp in splits:
        full = await get_split_with_score(session, sp.id, user_id)
        if full:
            s, days, sc = full
            result.append(_build_split_out(s, days, sc))
    return result


@router.get("/splits/{split_id}", response_model=WorkoutSplitOut)
async def get_split_detail(split_id: str, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    full = await get_split_with_score(session, split_id, user_id)
    if not full:
        raise HTTPException(status_code=404, detail="Split not found")
    s, days, sc = full
    return _build_split_out(s, days, sc)


@router.post("/splits/score", response_model=WorkoutScoreOut)
async def score_split(body: WorkoutSplitCreate, user_id: str = Depends(get_current_user_id)):
    """Score a split without saving it — useful for live preview."""
    days = [d.model_dump() for d in body.days]
    score = score_workout_split(days)
    return WorkoutScoreOut(**asdict(score))


@router.post("/workout/score-plan", response_model=WorkoutScoreOut)
async def score_generated_plan(body: WorkoutScorePlanRequest, user_id: str = Depends(get_current_user_id)):
    """Score a generated (or edited) workout plan without saving — used for live score updates.

    Flattens plan.weeks[].days[] into a single day list and maps exercise 'name' → 'exercise_name'
    to match the format expected by score_workout_split().
    """
    days: list[dict] = []
    for week in body.plan.get("weeks", []):
        for day in week.get("days", []):
            exercises = [
                {**{k: v for k, v in ex.items() if k != "name"}, "exercise_name": ex.get("name", ex.get("exercise_name", ""))}
                for ex in day.get("exercises", [])
            ]
            days.append({**day, "exercises": exercises})
    score = score_workout_split(days)
    return WorkoutScoreOut(**asdict(score))


@router.delete("/splits/{split_id}", status_code=status.HTTP_204_NO_CONTENT)
async def del_split(split_id: str, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    if not await delete_split(session, split_id, user_id):
        raise HTTPException(status_code=404, detail="Split not found")


# ── LLM Plan Generation ───────────────────────────────────────────────────────

@router.post("/diet/generate", response_model=DietRecommendationOut, status_code=status.HTTP_201_CREATED)
async def generate_diet(body: GenerateDietRequest, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    try:
        return await generate_diet_recommendation(
            session, user_id, body.scan_id, body.metrics, body.goal_type,
            body.dietary_restrictions, body.age, body.height_cm, body.gender, body.activity_level,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Diet plan generation failed: {exc}") from exc


@router.patch("/diet/{rec_id}", response_model=DietRecommendationOut)
async def edit_diet_plan(rec_id: str, body: PlanEditRequest, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from ..models.diet_recommendation import DietRecommendation
    r = await session.execute(select(DietRecommendation).where(DietRecommendation.id == rec_id, DietRecommendation.user_id == user_id))
    rec = r.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    rec.edited_plan = json.dumps(body.edited_plan)
    await session.commit()
    await session.refresh(rec)
    return DietRecommendationOut.model_validate(rec)


@router.delete("/diet/{rec_id}", status_code=status.HTTP_204_NO_CONTENT)
async def del_diet(rec_id: str, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from ..models.diet_recommendation import DietRecommendation
    r = await session.execute(select(DietRecommendation).where(DietRecommendation.id == rec_id, DietRecommendation.user_id == user_id))
    rec = r.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Diet recommendation not found")
    await session.delete(rec)
    await session.commit()


@router.get("/diet", response_model=list[DietRecommendationOut])
async def list_diet(user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    return [DietRecommendationOut.model_validate(r) for r in await get_diet_recommendations(session, user_id)]


@router.post("/workout/generate", response_model=WorkoutRecommendationOut, status_code=status.HTTP_201_CREATED)
async def generate_workout(body: GenerateWorkoutRequest, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    try:
        return await generate_workout_recommendation(session, user_id, body.scan_id, body.metrics, body.goal_type)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Workout plan generation failed: {exc}") from exc


@router.patch("/workout/{rec_id}", response_model=WorkoutRecommendationOut)
async def edit_workout_plan(rec_id: str, body: PlanEditRequest, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from ..models.workout_recommendation import WorkoutRecommendation
    r = await session.execute(select(WorkoutRecommendation).where(WorkoutRecommendation.id == rec_id, WorkoutRecommendation.user_id == user_id))
    rec = r.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    rec.edited_plan = json.dumps(body.edited_plan)
    await session.commit()
    await session.refresh(rec)
    return WorkoutRecommendationOut.model_validate(rec)


@router.delete("/workout/{rec_id}", status_code=status.HTTP_204_NO_CONTENT)
async def del_workout(rec_id: str, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from ..models.workout_recommendation import WorkoutRecommendation
    r = await session.execute(select(WorkoutRecommendation).where(WorkoutRecommendation.id == rec_id, WorkoutRecommendation.user_id == user_id))
    rec = r.scalar_one_or_none()
    if not rec:
        raise HTTPException(status_code=404, detail="Workout recommendation not found")
    await session.delete(rec)
    await session.commit()


@router.get("/workout", response_model=list[WorkoutRecommendationOut])
async def list_workout(user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    return [WorkoutRecommendationOut.model_validate(r) for r in await get_workout_recommendations(session, user_id)]


# ── Food Log ──────────────────────────────────────────────────────────────────

@router.post("/food-log", response_model=list[FoodLogEntryOut], status_code=status.HTTP_201_CREATED)
async def create_food_log(body: FoodLogBatchCreate, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    if not body.entries:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="entries must not be empty")
    records = await create_log_entries(session, user_id, body.log_date, [e.model_dump() for e in body.entries])
    return [FoodLogEntryOut.model_validate(r) for r in records]


@router.get("/food-log/dates", response_model=list[str])
async def list_food_log_dates(user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    dates = await get_logged_dates(session, user_id)
    return [d.isoformat() for d in dates]


@router.get("/food-log", response_model=list[FoodLogEntryOut])
async def get_food_log(date: str = Query(...), user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    from datetime import date as date_cls
    try:
        log_date = date_cls.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date format, expected YYYY-MM-DD")
    entries = await get_entries_for_date(session, user_id, log_date)
    return [FoodLogEntryOut.model_validate(e) for e in entries]


@router.delete("/food-log/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_food_log_entry(entry_id: str, user_id: str = Depends(get_current_user_id), session: AsyncSession = Depends(get_db)):
    if not await delete_entry(session, entry_id, user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")


# ── Food DB Management ────────────────────────────────────────────────────────

@router.post("/food-db/refresh", status_code=status.HTTP_202_ACCEPTED)
async def trigger_food_db_refresh(user_id: str = Depends(get_current_user_id)):
    """Manually trigger a food database refresh from USDA FoodData Central."""
    import asyncio
    from ..services.food_seeder import refresh_food_db_job
    asyncio.create_task(refresh_food_db_job())
    return {"message": "Food database refresh triggered", "status": "accepted"}


@router.get("/food-db/status")
async def food_db_status(user_id: str = Depends(get_current_user_id)):
    """Return metadata about the current local food database."""
    import pathlib, json as _json
    from datetime import timezone
    foods_path = pathlib.Path(__file__).parent.parent / "data" / "foods.json"
    if not foods_path.exists():
        return {"exists": False, "food_count": 0, "last_updated": None}
    data = _json.loads(foods_path.read_text())
    last_updated = None
    if data:
        last_updated = data[0].get("last_updated")
    return {"exists": True, "food_count": len(data), "last_updated": last_updated}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_split_out(split, days: list[dict], score) -> WorkoutSplitOut:
    from ..models.workout_split import WorkoutSplitDay, WorkoutExercise
    day_outs = []
    for d in days:
        exs = [ExerciseOut(id="", day_id="", exercise_name=e["exercise_name"], sets=e.get("sets"), reps=e.get("reps"), weight_kg=e.get("weight_kg"), rest_seconds=e.get("rest_seconds"), notes=e.get("notes")) for e in d.get("exercises", [])]
        day_outs.append(SplitDayOut(id="", split_id=split.id, day_label=d["day_label"], focus=d.get("focus"), is_rest=d.get("is_rest", False), exercises=exs))
    return WorkoutSplitOut(
        id=split.id, user_id=split.user_id, name=split.name, description=split.description,
        days=day_outs, score=WorkoutScoreOut(**asdict(score)),
        created_at=split.created_at, updated_at=split.updated_at,
    )
