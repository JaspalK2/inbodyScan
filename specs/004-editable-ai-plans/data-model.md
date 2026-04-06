# Data Model: Editable AI-Generated Plans

**Feature**: 004-editable-ai-plans  
**Date**: 2026-04-02

---

## Existing Entities (no schema changes required)

### WorkoutRecommendation

Already exists in `services/recommendation-service/src/models/workout_recommendation.py`.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID (PK) | |
| user_id | str | FK to auth_users |
| scan_id | str | FK to scans |
| goal_type | str | e.g. "muscle_gain", "fat_loss" |
| llm_response | Text | Raw LLM output |
| structured_plan | Text (JSON) | Parsed plan JSON (see structure below) |
| edited_plan | Text (JSON) \| NULL | User-modified plan JSON; NULL = unedited |
| created_at | datetime | |

**`structured_plan` JSON shape** (from `build_workout_prompt`):
```json
{
  "summary": "...",
  "weeks": [
    {
      "week": 1,
      "days": [
        {
          "day": 1,
          "focus": "Upper Body Strength",
          "exercises": [
            {"name": "Bench Press", "sets": 4, "reps": "8-10", "rest_seconds": 90, "notes": "..."}
          ],
          "estimated_duration_minutes": 60
        }
      ]
    }
  ],
  "progression_notes": "..."
}
```

**Edit state logic**:
- If `edited_plan` is non-null → display `edited_plan`; it is the canonical current view
- If `edited_plan` is null → display `structured_plan`; this is the pristine AI-generated version
- Discard = set `edited_plan` back to null (or revert to last saved state in frontend)

---

### DietRecommendation

Already exists in `services/recommendation-service/src/models/diet_recommendation.py`.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID (PK) | |
| user_id | str | FK to auth_users |
| scan_id | str | FK to scans |
| goal_type | str | |
| llm_response | Text | Raw LLM output |
| structured_plan | Text (JSON) | Parsed plan JSON (see structure below) |
| edited_plan | Text (JSON) \| NULL | User-modified plan JSON; NULL = unedited |
| created_at | datetime | |

**`structured_plan` JSON shape** (from `build_diet_prompt`):
```json
{
  "summary": "...",
  "daily_targets": {"calories": 2200, "protein_g": 180, "carbs_g": 220, "fat_g": 60, "fiber_g": 30},
  "macro_targets": {"calories": 2200, "protein_g": 180, ...},
  "days": [
    {
      "day": 1,
      "meals": [
        {
          "meal": "breakfast",
          "foods": ["150g oats", "2 eggs"],
          "calories": 450,
          "protein_g": 28,
          "carbs_g": 55,
          "fat_g": 10
        }
      ],
      "day_totals": {"calories": 2190, "protein_g": 178, "carbs_g": 218, "fat_g": 59, "fiber_g": 29}
    }
  ],
  "micronutrient_highlights": ["..."],
  "meal_prep_tips": ["..."]
}
```

---

## Derived / Computed Values (no DB storage)

### WorkoutQualityScore

Computed by `score_workout_split(days)` in `workout_scorer.py`. Not persisted. Recomputed on demand.

| Field | Type | Notes |
|-------|------|-------|
| overall | int (0–100) | Weighted aggregate |
| coverage_score | int | Muscle group coverage |
| volume_score | int | Total weekly sets |
| balance_score | int | Push/pull/leg balance |
| cardio_score | int | Cardio inclusion |
| frequency_score | int | Training frequency |
| covered_groups | list[str] | |
| missing_groups | list[str] | |
| weekly_sets_per_group | dict[str, int] | |
| feedback | list[str] | Human-readable tips |
| label | str | e.g. "Excellent", "Good" |

**Input adapter for generated plans**: The LLM uses `"name"` for exercises; the scorer expects `"exercise_name"`. The `POST /recommendations/workout/score-plan` endpoint maps `name → exercise_name` before calling `score_workout_split`.

**Flattening structure**: The scorer expects `days: list[dict]` where each dict has an `exercises` list. The generated plan has a `weeks[].days[]` nesting. The endpoint flattens all days from all weeks into a single list for scoring (total program coverage, not per-week).

### MacroTotals

Computed client-side by summing meal values from the plan JSON.

| Field | Type | Notes |
|-------|------|-------|
| total_calories | float | Sum of all meals' `calories` |
| total_protein_g | float | Sum of all meals' `protein_g` |
| total_carbs_g | float | Sum of all meals' `carbs_g` |
| total_fat_g | float | Sum of all meals' `fat_g` |

Displayed as a pie chart with slices for protein / carbs / fat (by caloric contribution).

---

## State Transitions

### Plan Edit State (Frontend)

```
[No Plan] → generate → [Viewing: structured_plan | score=AI-optimal]
[Viewing] → enter edit mode → [Editing: in-memory edits | live score/macros]
[Editing] → save → PATCH /workout/{id} or PATCH /diet/{id} → [Viewing: edited_plan]
[Editing] → discard → [Viewing: previous saved state]
[Viewing] → generate new → (confirm overwrite?) → [Viewing: new structured_plan]
```

### Score Display Logic

- Initial display: Score computed from `structured_plan` by calling `POST /recommendations/workout/score-plan` once at load time
- During editing: Score recomputed via debounced (300 ms) call to same endpoint with current in-memory exercise state
- After save: Score reflects the saved `edited_plan`
