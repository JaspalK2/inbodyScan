# Research: Plan Log and Workout Fixes (007)

## Decision 1: Why Day Plans Don't Appear in Day Planner

**Finding**: The `DayPlannerTab` already has a `useQuery({ queryKey: ["day-plans"] })` at line 1095 and renders `DayPlanCard` components with an `onApply` prop at line 1228. The `applyPlanMutation` is wired. The "Log to today" button (BookmarkPlus icon) exists on `DayPlanCard`.

**Root cause**: The `saveDayPlan()` function in `DietDayRow` calls `recommendations.createDayPlan()` which posts to the backend. However, after success it only calls `qc.invalidateQueries({ queryKey: ["day-plans"] })` — but `DayPlannerTab` is a different mounted component. If the query cache is already stale or the component re-fetches correctly, the plan should appear. **The actual issue is likely that the `applyPlanMutation` in `DayPlannerTab` uses `items_snapshot` data from `DayPlanEntry`, but when saved via `DietDayRow.saveDayPlan()`, the `items_snapshot` field may be empty** — the entries only contain macro totals, not individual food items. So "Log this day" has nothing to log item-by-item.

**Decision**: Fix `saveDayPlan()` to include `items_snapshot` with individual food items per meal slot entry. Also confirm that the query invalidation refreshes the DayPlannerTab list correctly (it should — TanStack Query cache is shared).

---

## Decision 2: Saved Meals Grouping — "Day Planner Meals" vs "My Meals"

**Finding**: The FoodMealsTab saved sub-tab (lines 1028–1046) renders a flat list of all `CustomMeal` records. There is no grouping. Day-planner-sourced meals are named `"Day Planner — {Slot}"` (from feature 006). User-created meals have user-chosen names.

**Decision**: Split the flat list into two sections:
1. **Day Planner Meals**: meals whose `name` starts with `"Day Planner — "`. Group by implied day number — parse the `description` field (set to `"Saved from Day N diet plan"`) to extract the day number. Group under `"Day N"` headings.
2. **My Meals**: meals whose `name` does NOT start with `"Day Planner — "`.

**Rationale**: The prefix convention from feature 006 is the reliable discriminator. The `description` field contains the day number — no additional data needed.

---

## Decision 3: Diet Plan Deletion

**Finding**: `DietPlanCard` (line 406) has no `onDelete` prop and no delete button. The `DietTab` does not pass any delete handler. The backend endpoint `DELETE /api/recommendations/diet/{id}` does NOT exist in the current router.

**Decision**: 
1. Add `DELETE /api/recommendations/diet/{id}` backend endpoint (simple deletion by id scoped to user).
2. Add `deleteDiet` to `api.ts` frontend client.
3. Add delete button + confirmation to `DietPlanCard`.

**Rationale**: This requires a small backend change but is straightforward — same pattern as the existing `DELETE /api/recommendations/splits/{id}`.

---

## Decision 4: Workout Edit — Sets Field Blocks Clearing

**Finding**: The Sets input onChange handler uses `parseInt(e.target.value) || ex.sets` (line 1715–1718). This means:
- `parseInt("8")` = 8 ✅
- `parseInt("0")` = 0, which is falsy → falls back to `ex.sets` ❌
- `parseInt("")` = NaN, falsy → falls back to `ex.sets` ❌
- User cannot clear the field to type a new value

The Reps field also has issues (though less critical since reps is a string).

**Decision**: Change all numeric field handlers in WorkoutPlanCard edit mode to use `e.target.value` directly as a string for controlled input, converting to number only when saving. Or use `parseInt(e.target.value)` without the `|| ex.sets` fallback — accept empty/0 values. Simplest fix: store `ex.sets` as the raw input string while editing, parse on save.

**Chosen approach**: Change `sets: parseInt(e.target.value) || ex.sets` to `sets: e.target.value` (store as raw string during editing, same as `reps` which already works as a string). Parse on save only. This is the minimal change consistent with existing patterns.

---

## Decision 5: AI Workout Scoring 100/100

**Finding**: The workout prompt (`prompt_builder.py` lines 67–111) does not specify muscle group coverage requirements. The quality scorer rewards: coverage (hitting all major muscle groups), volume (sufficient sets per group), balance (push/pull/legs balance), cardio, and frequency. A generic 5-day program often misses some groups (e.g., rear delts, calves) reducing the score.

**Decision**: Update `build_workout_prompt()` to explicitly require:
- All major muscle groups covered: chest, back, shoulders, biceps, triceps, quadriceps, hamstrings, glutes, calves, core
- 3–5 sets per muscle group per week minimum
- Include both push and pull movements each week
- Include at least 1 cardio session per week
- Include compound movements that hit multiple groups

**Rationale**: The scorer's `covered_groups` check and `weekly_sets_per_group` thresholds drive the score. By explicitly instructing the LLM to hit all groups with adequate volume, the generated plan will satisfy all scorer criteria.

---

## License Compliance Check

- Backend: One new endpoint (`DELETE /api/recommendations/diet/{id}`) — pure FastAPI/SQLAlchemy, no new packages.
- Frontend: No new npm packages.

**Constitution Principle III gate**: PASS.
