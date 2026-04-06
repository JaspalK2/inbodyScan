# Tasks: Plan Editing and Log Fixes

**Input**: Design documents from `/specs/005-plan-editing-fixes/`  
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Tests**: Mandatory per Constitution Principle IV (NON-NEGOTIABLE for this project).

**Organization**: Tasks grouped by user story. US1–US3 are P1 (frontend-only fixes). US4 is P2 (new backend endpoint + frontend exercise typeahead).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 / US2 / US3 / US4 per spec.md priorities

---

## Phase 1: Setup

**Purpose**: Download CC0 exercise dataset and verify test infrastructure. No new DB migrations.

- [X] T001 Download `yuhonas/free-exercise-db` CC0 JSON to `services/recommendation-service/src/data/exercises.json` by fetching `https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json` and saving it; add a comment in the file header noting license CC0 1.0 Universal
- [X] T002 [P] Verify `services/recommendation-service/tests/unit/` and `services/recommendation-service/tests/integration/` directories exist with `__init__.py`; create if missing

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend exercise search endpoint used by US4 but built first as infrastructure. Must complete before US4 frontend work.

- [X] T003 Add `ExerciseSearchResult` Pydantic schema to `services/recommendation-service/src/schemas/recommendation.py`: fields `name: str`, `primary_muscles: list[str]`, `secondary_muscles: list[str]`, `category: str`, `equipment: str`, `level: str`
- [X] T004 Create `services/recommendation-service/src/services/exercise_search.py`: load `src/data/exercises.json` once at module level into a Python list; implement `search_exercises(q: str, limit: int = 20) -> list[dict]` that does case-insensitive substring match on the `name` field and returns up to `limit` results mapped to `ExerciseSearchResult` shape
- [X] T005 Add `GET /api/recommendations/exercises/search` endpoint to `services/recommendation-service/src/routers/recommendations.py`: query param `q: str` (min length 2, raise 400 otherwise), `limit: int = 20`; call `search_exercises(q, limit)`; return `list[ExerciseSearchResult]`; require `get_current_user_id` dependency

**Checkpoint**: Exercise search endpoint available — US4 frontend work can proceed.

---

## Phase 3: User Story 1 — Save Individual Meals from Diet Plan (Priority: P1)

**Goal**: Add a "Save meal" button to every meal row in the diet plan (view mode and edit mode). Clicking it calls the existing `POST /api/recommendations/meals` to create a `CustomMeal` entry with the meal's foods and macros.

**Independent Test**: Open diet plan → expand Day 1 → click "Save meal" on Breakfast (view mode) → navigate to Food & Meals → Saved Meals tab → confirm the entry appears with correct name and macro summary.

### Tests for User Story 1

- [ ] T006 [P] [US1] Write unit test for the Save Meal mapping logic in `frontend/src/` (or co-located): given a `meal` object with `foods: string[]`, `calories`, `protein_g`, `carbs_g`, `fat_g`, assert that the `createMeal` payload has `name = "<meal.meal> meal"`, `items` array with one entry per food string with `food_name = food`, `quantity_g = 100`, and macro fields proportionally split — test in `frontend/app/(app)/recommendations/page.test.tsx` (create file if needed) or inline Jest test

### Implementation for User Story 1

- [X] T007 [US1] Add "Save meal" button to each meal row in `DietDayRow` inside `frontend/app/(app)/recommendations/page.tsx`: in the view-mode section of each meal (alongside the existing "Log" button), add a `Button` with `BookmarkPlus` icon labelled "Save"; on click, call `recommendations.createMeal({ name: \`\${meal.meal} meal\`, description: \`Saved from diet plan\`, items: meal.foods.map((f, i) => ({ food_name: f, quantity_g: 100, calories_kcal: meal._mf?.[i]?.c ?? (meal.calories / Math.max(meal.foods.length,1)), protein_g: meal._mf?.[i]?.p ?? (meal.protein_g / Math.max(meal.foods.length,1)), carbs_g: meal._mf?.[i]?.cb ?? (meal.carbs_g / Math.max(meal.foods.length,1)), fat_g: meal._mf?.[i]?.f ?? (meal.fat_g / Math.max(meal.foods.length,1)) })) })`; show a success toast / brief feedback on completion; also add the same button in edit mode (below the food list, above the search panel)
- [X] T008 [P] [US1] Invalidate `["custom-meals"]` query on successful meal save in T007 so that the Saved Meals tab refreshes automatically without a page reload

---

## Phase 4: User Story 2 — Saved Day Plans Visible in Saved Meals Tab (Priority: P1)

**Goal**: The Saved Meals sub-tab in `FoodMealsTab` currently only renders individual custom meals. Add a "Day Plans" section below that queries and renders saved day plans.

