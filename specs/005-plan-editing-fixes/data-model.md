# Data Model: Plan Editing and Log Fixes (005)

## No New Database Models Required

All entities needed by this feature map to existing models. No migrations are needed.

---

## Existing Models Used

### CustomMeal + CustomMealItem
**File**: `services/recommendation-service/src/models/custom_meal.py`

Used for **US1 — Save meal from diet plan**.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| user_id | str | FK — enforces user scoping |
| name | str | e.g. "breakfast — muscle gain plan" |
| description | str \| None | Optional context |
| items | CustomMealItem[] | One row per food string |

**CustomMealItem** (child):

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| meal_id | UUID | FK → CustomMeal |
| food_name | str | Full food string, e.g. "200g chicken breast" |
| quantity_g | float | 100 (placeholder — quantity embedded in food_name) |
| calories_kcal | float \| None | Per-meal macro divided by item count (proportional) |
| protein_g | float \| None | Same |
| carbs_g | float \| None | Same |
| fat_g | float \| None | Same |

**Validation**: `items` must have at least one entry (FR-003). Enforced at service layer before insert.

---

### DayPlan + DayPlanEntry
**File**: `services/recommendation-service/src/models/day_plan.py`

Used for **US2 (display in saved tab)** and **US3 (apply to food log)**.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | PK |
| user_id | str | FK — enforces user scoping |
| name | str | e.g. "Day 3 meal plan" |
| plan_date | date \| None | Optional target date |
| notes | str \| None | Source context |
| entries | DayPlanEntry[] | One per meal slot |

**DayPlanEntry** (child):

| Field | Type | Notes |
|-------|------|-------|
| meal_slot | str | "breakfast" / "lunch" / "dinner" / "snack" |
| calories_kcal | float \| None | Aggregate for this slot |
| protein_g | float \| None | |
| carbs_g | float \| None | |
| fat_g | float \| None | |
| items_snapshot | JSONB | Array of `{food_name, quantity_g, calories_kcal, protein_g, ...}` |

When applying a DayPlan to the food log (US3), each `items_snapshot` entry maps directly to a `FoodLogBatchCreate.entries` item.

---

### DailyFoodLogEntry
**File**: `services/recommendation-service/src/models/food_log.py`

Used for **US3 — log applied day plan entries**.

No changes to this model. `source = "day_plan"` and `source_ref_id = day_plan.id` provide traceability.

---

## New: ExerciseLibrary (In-Memory, Not Persisted)

The exercise dataset is loaded from the CC0 static JSON at service startup. It is **not stored in the database** — it lives in application memory as a Python list filtered on search requests.

**Shape of each exercise record** (from `yuhonas/free-exercise-db`):

| Field | Type | Notes |
|-------|------|-------|
| name | str | Display name, e.g. "Barbell Bench Press" |
| primaryMuscles | str[] | e.g. ["chest"] |
| secondaryMuscles | str[] | e.g. ["triceps", "shoulders"] |
| category | str | e.g. "strength" |
| equipment | str | e.g. "barbell" |
| level | str | "beginner" / "intermediate" / "expert" |

**Search endpoint output** (subset returned to client):

```json
{
  "name": "Barbell Bench Press",
  "primary_muscles": ["chest"],
  "secondary_muscles": ["triceps", "shoulders"],
  "category": "strength",
  "equipment": "barbell"
}
```

The `name` field is what gets written into `WorkoutRecommendation.structured_plan` / `edited_plan` when the user selects an exercise replacement.
