from __future__ import annotations
import json
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, model_validator


# ── Macros ───────────────────────────────────────────────────────────────────

class MacroRequest(BaseModel):
    metrics: dict[str, float | None]
    goal_type: str
    age: int | None = None
    height_cm: float | None = None
    gender: str | None = None
    activity_level: str = "moderate"

class MacroTargetsOut(BaseModel):
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    bmr: int
    tdee: int
    goal_adjustment_kcal: int
    protein_ratio: str
    notes: str


# ── Food ─────────────────────────────────────────────────────────────────────

class FoodResultOut(BaseModel):
    fdc_id: int
    name: str
    brand: str | None = None
    category: str | None = None
    calories_kcal: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None
    sugar_g: float | None = None
    sodium_mg: float | None = None
    potassium_mg: float | None = None
    calcium_mg: float | None = None
    iron_mg: float | None = None
    vitamin_c_mg: float | None = None
    vitamin_d_ug: float | None = None
    serving_size: float | None = None
    serving_unit: str | None = None


# ── Custom Meals ─────────────────────────────────────────────────────────────

class MealItemIn(BaseModel):
    fdc_id: int | None = None
    food_name: str
    quantity_g: float = 100.0
    entered_quantity: float | None = None
    entered_unit: str | None = None
    calories_kcal: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None
    sodium_mg: float | None = None

class MealItemOut(MealItemIn):
    id: str
    meal_id: str
    model_config = {"from_attributes": True}

class CustomMealCreate(BaseModel):
    name: str
    description: str | None = None
    items: list[MealItemIn] = []

class CustomMealUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    items: list[MealItemIn] | None = None

class CustomMealOut(BaseModel):
    id: str
    user_id: str
    name: str
    description: str | None
    items: list[MealItemOut] = []
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


# ── Day Plans ─────────────────────────────────────────────────────────────────

class DayPlanEntryIn(BaseModel):
    meal_slot: str                        # breakfast|lunch|dinner|snack|other
    custom_meal_id: str | None = None
    custom_meal_name: str | None = None
    calories_kcal: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None
    items_snapshot: list[dict] | None = None

class DayPlanEntryOut(BaseModel):
    id: str
    day_plan_id: str
    meal_slot: str
    custom_meal_id: str | None
    custom_meal_name: str | None
    calories_kcal: float | None
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None
    fiber_g: float | None
    items_snapshot: list[dict] | None = None
    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def parse_snapshot(cls, v):
        if hasattr(v, "__dict__") and not isinstance(v, dict):
            # Convert ORM object to a plain dict so we never mutate the live
            # session-tracked object (which would mark it dirty and cause asyncpg
            # to flush a Python list into a TEXT column on the next query).
            data = {k: val for k, val in vars(v).items() if not k.startswith("_")}
            snap = data.get("items_snapshot")
            if isinstance(snap, str):
                try:
                    data["items_snapshot"] = json.loads(snap)
                except Exception:
                    pass
            return data
        if isinstance(v, dict):
            snap = v.get("items_snapshot")
            if isinstance(snap, str):
                try:
                    return {**v, "items_snapshot": json.loads(snap)}
                except Exception:
                    pass
        return v

class DayPlanCreate(BaseModel):
    name: str
    plan_date: date | None = None
    notes: str | None = None
    entries: list[DayPlanEntryIn] = []

class DayPlanOut(BaseModel):
    id: str
    user_id: str
    name: str
    plan_date: date | None
    notes: str | None
    entries: list[DayPlanEntryOut] = []
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


# ── Workout Splits ────────────────────────────────────────────────────────────

class ExerciseIn(BaseModel):
    exercise_name: str
    sets: int | None = None
    reps: str | None = None
    weight_kg: float | None = None
    rest_seconds: int | None = None
    notes: str | None = None

class ExerciseOut(ExerciseIn):
    id: str
    day_id: str
    sort_order: int = 0
    model_config = {"from_attributes": True}

class SplitDayIn(BaseModel):
    day_label: str
    focus: str | None = None
    is_rest: bool = False
    exercises: list[ExerciseIn] = []

class SplitDayOut(BaseModel):
    id: str
    split_id: str
    day_label: str
    focus: str | None
    is_rest: bool
    exercises: list[ExerciseOut] = []
    model_config = {"from_attributes": True}

class WorkoutSplitCreate(BaseModel):
    name: str
    description: str | None = None
    days: list[SplitDayIn] = []

class WorkoutScoreOut(BaseModel):
    overall: int
    coverage_score: int
    volume_score: int
    balance_score: int
    cardio_score: int
    frequency_score: int
    covered_groups: list[str]
    missing_groups: list[str]
    weekly_sets_per_group: dict[str, int]
    feedback: list[str]
    label: str

class WorkoutSplitOut(BaseModel):
    id: str
    user_id: str
    name: str
    description: str | None
    days: list[SplitDayOut] = []
    score: WorkoutScoreOut | None = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


# ── LLM Recommendations ───────────────────────────────────────────────────────

class GenerateDietRequest(BaseModel):
    scan_id: str
    metrics: dict[str, float | None]
    goal_type: str
    dietary_restrictions: list[str] = []
    age: int | None = None
    height_cm: float | None = None
    gender: str | None = None
    activity_level: str = "moderate"

class GenerateWorkoutRequest(BaseModel):
    scan_id: str
    metrics: dict[str, float | None]
    goal_type: str

class PlanEditRequest(BaseModel):
    edited_plan: dict   # full edited plan JSON

class WorkoutScorePlanRequest(BaseModel):
    plan: dict  # full structured_plan or edited_plan JSON (weeks[].days[].exercises[])


class ExerciseSearchResult(BaseModel):
    name: str
    primary_muscles: list[str]
    secondary_muscles: list[str]
    category: str
    equipment: str
    level: str


def _parse_plan(values, field: str):
    val = getattr(values, field, None) if hasattr(values, "__dict__") else values.get(field)
    if isinstance(val, str):
        try:
            parsed = json.loads(val)
            if hasattr(values, "__dict__"):
                object.__setattr__(values, field, parsed)
            else:
                values[field] = parsed
        except json.JSONDecodeError:
            pass
    return values


class DietRecommendationOut(BaseModel):
    id: str
    user_id: str
    scan_id: str
    goal_type: str
    structured_plan: dict
    edited_plan: dict | None = None
    created_at: datetime
    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def parse_plans(cls, v):
        v = _parse_plan(v, "structured_plan")
        v = _parse_plan(v, "edited_plan")
        return v


class WorkoutRecommendationOut(BaseModel):
    id: str
    user_id: str
    scan_id: str
    goal_type: str
    structured_plan: dict
    edited_plan: dict | None = None
    created_at: datetime
    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def parse_plans(cls, v):
        v = _parse_plan(v, "structured_plan")
        v = _parse_plan(v, "edited_plan")
        return v


# ── Food Log Schemas ───────────────────────────────────────────────────────────

class FoodLogEntryIn(BaseModel):
    fdc_id: int | None = None
    food_name: str
    brand: str | None = None
    source: str = "manual"
    source_ref_id: str | None = None
    quantity_g: float
    entered_quantity: float | None = None
    entered_unit: str | None = None
    calories_kcal: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None

class FoodLogBatchCreate(BaseModel):
    log_date: date
    entries: list[FoodLogEntryIn]

class FoodLogEntryOut(FoodLogEntryIn):
    id: str
    user_id: str
    log_date: date
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
