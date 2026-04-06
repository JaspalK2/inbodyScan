# API Contracts: Plan Log and Workout Fixes (007)

## New Endpoint: Delete Diet Recommendation

```
DELETE /api/recommendations/diet/{id}
Authorization: Bearer <token>

Success: 204 No Content
Error:   404 {"detail": "Diet recommendation not found"}
```

All other endpoints used in this feature already exist. No other backend changes required.

## UI Contracts

### Contract 1: DayPlannerTab — "Log this day" must log food items

The `applyPlanMutation` in `DayPlannerTab` maps `DayPlanEntry.items_snapshot` to food log entries. For this to work, `items_snapshot` MUST be populated when the day plan is saved. The `saveDayPlan()` function in `DietDayRow` must include `items_snapshot` with individual food items per entry (currently it sets macro totals but the items_snapshot structure is already correct in the code).

**Verification**: After "Save Day" → Day Planner → "Log this day" → food log for today shows individual food entries, not just macro aggregates.

### Contract 2: Saved Meals Tab — Two sections

```
Section 1: "Day Planner Meals"
  - Only meals where name.startsWith("Day Planner — ")
  - Grouped by day number extracted from description field
  - Sub-heading per day: "Day 1", "Day 2", etc.
  - If no day-planner meals: section is hidden entirely

Section 2: "My Meals"  
  - Only meals where name does NOT start with "Day Planner — "
  - Sorted by created_at descending
  - If no user meals: section is hidden entirely

If both are empty: single empty state message shown
```

### Contract 3: Diet Plan Delete

```
DietPlanCard receives onDelete?: () => void prop
Delete button: Trash2 icon, top-right of card header
Confirmation: window.confirm("Delete this diet plan? This cannot be undone.")
On confirm: call DELETE /api/recommendations/diet/{id}
On success: invalidate ["diet-recs"] query
```

### Contract 4: Workout Sets Field — Free Editing

```
Sets input onChange: sets: e.target.value  (store raw string)
Sets input value: String(ex.sets ?? "")    (display as string)
On save: parseInt(ex.sets) || undefined    (parse at save boundary only)
```

### Contract 5: Nested Button Fix in WorkoutPlanCard

The outer `<button>` in `WorkoutPlanCard` (the expand/collapse toggle) must be changed to `<div>` with `cursor-pointer` styling. The inner `<Button>` (Edit button) remains as-is. This is the same fix applied to `DietPlanCard` in feature 005.

### Contract 6: AI Workout Prompt — Coverage Requirements

The workout prompt must explicitly list all required muscle groups and set minimums:
```
Required muscle groups (all must be covered):
chest, back (upper + lower), shoulders (front + side + rear),
biceps, triceps, quadriceps, hamstrings, glutes, calves, core/abs

Volume requirements:
- Minimum 3 sets per muscle group per week
- Include compound movements (squat, deadlift, bench, row, press)
- Include push and pull movements each week
- Include at least 1 dedicated cardio or conditioning session per week
```
