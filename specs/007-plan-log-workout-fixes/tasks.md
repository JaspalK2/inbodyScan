# Tasks: Plan Log and Workout Fixes (007)

**Feature**: 007-plan-log-workout-fixes  
**Branch**: `007-plan-log-workout-fixes`  
**Plan**: [plan.md](plan.md)

---

## Phase 1: Setup

- [X] T001 Confirm affected files exist and are readable (no new files to create)

---

## Phase 2: Backend Fixes

- [X] T002 [US3] Add `DELETE /api/recommendations/diet/{id}` endpoint in `services/recommendation-service/src/routers/recommendations.py` — mirror existing `DELETE /splits/{id}` pattern (scope to authenticated user, return 204 or 404)
- [X] T003 [US6] Update `build_workout_prompt()` in `services/recommendation-service/src/services/prompt_builder.py` — add explicit muscle group coverage requirements (chest, back upper+lower, shoulders front+side+rear, biceps, triceps, quads, hamstrings, glutes, calves, core; minimum 3 sets per group per week; compound movements; push+pull each week; 1 cardio session)

---

## Phase 3: Frontend — api.ts

- [X] T004 [P] [US3] Add `deleteDiet(id: string)` function to `frontend/lib/api.ts` — calls `DELETE /api/recommendations/diet/{id}`

---

## Phase 4: Frontend — page.tsx fixes

- [X] T005 [US1] Fix nested `<button>` in `WorkoutPlanCard` in `frontend/app/(app)/recommendations/page.tsx` — change outer expand/collapse `<button>` to `<div>` with `cursor-pointer` and `role="button"`
- [X] T006 [US4] Fix Sets field onChange in `WorkoutPlanCard` edit mode in `frontend/app/(app)/recommendations/page.tsx` — change `sets: parseInt(e.target.value) || ex.sets` to `sets: e.target.value`; change value prop to `String(ex.sets ?? "")`; on save parse with `parseInt(String(ex.sets)) || undefined`
- [X] T007 [US3] Add delete button to `DietPlanCard` in `frontend/app/(app)/recommendations/page.tsx` — Trash2 icon in card header, `window.confirm("Delete this diet plan? This cannot be undone.")`, call `deleteDiet(plan.id)` then `invalidateQueries(["diet-recs"])`; add `onDelete` prop to `DietPlanCard`; wire up in `DietTab`
- [X] T008 [US2] Replace flat saved meals list with two-section grouped layout in `FoodMealsTab` saved sub-tab in `frontend/app/(app)/recommendations/page.tsx` — Section 1 "Day Planner Meals": meals where `name.startsWith("Day Planner — ")` grouped by day number from description; Section 2 "My Meals": all other meals; hide empty sections; single empty state if both empty
- [X] T009 [US5] Verify `saveDayPlan()` in `DietDayRow` in `frontend/app/(app)/recommendations/page.tsx` populates `items_snapshot` with individual food items per entry — confirm entries array includes `items_snapshot: meal.foods.map(...)` and fix if missing

---

## Phase 5: Polish

- [ ] T010 Visual test Fix 1 (nested button): open http://localhost:3000/ → Workouts tab → expand a plan → confirm no console error about nested buttons
- [ ] T011 Visual test Fix 2 (diet delete): generate/view diet plans → click trash icon → confirm delete flow works
- [ ] T012 Visual test Fix 3 (sets editing): edit a workout plan → change sets from 3 to 8 → save → reload → confirm value persists
- [ ] T013 Visual test Fix 4 (saved meals grouping): save Day 1 + Day 2 → open Food & Meals → Saved Meals → confirm two sections with day sub-groups
- [ ] T014 Visual test Fix 5 (log this day): save a day plan → Day Planner tab → Log this day → food log shows individual items
- [ ] T015 Visual test Fix 6 (100/100 workout): generate new workout plan → confirm score is 100/100

---

## Dependencies

- T004 must complete before T007 (deleteDiet needed in DietPlanCard)
- T002 must complete before T004 (endpoint must exist before frontend calls it)
- T003 is independent (backend only, no frontend dependency)
- T005–T009 are independent of each other (different code sections in page.tsx)
- T010–T015 run after their respective implementation tasks

## Parallel Opportunities

- T003 and T004 can run in parallel (different files)
- T005, T006, T008, T009 can run in parallel (different components in page.tsx, no shared state)
- T010–T015 can run as a batch after all implementation tasks complete
