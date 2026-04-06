# Data Model: Plans UX Fixes and Workout Insights

**Feature**: 011-plans-fixes-workout-insight  
**Date**: 2026-04-05

---

## No Schema Changes Required

This feature makes no changes to the database schema. All changes are to:
1. Frontend computed values (diet day totals)
2. AI prompt structure (workout explanation field)
3. A new backend DELETE endpoint (no new table/column)

---

## Existing Entities (Relevant)

### WorkoutRecommendation

Stored in `workout_recommendations` table. No column changes.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to auth users; all queries MUST filter by this |
| scan_id | UUID | Foreign key to scan that triggered this recommendation |
| goal_type | string | e.g. "build_muscle", "lose_fat" |
| llm_response | text | Raw LLM output |
| structured_plan | JSON | Contains: `days`, `summary`, and now **`plan_explanation`** (new top-level key within JSON) |
| edited_plan | JSON (nullable) | User-edited version |
| created_at | timestamp | |

**`structured_plan` JSON shape (updated)**:
```json
{
  "plan_explanation": "2–4 sentence explanation referencing body composition data",
  "summary": "Overall program description (existing field)",
  "days": [ ... ]
}
```

The `plan_explanation` key is a new top-level field within the existing `structured_plan` JSON blob. No migration required. Existing plans without this field fall back to displaying `summary`.

---

### DietRecommendation

Stored in `diet_recommendations` table. No changes.

The `structured_plan` JSON shape for days:
```json
{
  "days": [
    {
      "day": 1,
      "day_totals": { "calories": 2950, ... },  // THIS FIELD IS NOW IGNORED ON DISPLAY
      "meals": [
        { "name": "Breakfast", "calories": 650, "protein_g": 40, "carbs_g": 70, "fat_g": 15 },
        { "name": "Lunch",     "calories": 700, "protein_g": 45, "carbs_g": 80, "fat_g": 18 },
        { "name": "Dinner",    "calories": 600, "protein_g": 38, "carbs_g": 65, "fat_g": 16 }
      ]
    }
  ]
}
```

**Display rule**: Day totals shown to users MUST be computed by summing `meals[*].calories`, `meals[*].protein_g`, `meals[*].carbs_g`, `meals[*].fat_g`. The `day_totals` object from the AI is ignored entirely.

---

### DayPlan

Stored in `day_plans` table. No changes.

Already fetched via `GET /api/recommendations/day-plans`. Display bug is frontend-only — the query result must be rendered directly in "My Saved Meals" and Day Planner sections.
