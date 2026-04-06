# Tasks: Fix Dietary Restriction Enforcement & Redesign Diet Plan Saved Meals UX

**Input**: Design documents from `/specs/018-diet-restrictions-plan-ux/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Organization**: US1 (data fix + tests — P0 safety) and US2 (auto-save + UI redesign — P1) are independent. US1 is backend-only; US2 is frontend-only. No shared files. Both can proceed in parallel after Phase 1 read.

---

## Phase 1: Setup

**Purpose**: Confirm the state of the two affected files before writing.

- [X] T001 Read `services/recommendation-service/src/data/foods.json` — confirm the 6 incorrectly-flagged entries (Chicken thighs, ON THE BORDER ground beef taco, Fish oil salmon, Snacks shrimp cracker, APPLEBEE'S Double Crunch Shrimp, DENNY'S golden fried shrimp all have `vegetarian: true`) — no code changes yet
- [X] T002 Read `frontend/app/(app)/recommendations/page.tsx` lines 350–800 — confirm location of `generateDietMutation` (around line 369), `DietDayRow` component, the "Save day" `<Button>`, and `FoodMealsTab` saved plans section — no code changes yet

---

## Phase 2: Foundational

No shared blocking prerequisites. Both user stories are fully independent (different files, different languages). Phase 1 reads are the only prerequisite.

**Checkpoint**: Phase 1 reads complete → US1 and US2 can proceed in parallel.

---

## Phase 3: User Story 1 — Dietary Restrictions Enforced During Plan Generation (Priority: P0) 🎯 MVP

**Goal**: Fix the 6 incorrect restriction flags in `foods.json` so vegetarian/vegan users never receive meat or fish items in generated plans.

**Independent Test**: Run `pytest services/recommendation-service/tests/test_diet_restrictions.py -v` — all parametrized restriction tests pass. Confirm zero non-vegetarian items appear when `restrictions=["vegetarian"]`.

### Tests for User Story 1

- [X] T003 [US1] In `services/recommendation-service/tests/test_diet_restrictions.py` (new file), write `test_vegetarian_plan_contains_no_meat_or_fish`: generate a plan with `restrictions=["vegetarian"]`; assert no item's `food_name` matches any of the known non-vegetarian names in `foods.json` (check against a hardcoded list: `"Chicken"`, `"chicken"`, `"beef"`, `"Beef"`, `"shrimp"`, `"Shrimp"`, `"salmon"`, `"Salmon"`, `"tuna"`, `"Tuna"`, `"tilapia"`, `"Tilapia"`, `"Fish"`, `"pork"`, `"Pork"`, `"turkey"`, `"Turkey"`, `"lamb"`, `"Lamb"`) — this test MUST FAIL before T004 is applied
- [X] T004 [P] [US1] In `services/recommendation-service/tests/test_diet_restrictions.py`, add `test_vegan_plan_contains_no_animal_products`: generate with `restrictions=["vegan"]`; assert zero items with any meat/fish name (same list as T003) appear
- [X] T005 [P] [US1] In `services/recommendation-service/tests/test_diet_restrictions.py`, add `test_multiple_restrictions_satisfied`: generate with `restrictions=["vegetarian", "gluten_free"]`; assert the plan generates without error and has 7 days
- [X] T006 [P] [US1] In `services/recommendation-service/tests/test_diet_restrictions.py`, add `test_no_restrictions_generates_normally`: generate with `restrictions=[]`; assert 7 days with ≥1 item per day across all meal slots that have available foods

**Checkpoint**: Tests T003–T006 exist and T003 FAILS (confirming the bug) → ready to fix

### Implementation for User Story 1

- [X] T007 [US1] In `services/recommendation-service/src/data/foods.json`, find the entry `"Chicken, thighs, frozen, breaded, reheated"` and change its `restrictions.vegetarian` from `true` to `false` and `restrictions.vegan` from `true` to `false`
- [X] T008 [US1] In `services/recommendation-service/src/data/foods.json`, find the entry `"ON THE BORDER, soft taco with ground beef, cheese and lettuce"` and change `restrictions.vegetarian` and `restrictions.vegan` from `true` to `false`
- [X] T009 [US1] In `services/recommendation-service/src/data/foods.json`, find the entry `"Fish oil, salmon"` and change `restrictions.vegetarian` and `restrictions.vegan` from `true` to `false`
- [X] T010 [US1] In `services/recommendation-service/src/data/foods.json`, find the entry `"Snacks, shrimp cracker"` and change `restrictions.vegetarian` and `restrictions.vegan` from `true` to `false`
- [X] T011 [US1] In `services/recommendation-service/src/data/foods.json`, find the entry `"APPLEBEE'S, Double Crunch Shrimp"` and change `restrictions.vegetarian` and `restrictions.vegan` from `true` to `false`
- [X] T012 [US1] In `services/recommendation-service/src/data/foods.json`, find the entry `"DENNY'S, golden fried shrimp"` and change `restrictions.vegetarian` and `restrictions.vegan` from `true` to `false`
- [X] T013 [US1] Run `pytest services/recommendation-service/tests/test_diet_restrictions.py services/recommendation-service/tests/test_diet_engine.py -v` to confirm all restriction tests now pass and all existing diet engine tests still pass

**Checkpoint**: US1 complete — vegetarian/vegan restrictions enforced, all tests pass.

---

## Phase 4: User Story 2 — Auto-Save Generated Plans & Redesigned Saved Plans Display (Priority: P1)

**Goal**: Remove the manual "Save day" button; auto-save all 7 days on generation; redesign the saved plans section to show date-stamped plan blocks grouped by recommendation ID, each expandable to day rows and meal macros.

**Independent Test**: Generate a diet plan in the UI → navigate to Food & Meals → My Saved Meals → a new date-stamped plan block appears containing 7 day rows → expand a day → meal macros visible. No "Save day" button anywhere in the diet tab.

### Tests for User Story 2

- [X] T014 [US2] In `frontend/__tests__/recommendations/autoSavePlan.test.ts` (new file), write `auto-saves 7 day plans on successful generation`: mock `recommendations.generateDiet` returning a rec with `id="test-rec-id"` and 7 days each with 4 meals; mock `recommendations.createDayPlan`; assert `createDayPlan` is called exactly 7 times, each call has `notes: "test-rec-id"`, and `["day-plans"]` query is invalidated — this test MUST FAIL before T016 is applied
- [X] T015 [P] [US2] In `frontend/__tests__/recommendations/autoSavePlan.test.ts`, add `does not auto-save if generation fails`: mock `generateDiet` throwing an error; assert `createDayPlan` is never called
- [X] T016 [P] [US2] In `frontend/__tests__/recommendations/autoSavePlan.test.ts`, add `groups day plans by notes field in UI`: render the saved plans section with mock `dayPlans` where 7 entries share `notes: "rec-1"` and 7 entries share `notes: "rec-2"`; assert exactly 2 plan block headers are rendered

**Checkpoint**: Tests T014–T016 exist and T014 FAILS → ready to implement

### Implementation for User Story 2

- [X] T017 [US2] In `frontend/app/(app)/recommendations/page.tsx`, remove the `saveDayPlan` async function from the `DietDayRow` component (approximately lines 710–755) and all associated state: `saveError`, `saveSuccess`, `saveSuccessTimerRef` — do NOT yet remove the button from JSX
- [X] T018 [US2] In `frontend/app/(app)/recommendations/page.tsx`, remove the "Save day" `<Button>` element and its surrounding `<div>` from `DietDayRow`'s JSX (approximately lines 765–768); also remove the inline success/error `<p>` messages below it
- [X] T019 [US2] In `frontend/app/(app)/recommendations/page.tsx`, in the `generateDietMutation` definition (around line 369), add an `onSuccess: async (rec) => { ... }` callback that: (a) iterates `rec.structured_plan.days` (7 items), (b) for each `day`, calls `await recommendations.createDayPlan({ name: \`AI Plan ${dateStr} (Day ${day.day})\`, plan_date: todayISO, notes: rec.id, entries: day.meals.map(meal => ({ meal_slot: meal.meal_name.toLowerCase(), custom_meal_name: meal.meal_name, calories_kcal: meal.meal_totals.calories, protein_g: meal.meal_totals.protein_g, carbs_g: meal.meal_totals.carbs_g, fat_g: meal.meal_totals.fat_g, fiber_g: meal.meal_totals.fiber_g ?? 0, items_snapshot: meal.items })) })`, (c) after all 7 saves, calls `queryClient.invalidateQueries({ queryKey: ["day-plans"] })`
- [X] T020 [US2] In `frontend/app/(app)/recommendations/page.tsx`, inside `FoodMealsTab`, replace the current flat "Saved Day Plans" card list (approximately lines 1154–1161) with a grouped view: (a) group `dayPlans` by `notes` field using `Object.groupBy` or `reduce`, (b) sort groups by the `created_at` of the first entry newest-first, (c) for each group render a collapsible plan block with header showing the formatted `created_at` date and a delete-all button; the block when expanded shows the 7 day entries sorted by day number extracted from the `name` field (e.g. `"AI Plan 2026-04-06 (Day 3)"` → day 3)
- [X] T021 [US2] In `frontend/app/(app)/recommendations/page.tsx`, inside the expanded plan block for each day entry, render a nested collapsible row showing the day's 4 meal entries from `entries` (meal slot name + `calories_kcal`, `protein_g`, `carbs_g`, `fat_g`) and an inner collapsible for `items_snapshot` listing individual food items with their gram weights
- [X] T022 [US2] In `frontend/app/(app)/recommendations/page.tsx`, implement the delete-all handler for a plan block: given a group of 7 day plans sharing the same `notes` value, call `recommendations.deleteDayPlan(id)` for each of the 7 IDs in sequence, then invalidate `["day-plans"]` query; wire the trash icon button on each plan block header to this handler
- [X] T023 [US2] Run `npx vitest run frontend/__tests__/recommendations/autoSavePlan.test.ts` to confirm all 3 auto-save tests now pass

**Checkpoint**: US2 complete — auto-save on generation works, saved plans section shows grouped date-stamped plan blocks with nested day/meal/macro detail.

---

## Phase 5: Polish & Validation

- [X] T024 Run `pytest services/recommendation-service/tests/ -v` to confirm all backend tests pass (US1 regression check)
- [X] T025 [P] Run `npx vitest run frontend/__tests__/` to confirm all frontend tests pass (US2 regression check)
- [X] T026 Perform the quickstart.md Scenario 1 validation: set profile restriction to "vegetarian", generate a plan, confirm zero shrimp/salmon/chicken items appear in any of the 7 days
- [X] T027 [P] Perform the quickstart.md Scenario 4 validation: generate a plan, navigate to Food & Meals → My Saved Meals, confirm new date-stamped plan block appears with 7 expandable day rows

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately; T001 and T002 can run in parallel
- **Foundational (Phase 2)**: No foundational work needed; US1 and US3 are fully independent
- **US1 (Phase 3)**: Depends on T001 (foods.json read). T003 → T004/T005/T006 (parallel) → T007–T012 (sequential, same file) → T013
- **US2 (Phase 4)**: Depends on T002 (page.tsx read). T014 → T015/T016 (parallel) → T017 → T018 → T019 → T020 → T021 → T022 → T023
- **Polish (Phase 5)**: Depends on T013 (US1 complete) and T023 (US2 complete)

### User Story Dependencies

- **US1 and US2 are fully independent** — different files, different languages; can run in parallel after Phase 1

### Within US1

- T003 must come first (failing test must exist before fix)
- T004, T005, T006 can parallel with T003 (same new file, different test functions — run sequentially if single developer)
- T007–T012 must run sequentially (all edits to foods.json)
- T013 validates T007–T012

### Within US2

- T014 first (failing test)
- T015, T016 parallel with T014
- T017 → T018 sequential (same component, remove state before removing JSX)
- T019 independent of T017/T018 (different section of same file — sequential in practice)
- T020 → T021 → T022 sequential (same FoodMealsTab section, layered)
- T023 validates T019–T022

---

## Parallel Opportunities

```bash
# Phase 1 — parallel:
Task A: T001 Read foods.json
Task B: T002 Read page.tsx

# After Phase 1 — US1 and US2 fully parallel:
Stream A (US1): T003 → T004/T005/T006 → T007...T012 → T013
Stream B (US2): T014 → T015/T016 → T017 → T018 → T019 → T020 → T021 → T022 → T023

# Phase 5 — parallel (after both streams complete):
Task A: T024 + T026 (backend)
Task B: T025 + T027 (frontend)
```

---

## Implementation Strategy

### MVP (US1 only — P0 safety fix)

1. T001: Read foods.json
2. T003: Write failing test
3. T007–T012: Fix 6 data entries
4. T013: Confirm all tests pass
5. **STOP and VALIDATE**: vegetarian plan generation verified clean

### Full Delivery

Add US2 tasks T002, T014–T023 for auto-save + UI redesign, then T024–T027 for final validation.

---

## Notes

- T007–T012 are all edits to the same `foods.json` file — apply them sequentially in one editing pass to avoid file conflicts
- T019 builds the auto-save logic; it must correctly handle the `rec.structured_plan` shape (`days[].meals[].meal_totals` and `days[].meals[].items`)
- The `notes` field in `DayPlanCreate` is already a `str | None` in the schema — no schema change needed to store the rec ID
- T020 grouping: use `Array.reduce` to group `dayPlans` by `d.notes`; entries with `notes: null` (manually saved plans) can be shown in a separate "Manual saves" group or at the bottom
- T022 delete-all: use `Promise.all` or sequential awaits for the 7 deletions; invalidate cache once after all complete
