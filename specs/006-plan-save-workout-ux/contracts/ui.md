# UI Contracts: Plan Save Flow and Workout UX Fixes (006)

All changes are frontend-only. No new backend endpoints are introduced.
Existing endpoints used: `POST /meals`, `POST /day-plans`, `PATCH /workout/{id}`, `POST /splits/score`.

---

## Contract 1: "Save Day" Composite Action (DietDayRow)

**Trigger**: User clicks "Save Day" button on any diet plan day row.

**Precondition**: At least one meal slot in the day has a non-empty foods list.

**Action sequence**:
1. Validate ≥ 1 non-empty meal slot. If none: show error toast "No meals to save — add foods first." Abort.
2. Call `POST /api/recommendations/day-plans` with:
   - `name`: `"Day {N} — {goal_type}"` (auto-generated, where N is the day number)
   - `plan_date`: null (no specific date)
   - `entries`: one entry per meal slot containing `meal_slot`, `calories_kcal`, `protein_g`, `carbs_g`, `fat_g`, `fiber_g`, `items_snapshot`
3. On day plan save success: call `POST /api/recommendations/meals` for each non-empty meal slot simultaneously:
   - `name`: `"Day Planner — {Slot}"` (e.g., `"Day Planner — Breakfast"`)
   - `description`: `"Saved from Day {N} diet plan"`
   - `items`: mapped from the meal's food items with macros
4. On full success: invalidate `["custom-meals"]` and `["day-plans"]` queries; show success toast "Day saved — {N} meals added to Saved Meals."
5. On partial meal save failure: show warning toast listing which slots failed; day plan record remains.

**UI state during action**: Save Day button shows spinner; all other day actions disabled.

---

## Contract 2: Saved Meals Tab Content (FoodMealsTab)

**What appears in the "saved" sub-tab**:
- All `CustomMeal` records for the authenticated user, sorted by `created_at` descending.
- Includes user-named meals AND "Day Planner — [Slot]" auto-saved meals.
- Does NOT include `DayPlan` records (those are in the Day Planner tab only).
- The "Day Plans" section added in feature 005 MUST be removed.

**Empty state**: "No saved meals yet. Build a meal in the search tab or save a generated diet day."

---

## Contract 3: Exercise Row — View Mode Labels

**Before (current)**:
```
· Bench Press — 3×8-12 (60s rest)
```

**After (required)**:
```
· Bench Press
  Sets: 3  ·  Reps: 8–12  ·  Weight: 60 kg  ·  Rest: 60 s
```

Rules:
- If `weight_kg` is null or 0: omit the Weight field entirely.
- If `rest_seconds` is null or 0: omit the Rest field entirely.
- If `sets` is null: show "Sets: —".
- If `reps` is null or empty: show "Reps: —".

---

## Contract 4: Exercise Row — Edit Mode Labels

Each exercise row in edit mode uses a grid layout. Each input MUST have a label above or a placeholder that names the field:

| Input | Label / Placeholder |
|-------|-------------------|
| Name (typeahead) | Label: "Exercise" OR placeholder "Search exercise…" |
| Sets | Label: "Sets" |
| Reps | Label: "Reps" (e.g. 8-12) |
| Weight | Label: "kg" suffix or label "Weight (kg)" |
| Rest | Label: "Rest (s)" |
| Remove button | aria-label="Remove exercise" |

---

## Contract 5: Add/Remove Exercises in Generated Workout Plan Edit Mode

**Add exercise button**: Appears below the last exercise row on each non-rest day. Label: "+ Add exercise". On click:
- Appends `{ name: "", sets: 3, reps: "8-12", weight_kg: null, rest_seconds: 60 }` to the day's exercise list.
- Score debounce fires (300ms).

**Remove exercise button**: Appears on each exercise row. Icon: `X` or `Trash2`. On click:
- Removes that exercise from the day's list.
- Score debounce fires (300ms).

**Rest days**: No "Add exercise" button shown. No exercise rows shown.

---

## Contract 6: Live Score in Split Builder

The custom split builder (`WorkoutTab`) currently shows score only after saving. This changes:

- Score panel MUST appear as soon as ≥ 1 exercise exists across any day.
- Score recalculates via `POST /api/recommendations/splits/score` with 300ms debounce on every change to `days` state (exercise added, removed, name changed, sets/reps changed).
- Score panel placement: same visual style as in the generated workout plan card (coverage/volume/balance/cardio/frequency sub-scores + feedback bullets).
- Score panel disappears when all days have 0 exercises.