**Independent Test**: Save a day plan from the Diet tab → navigate to Food & Meals → Saved Meals tab → confirm a "Day Plans" section appears with the saved plan listed by name; expand it to confirm meal slots and food items are shown.

**Depends on**: None — fully independent frontend change using existing `listDayPlans()` API.

### Tests for User Story 2

- [ ] T009 [P] [US2] Write unit/render test for the Day Plans section in `frontend/app/(app)/recommendations/page.test.tsx`: mock `listDayPlans` returning one plan with two entries; assert the plan name renders and each meal slot is visible when expanded

### Implementation for User Story 2

- [X] T010 [US2] Add `useQuery({ queryKey: ["day-plans"], queryFn: recommendations.listDayPlans })` inside `FoodMealsTab` in `frontend/app/(app)/recommendations/page.tsx` (currently only `savedMeals` is queried in that tab)
- [X] T011 [US2] In the `saved` sub-tab render section of `FoodMealsTab` in `frontend/app/(app)/recommendations/page.tsx`, add a "Day Plans" section below the existing saved meals list: show a "No saved day plans yet" empty state when none exist; for each plan render a collapsible row showing plan name + date (if set); when expanded show each `DayPlanEntry` with its `meal_slot` and `items_snapshot` food names

---

## Phase 5: User Story 3 — Apply Saved Day Plan from Day Planner (Priority: P1)

**Goal**: In `DayPlannerTab`, add a "Use saved plan" button that opens a picker listing saved day plans. Selecting one batch-creates food log entries for the currently selected date from the plan's `items_snapshot`.

**Independent Test**: Navigate to Day Planner → select today → click "Use saved plan" → pick a saved plan → confirm food log entries for today are populated with the plan's meals and macros.

**Depends on**: T010 (day plans query) is helpful but not blocking — US3 can add its own `listDayPlans` call independently.

### Tests for User Story 3

- [ ] T012 [P] [US3] Write unit test for the day-plan-to-food-log mapping: given a `DayPlanOut` with two entries each having `items_snapshot`, assert that the resulting `FoodLogBatchCreate.entries` array has the correct `food_name`, `quantity_g`, `calories_kcal`, `source = "day_plan"`, `source_ref_id = plan.id` fields — test in `frontend/app/(app)/recommendations/page.test.tsx`

### Implementation for User Story 3

- [X] T013 [US3] Add `useQuery({ queryKey: ["day-plans"], queryFn: recommendations.listDayPlans })` inside `DayPlannerTab` in `frontend/app/(app)/recommendations/page.tsx` if not already present
- [X] T014 [US3] Add a "Use saved plan" button to the `DayPlannerTab` header area in `frontend/app/(app)/recommendations/page.tsx`: clicking it toggles a picker panel showing the list of saved day plans (or an empty state "No saved day plans yet — save a day plan from the Diet tab"); each plan shows its name and entry count
- [X] T015 [US3] On selecting a plan in the picker, call `recommendations.createFoodLog({ log_date: selectedDate, entries: plan.entries.flatMap(entry => (entry.items_snapshot ?? []).map(item => ({ food_name: item.food_name, quantity_g: item.quantity_g ?? 100, calories_kcal: item.calories_kcal ?? null, protein_g: item.protein_g ?? null, carbs_g: item.carbs_g ?? null, fat_g: item.fat_g ?? null, source: "day_plan", source_ref_id: plan.id }))) })` in `frontend/app/(app)/recommendations/page.tsx`; on success invalidate `["food-log", selectedDate]` and close the picker; show success feedback ("Plan applied to food log")

---

## Phase 6: User Story 4 — Exercise Typeahead in Workout Plan Editor (Priority: P2)

**Goal**: In the workout plan edit mode, replace the free-text exercise name input with an inline typeahead that searches the CC0 exercise dataset via the new `GET /exercises/search` endpoint. Selecting an exercise updates the plan and triggers the existing live score recalculation.

**Independent Test**: Open workout plan → Edit → click exercise name → type "squat" → dropdown appears with matching exercises → select one → score updates within 1 s → Save → reload → change persists.

**Depends on**: T003–T005 (exercise search endpoint) must be complete before frontend can call it.

### Tests for User Story 4

