# Data Model: Plan Save Flow and Workout UX Fixes (006)

> No new database tables or backend schema changes are required for this feature.
> All entities below are existing structures used or extended by frontend logic only.

## Existing Entities (Used, Not Changed)

### CustomMeal
Stored via `POST /api/recommendations/meals`.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Server-generated |
| user_id | UUID | Scoped to authenticated user |
| name | string | User-chosen OR "Day Planner — {Slot}" for auto-saved meals |
| description | string \| null | Optional |
| items | MealItem[] | Food items with macros |
| created_at | ISO datetime | |
| updated_at | ISO datetime | |

**New naming convention** (no schema change): When a `CustomMeal` is auto-saved from a generated diet day save action, its `name` field uses the format `"Day Planner — {Slot}"` (e.g., `"Day Planner — Breakfast"`). This is a UI-level convention; the backend stores it as a plain string.

### DayPlan
Stored via `POST /api/recommendations/day-plans`.

| Field | Type | Notes |
|-------|------|-------|
| id | UUID | Server-generated |
| user_id | UUID | Scoped to authenticated user |
| name | string | User-provided or auto-generated from diet plan |
| plan_date | date \| null | Optional target date |
| notes | string \| null | |
| entries | DayPlanEntry[] | One per meal slot |
| created_at | ISO datetime | |
| updated_at | ISO datetime | |

### DayPlanEntry (within DayPlan)

| Field | Type | Notes |
|-------|------|-------|
| meal_slot | "breakfast" \| "lunch" \| "dinner" \| "snack" | |
| custom_meal_id | UUID \| null | Reference to CustomMeal |
| custom_meal_name | string \| null | Denormalised name for display |
| calories_kcal | number \| null | Denormalised |
| protein_g | number \| null | |
| carbs_g | number \| null | |
| fat_g | number \| null | |
| fiber_g | number \| null | |
| items_snapshot | MealItem[] \| null | Food item snapshot |

### WorkoutPlan (AI-generated)
Stored via `POST /api/recommendations/workout/generate`. The `structured_plan` JSON shape:

```
{
  summary: string,
  weeks: [
    {
      week: number,
      days: [
        {
          day: number,
          focus: string,
          is_rest: boolean,
          exercises: [
            {
              name: string,
              sets: number,
              reps: string,        // e.g. "8-12"
              weight_kg: number | null,
              rest_seconds: number | null,
              notes: string | null
            }
          ]
        }
      ]
    }
  ]
}
```

**UI-only change**: In edit mode, each exercise row gains a remove button and each non-rest day gains an "Add exercise" button. These changes mutate the local `editedWorkout` state and are persisted via the existing `PATCH /api/recommendations/workout/{id}` endpoint.

### WorkoutSplit (user-built)
Stored via `POST /api/recommendations/splits`. Days and exercises shape mirrors the day-level structure above but without weekly grouping. Score is computed client-side via `POST /api/recommendations/splits/score`.

## State Transitions

### "Save Day" Action (new composite flow)

```
User clicks "Save Day" on generated diet day
  → VALIDATE: at least one meal slot is non-empty
    → FAIL: show error toast, abort
    → PASS: proceed
  → CALL createDayPlan({ name, plan_date, entries })
    → on success: store dayPlanId
    → on failure: show error, abort meal saves
  → CALL createMeal({ name: "Day Planner — {Slot}", items: [...] }) 
     for each non-empty slot (Promise.all)
    → on success: invalidate ["custom-meals"] and ["day-plans"] queries
    → on partial failure: show partial success toast listing which meals failed
```

### Edit Workout Plan — Add/Remove Exercise

```
User clicks "Add exercise" on a non-rest day
  → Append new exercise { name: "", sets: 3, reps: "8-12", weight_kg: null, rest_seconds: 60 }
  → Trigger score debounce (300ms)

User clicks remove icon on an exercise
  → Filter exercise out of day.exercises array
  → Trigger score debounce (300ms)
```
