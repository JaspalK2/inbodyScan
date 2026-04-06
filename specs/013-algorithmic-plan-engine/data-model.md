# Data Model: Algorithmic Plan Engine

**Feature**: `013-algorithmic-plan-engine`  
**Date**: 2026-04-05

No new database tables are required. All changes are to in-memory data structures and local files. The existing `diet_recommendations` and `workout_recommendations` tables are unchanged.

---

## New Local Data Files

### `src/data/foods.json` (new, seeded from USDA)

Array of food objects. Each entry:

```json
{
  "fdc_id": 171705,
  "name": "Chicken breast, raw",
  "category": "Poultry Products",
  "calories_per_100g": 120.0,
  "protein_per_100g": 22.5,
  "carbs_per_100g": 0.0,
  "fat_per_100g": 2.6,
  "fiber_per_100g": 0.0,
  "tags": ["protein_source", "low_carb"],
  "restrictions": {
    "vegetarian": false,
    "vegan": false,
    "gluten_free": true,
    "dairy_free": true,
    "halal": true,
    "kosher": false
  },
  "meal_slots": ["lunch", "dinner"],
  "last_updated": "2026-04-05"
}
```

**Fields**:
- `fdc_id`: USDA unique identifier (integer)
- `name`: human-readable food name
- `category`: USDA food category string
- `calories/protein/carbs/fat/fiber_per_100g`: macro values per 100g (float)
- `tags`: list of role tags (`protein_source`, `carb_source`, `fat_source`, `vegetable`, `fruit`, `dairy`, etc.)
- `restrictions`: boolean flags for each supported dietary restriction
- `meal_slots`: which meal slots this food is appropriate for (subset of `["breakfast", "lunch", "dinner", "snack"]`)
- `last_updated`: ISO date string for tracking refresh age

### `src/data/exercises.json` (existing, unchanged)

873 exercises with `primaryMuscles`, `secondaryMuscles`, `category`, `equipment`, `level`. No changes.

---

## New In-Memory Structures (Python dataclasses, no DB)

### `WorkoutDayPlan`
```python
@dataclass
class WorkoutDayPlan:
    day: int                    # 1–7
    focus: str                  # e.g. "Push – Chest & Triceps"
    is_rest: bool
    exercises: list[ExerciseSlot]
    estimated_duration_minutes: int
```

### `ExerciseSlot`
```python
@dataclass
class ExerciseSlot:
    name: str
    sets: int
    reps: str          # e.g. "8-12" or "30 min"
    rest_seconds: int
    notes: str         # brief form cue
    muscle_group: str  # primary muscle targeted
```

### `MealSlot`
```python
@dataclass
class MealSlot:
    meal: str           # "breakfast" | "lunch" | "dinner" | "snack"
    foods: list[str]    # e.g. ["150g chicken breast", "1 cup brown rice"]
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
```

### `DietDayPlan`
```python
@dataclass
class DietDayPlan:
    day: int
    meals: list[MealSlot]
    day_totals: dict    # computed by summing meals — never assumed
```

---

## Existing Entities (unchanged)

- `DietRecommendation`: `id`, `user_id`, `scan_id`, `goal_type`, `llm_response`, `structured_plan` (JSON), `created_at`
- `WorkoutRecommendation`: `id`, `user_id`, `scan_id`, `goal_type`, `llm_response`, `structured_plan` (JSON), `created_at`

The `structured_plan` JSON column stores the serialised output of the new algorithmic engines. Schema is identical to what the LLM previously returned — frontend requires no changes.