- [X] T016 [P] [US4] Write unit test for `search_exercises()` in `services/recommendation-service/tests/unit/test_exercise_search.py`: assert that searching "bench" returns results containing "Bench Press"; assert case-insensitive match; assert empty list for "zzzzxxx"; assert limit is respected
- [X] T017 [P] [US4] Write integration test for `GET /api/recommendations/exercises/search?q=squat` in `services/recommendation-service/tests/integration/test_exercises_endpoint.py`: assert 200 with non-empty list of `ExerciseSearchResult`-shaped objects; assert 400 when `q` is 1 character; assert 401 without auth token
- [X] T018 [P] [US4] Add `searchExercises: (q: string, limit?: number) => request<ExerciseSearchResult[]>("recommendation", \`/api/recommendations/exercises/search?q=\${encodeURIComponent(q)}&limit=\${limit ?? 20}\`)` to `frontend/lib/api.ts`; add `ExerciseSearchResult` interface: `{ name: string; primary_muscles: string[]; secondary_muscles: string[]; category: string; equipment: string; level: string }`

### Implementation for User Story 4

- [X] T019 [US4] In the workout plan edit mode inside `frontend/app/(app)/recommendations/page.tsx`, find the exercise name field (the `<input>` or text element showing `exercise.name` in the weekly/daily exercise table) and replace it with an inline typeahead: when in edit mode the name field renders as a text input; on input (debounced 300 ms, min 2 chars) call `recommendations.searchExercises(q)`; render a dropdown list of results showing `name` + `primary_muscles[0]`; selecting a result calls the existing exercise update handler with the new name; show "No exercises found" when results are empty; show error state when the API call fails
- [X] T020 [US4] Wire the exercise name change (from the typeahead in T019) into the existing live score debounce in `frontend/app/(app)/recommendations/page.tsx`: after updating the exercise name in the plan state, the existing `POST /workout/score-plan` debounce (already implemented) picks up the changed plan and recalculates the score — verify the wiring is correct and no extra debounce is added

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T021 [P] Run all backend tests: `cd services/recommendation-service && python -m pytest tests/ -v` — all tests must pass
- [ ] T022 [P] Validate quickstart scenarios 1–6 from `specs/005-plan-editing-fixes/quickstart.md` manually against local stack
- [ ] T023 [P] Verify all new UI elements use existing design token classes only (purple-400, cyan-300, amber-300, green-400 etc.) and existing `Button`, `BookmarkPlus`, `ChevronDown`/`ChevronUp`, `Loader2` components — no inline colours or reimplemented primitives

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (exercises.json must exist before T004 loads it)
- **US1 (Phase 3)**: No backend dependency — fully frontend, start after Phase 1
- **US2 (Phase 4)**: No dependencies — fully frontend, start immediately
- **US3 (Phase 5)**: No dependencies — fully frontend, start immediately
- **US4 (Phase 6)**: Depends on Phase 2 (T003–T005 must be complete before T019 can call the endpoint)
- **Polish (Phase 7)**: Depends on all prior phases

### User Story Dependencies

- US1, US2, US3 are fully independent of each other and of US4 — all can run in parallel after Phase 1
- US4 backend (T016–T018) can run in parallel with US1/US2/US3
- US4 frontend (T019–T020) depends on T003–T005 (endpoint) and T018 (API client)

### Parallel Opportunities

- T001 + T002 can run in parallel (different targets)
- T003, T004, T005 must be sequential (T004 uses schema from T003; T005 uses service from T004)
- T006, T009, T012, T016, T017, T018 can all run in parallel (different test files)
- T007 + T008 are sequential (T008 adds invalidation to T007's mutation)
- T010 + T011 are sequential (T011 renders data from T010's query)
- T013 + T014 + T015 are sequential within US3
- T019 + T020 are sequential within US4 frontend
- T021 + T022 + T023 can all run in parallel

---

## Implementation Strategy

### MVP: US1 + US2 + US3 (all P1, no backend work)

1. Complete Phase 1: Setup (T001–T002)
2. Complete US1 (T006–T008): Save meal button
3. Complete US2 (T009–T011): Day plans in Saved Meals tab
4. Complete US3 (T012–T015): Apply day plan from Day Planner
5. **STOP and VALIDATE**: Run quickstart scenarios 1–4

### Incremental Delivery

1. Setup → ready for all stories
2. US1 → save meal from diet plan
3. US2 → day plans visible in Saved Meals
4. US3 → apply saved plan to food log (completes the P1 MVP)
5. Foundational (Phase 2) + US4 → exercise search and workout editing
6. Polish → full suite green

---

## Notes

- No DB migrations required — all existing models used as-is
- Exercise dataset (CC0) must be committed to the repo alongside the service code
- `_mf` (per-food macro tracking) is already in-memory state from the previous feature; US1 uses it for proportional macro splitting when saving
- The existing `POST /workout/score-plan` debounce in the workout editor already handles live score updates — T020 only needs to verify the wiring, not re-implement it
- Constitution Principle IV: all test tasks are mandatory; do not skip
