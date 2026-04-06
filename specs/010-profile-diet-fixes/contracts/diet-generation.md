# Contract: Diet Generation with Macro Validation (recommendation-service)

**Service**: recommendation-service  
**Change**: Server-side macro validation + retry loop added to `generate_diet_recommendation()`.

---

## POST /api/recommendations/diet (unchanged external contract)

**Auth**: Bearer token required  
**Request body** (no changes to shape):

```json
{
  "scan_id": "uuid",
  "metrics": { "weight_kg": 70.0, "body_fat_percentage": 20.0 },
  "goal_type": "build_muscle",
  "dietary_restrictions": ["vegetarian"],
  "age": 28,
  "height_cm": 175.0,
  "gender": "male",
  "activity_level": "moderately_active"
}
```

**Response** (200 OK): Unchanged — returns `DietRecommendation` with `structured_plan`.

---

## Internal Retry Logic Contract

The following behavior is guaranteed by the implementation:

1. After LLM generation, validate each day in `structured_plan.days`:
   - For each day: check `abs(day_totals[macro] - daily_target[macro]) / daily_target[macro] <= 0.10` for calories, protein_g, carbs_g, fat_g.
   - If **all days pass** → return immediately.
   - If **any day fails** → retry the full generation (up to 3 total attempts).
2. If all 3 attempts produce out-of-range plans → log a warning and return the best attempt (closest to targets by total calorie delta).
3. The retry count is never exposed in the API response.

---

## `_validate_diet_macros(plan, macro_targets) -> bool`

```python
def _validate_diet_macros(plan: dict, macro_targets) -> bool:
    """Return True if every day's totals are within ±10% of targets."""
    targets = {
        "calories": macro_targets.calories,
        "protein_g": macro_targets.protein_g,
        "carbs_g": macro_targets.carbs_g,
        "fat_g": macro_targets.fat_g,
    }
    for day in plan.get("days", []):
        totals = day.get("day_totals", {})
        for key, target in targets.items():
            if target <= 0:
                continue
            actual = totals.get(key, 0)
            if abs(actual - target) / target > 0.10:
                return False
    return True
```

---

## Test Requirements

- `_validate_diet_macros` returns `True` when all days within ±10%
- `_validate_diet_macros` returns `False` when any day's calories are >10% off
- `_validate_diet_macros` returns `True` for an empty days list (no days to fail)
- `generate_diet_recommendation()` retries up to 3× when validator returns `False`
- `generate_diet_recommendation()` returns on first passing attempt (no unnecessary retries)
