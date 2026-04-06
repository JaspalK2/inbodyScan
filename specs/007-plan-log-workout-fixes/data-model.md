# Data Model: Plan Log and Workout Fixes (007)

## New Backend Endpoint

### DELETE /api/recommendations/diet/{id}

Deletes a `DietRecommendation` record scoped to the authenticated user.

| Field | Value |
|-------|-------|
| Method | DELETE |
| Path | `/api/recommendations/diet/{id}` |
| Auth | Required (user-scoped) |
| Success | 204 No Content |
| Error | 404 if not found or belongs to different user |

**Implementation**: Mirror the existing `DELETE /api/recommendations/splits/{id}` pattern in `recommendations.py`.

## Existing Entities (Affected by UI Changes)

### DietRecommendation
Existing model. New: deletable via UI.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | |
| user_id | UUID | Scoped filter on delete |
| goal_type | string | |
| structured_plan | JSON | |
| edited_plan | JSON \| null | |
| created_at | datetime | |

### DayPlan
Existing model. Fix: `items_snapshot` must be populated when saving from diet plan.

| Field | Type | Notes |
|-------|------|-------|
| entries[].items_snapshot | MealItem[] \| null | MUST be populated with per-food items when saving from DietDayRow |

### CustomMeal
Existing model. New: UI groups by name prefix.

Naming convention (stable from feature 006):
- **Day Planner sourced**: name starts with `"Day Planner — "`, description = `"Saved from Day N diet plan"`
- **User created**: name is user-chosen, no standard prefix

Grouping logic:
- Parse `description` for `"Saved from Day N diet plan"` to extract day number N
- Group all day-planner meals by N under "Day N" heading
- All other meals go in "My Meals"

### WorkoutRecommendation (exercise sets field)
Existing model. Fix: Sets stored as raw string during editing, parsed to int on save.

In `WorkoutPlanCard` edit mode local state, `ex.sets` will be treated as `string | number` during editing to allow free text input.
