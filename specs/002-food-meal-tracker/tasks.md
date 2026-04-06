---
description: "Task list for Food & Meal Tracker Enhancements"
---

# Tasks: Food & Meal Tracker Enhancements

**Input**: Design documents from `/specs/002-food-meal-tracker/`
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅

**Note**: Per project constitution Principle IV (Mandatory Test Coverage), test tasks are REQUIRED for this project. All user story phases include test tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Exact file paths included in all task descriptions

## Path Conventions

- Backend service: `services/recommendation-service/src/`
- Frontend: `frontend/app/(app)/recommendations/` and `frontend/lib/`
- Shared Python: `shared/python/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database table creation and import wiring. No new project structure needed — this feature extends an existing service.

- [X] T001 Create `daily_food_log_entries` table in Supabase by running the SQL from `specs/002-food-meal-tracker/quickstart.md` (CREATE TABLE + two indexes)
- [X] T002 [P] Create `DailyFoodLogEntry` SQLAlchemy model (all columns from data-model.md: id, user_id, log_date, fdc_id, food_name, brand, source, source_ref_id, quantity_g, macro columns, created_at) in `services/recommendation-service/src/models/food_log.py`
- [X] T003 [P] Add `food_log` model import to `services/recommendation-service/src/main.py` alongside existing model imports so SQLAlchemy metadata is populated

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend service and schema for food log — required before ALL user story implementations.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Add `FoodLogEntryIn`, `FoodLogBatchCreate`, and `FoodLogEntryOut` Pydantic schemas to `services/recommendation-service/src/schemas/recommendation.py` (fields: fdc_id nullable int, food_name str, brand nullable str, source str default "manual", source_ref_id nullable str, quantity_g float, calories_kcal/protein_g/carbs_g/fat_g/fiber_g all nullable float; Out adds id, user_id, log_date date, created_at datetime)
- [X] T005 Implement `FoodLogService` with four functions in `services/recommendation-service/src/services/food_log_service.py`: `create_log_entries(session, user_id, log_date, entries)`, `get_entries_for_date(session, user_id, log_date)`, `delete_entry(session, entry_id, user_id)`, `get_logged_dates(session, user_id)` — all queries MUST filter by `user_id`
- [X] T006 Add four food-log endpoints to `services/recommendation-service/src/routers/recommendations.py`: `POST /api/recommendations/food-log` (batch create, 201), `GET /api/recommendations/food-log?date=YYYY-MM-DD` (200 or []), `DELETE /api/recommendations/food-log/{entry_id}` (204), `GET /api/recommendations/food-log/dates` (200 list of ISO date strings) — all use `get_current_user_id` dependency
- [X] T007 [P] Add food log API client functions to `frontend/lib/api.ts`: `createFoodLog(data: FoodLogBatchCreate)`, `getFoodLog(date: string)`, `deleteFoodLogEntry(id: string)`, `getFoodLogDates()` — using existing `request()` helper pointing to `"recommendation"` service
- [X] T008 [P] Add TypeScript types to `frontend/lib/api.ts`: `FoodLogEntryIn`, `FoodLogEntryOut`, `FoodLogBatchCreate` matching the Pydantic schemas

**Checkpoint**: Foundation ready — `POST /api/recommendations/food-log` accepts entries, `GET` returns them for a date, `DELETE` removes one. Verify with curl before proceeding.

---

## Phase 3: User Story 1 — Daily Food Log with Macro Pie Chart (Priority: P1) 🎯 MVP

**Goal**: Users can add food items to a daily log and see a live macro pie chart update on the Food & Meals tab.

**Independent Test**: Search for "chicken breast," add 200 g → item appears in today's food log → pie chart updates. Remove the item → pie chart recalculates. No saved meals or AI plans needed.

### Tests for User Story 1 ⚠️ Write and verify these FAIL before implementing

- [ ] T009 [P] [US1] Integration test: `POST /api/recommendations/food-log` with valid entries returns 201 and correct response shape in `services/recommendation-service/tests/integration/test_food_log.py`
- [ ] T010 [P] [US1] Integration test: `GET /api/recommendations/food-log?date=2026-04-02` returns only entries for that date and user in `services/recommendation-service/tests/integration/test_food_log.py`
- [ ] T011 [P] [US1] Integration test: `DELETE /api/recommendations/food-log/{id}` removes entry; re-fetching returns empty for that date in `services/recommendation-service/tests/integration/test_food_log.py`
- [ ] T012 [P] [US1] Integration test: `GET /api/recommendations/food-log?date=X` for a different user does NOT return the first user's entries (data isolation check) in `services/recommendation-service/tests/integration/test_food_log.py`
- [ ] T013 [P] [US1] Unit test: `FoodLogService.get_entries_for_date()` returns entries sorted by `created_at` ascending in `services/recommendation-service/tests/unit/test_food_log_service.py`
- [ ] T014 [P] [US1] E2E test: add food item via search → confirm it appears in food log panel and pie chart reflects macros in `frontend/tests/e2e/test_food_log.spec.ts`

### Implementation for User Story 1

- [X] T015 [US1] Add a "Food Log" panel to the Food & Meals tab in `frontend/app/(app)/recommendations/page.tsx`: a date picker (defaulting to today) above a list of `FoodLogEntryOut` items (food name, brand badge if present, quantity g, calories, protein/carbs/fat g, delete button per row); use `useQuery({ queryKey: ["food-log", selectedDate], queryFn: () => recommendations.getFoodLog(selectedDate) })`
- [X] T016 [P] [US1] Add macro pie chart component inline in the Food & Meals tab of `frontend/app/(app)/recommendations/page.tsx`: Recharts `PieChart` with three slices (protein purple `#A855F7`, carbs cyan `#06B6D4`, fat amber `#F59E0B`); slice size = `Math.min(consumed / target, 1)` of 360°; overflow (consumed > target) fills the slice in red `#EF4444`; if no targets, show absolute gram totals with "Complete your profile for target-relative display" note
- [X] T017 [US1] Wire "Add to Today" button on food search result cards in `frontend/app/(app)/recommendations/page.tsx` to call `recommendations.createFoodLog({ log_date: selectedDate, entries: [{ fdc_id, food_name, brand, source: "manual", quantity_g, ...scaledMacros }] })`, then `queryClient.invalidateQueries(["food-log", selectedDate])` to refresh log and pie chart
- [X] T018 [US1] Wire delete button on each food log row to call `recommendations.deleteFoodLogEntry(id)` then invalidate `["food-log", selectedDate]` query in `frontend/app/(app)/recommendations/page.tsx`

**Checkpoint**: US1 fully functional — search, add, log panel, pie chart, and delete all work independently.

---

## Phase 4: User Story 2 — Restaurant Meal Search (Priority: P1)

**Goal**: Restaurant/branded items appear in food search results with a source label.

**Independent Test**: Search "Big Mac" → at least one result with `brand = "McDonald's"` (or similar) returned and labelled. Add it → logs correctly with brand shown in the log panel.

### Tests for User Story 2 ⚠️ Write and verify these FAIL before implementing

- [ ] T019 [P] [US2] Integration test: `GET /api/recommendations/food/search?q=Big+Mac` returns at least one result with a non-null `brand` field in `services/recommendation-service/tests/integration/test_food_search.py`
- [ ] T020 [P] [US2] Unit test: `_build_food_result()` in `food_search.py` maps `brandOwner` and `brandName` USDA fields to `brand` field correctly in `services/recommendation-service/tests/unit/test_food_search.py`
- [ ] T021 [P] [US2] E2E test: search "Starbucks" → confirm branded result appears with restaurant label badge in `frontend/tests/e2e/test_food_log.spec.ts`

### Implementation for User Story 2

- [X] T022 [US2] Add brand source label badge to food search result cards in `frontend/app/(app)/recommendations/page.tsx`: if `result.brand` is non-null, render a small badge (e.g., shadcn `Badge` variant `secondary`) showing the brand name next to the food name; if null, no badge (generic ingredient)
- [X] T023 [US2] Ensure `brand` is included in the `FoodResultOut` schema response and passed through to the `createFoodLog` call when adding a restaurant item in `frontend/app/(app)/recommendations/page.tsx` (the `brand` field already exists on `FoodResult` dataclass — verify it is included in `FoodResultOut` schema in `services/recommendation-service/src/schemas/recommendation.py`)

**Checkpoint**: US2 functional — restaurant items labelled in search results and brand shown in food log panel.

---

## Phase 5: User Story 3 — Saved Food Shortcuts (Priority: P2)

**Goal**: Saved custom meals appear with a one-tap "Add to Today" shortcut that logs all meal items at once.

**Independent Test**: Save a custom meal → "Saved" shortcuts section shows it with "Add to Today" → tap button → all meal items appear in today's food log and pie chart updates. Requires US1 complete.

### Tests for User Story 3 ⚠️ Write and verify these FAIL before implementing

- [ ] T024 [P] [US3] Integration test: `POST /api/recommendations/food-log` with `source=saved_meal` and `source_ref_id=<meal_id>` creates entries correctly in `services/recommendation-service/tests/integration/test_food_log.py`
- [ ] T025 [P] [US3] E2E test: saved meal shortcut "Add to Today" logs all meal items and pie chart updates in `frontend/tests/e2e/test_food_log.spec.ts`

### Implementation for User Story 3

- [X] T026 [US3] Add a "Saved Meals" shortcuts section to the Food & Meals tab in `frontend/app/(app)/recommendations/page.tsx`: query `["custom-meals"]` (already available) and render each meal as a card with name, total macro summary, and an "Add to Today" button; show an empty state ("Save a meal from search results to see shortcuts here") if no saved meals exist
- [X] T027 [US3] Wire the saved meal "Add to Today" button in `frontend/app/(app)/recommendations/page.tsx` to call `recommendations.createFoodLog({ log_date: selectedDate, entries: meal.items.map(item => ({ fdc_id: item.fdc_id, food_name: item.food_name, source: "saved_meal", source_ref_id: meal.id, quantity_g: item.quantity_g, ...item macros })) })` then invalidate `["food-log", selectedDate]`

**Checkpoint**: US3 functional — saved meals shortcut section works and adds all items to the log in one action.

---

## Phase 6: User Story 4 — Editable AI Diet Plan with Live Macro Impact (Priority: P2)

**Goal**: Each generated diet plan meal has a "Log this meal" button. Editing quantity shows a live inline macro preview. Only after logging does the pie chart update.

**Independent Test**: Generate a diet plan → change a meal's quantity → inline macro preview updates instantly → tap "Log this meal" → pie chart updates with the edited quantity. Requires US1 complete.

### Tests for User Story 4 ⚠️ Write and verify these FAIL before implementing

- [ ] T028 [P] [US4] Integration test: `POST /api/recommendations/food-log` with `source=diet_plan` and `source_ref_id=<rec_id>` creates entries correctly in `services/recommendation-service/tests/integration/test_food_log.py`
- [ ] T029 [P] [US4] Unit test (Vitest): editing a meal quantity in diet plan edit mode recalculates inline macro preview without calling any API in `frontend/tests/unit/dietPlanEdit.test.ts`
- [ ] T030 [P] [US4] E2E test: generate diet plan → log one meal → pie chart updates → revert plan → previously logged entry is NOT removed from log in `frontend/tests/e2e/test_diet_plan.spec.ts`

### Implementation for User Story 4

- [X] T031 [US4] Add "Log this meal" button to each meal card in the Diet tab's generated plan accordion in `frontend/app/(app)/recommendations/page.tsx`: button calls `recommendations.createFoodLog({ log_date: selectedDate, entries: parsedMealItems.map(item => ({ food_name: item.name, source: "diet_plan", source_ref_id: rec.id, quantity_g: item.quantity_g, ...computedMacros })) })` then invalidates `["food-log", selectedDate]`
- [ ] T032 [US4] Add inline macro preview to diet plan meal edit mode in `frontend/app/(app)/recommendations/page.tsx`: when the user changes a quantity input in edit mode, compute `scaledMacros = { protein_g: baseProtein * (newQty / baseQty), ... }` client-side and display immediately below the input — no API call, pure multiplication
- [ ] T033 [US4] Add "Already logged" indicator on diet plan meal cards in `frontend/app/(app)/recommendations/page.tsx`: check if any `food-log` entries for `selectedDate` have `source_ref_id === rec.id` — if so, show a checkmark or "Logged" badge on that meal card
- [ ] T034 [US4] Ensure "Revert to Original" action on diet plan in `frontend/app/(app)/recommendations/page.tsx` does NOT remove any food-log entries — only resets the `editedWorkout` / `editedDiet` local state and calls the existing `PATCH /api/recommendations/diet/{id}` revert; add a comment clarifying this behavior

**Checkpoint**: US4 functional — "Log this meal" works, inline macro preview updates live, pie chart only changes on explicit log action.

---

## Phase 7: User Story 5 — Editable AI Workout Plan with Live Quality Score (Priority: P2)

**Goal**: Editing any exercise in the generated workout plan immediately recalculates and displays the updated workout quality score.

**Independent Test**: Generate a workout plan → remove all cardio exercises → quality score's cardio sub-score drops immediately without page reload → save → score persists.

### Tests for User Story 5 ⚠️ Write and verify these FAIL before implementing

- [ ] T035 [P] [US5] Unit test (Vitest): removing all cardio exercises from a parsed workout plan and passing to `scoreSplit()` returns a lower cardio sub-score than the unmodified plan in `frontend/tests/unit/workoutPlanEdit.test.ts`
- [ ] T036 [P] [US5] E2E test: generate workout plan → remove one exercise → quality score updates within 1 second → save → log out + log in → edited plan and score still shown in `frontend/tests/e2e/test_workout_plan.spec.ts`

### Implementation for User Story 5

- [X] T037 [US5] Add live workout quality score preview to the workout plan edit mode in `frontend/app/(app)/recommendations/page.tsx`: when the user edits any exercise in `editedWorkout` state (add/remove/change), call `recommendations.scoreSplit({ name: "preview", days: parsedDays })` debounced at 300ms and display the returned `WorkoutScore` (overall score + sub-scores + feedback list) in a panel beside or below the plan — reuse the same `WorkoutScoreOut` display component already used in the split builder
- [ ] T038 [US5] Ensure the workout plan edit save button calls the existing `PATCH /api/recommendations/workout/{id}` endpoint with `{ edited_plan: editedWorkout }` and the displayed quality score updates to reflect the saved state in `frontend/app/(app)/recommendations/page.tsx`
- [ ] T039 [US5] Add "Revert to Original" button to the workout plan edit mode in `frontend/app/(app)/recommendations/page.tsx`: resets `editedWorkout` to `null`, calls `PATCH /api/recommendations/workout/{id}` with `{ edited_plan: null }` to clear the server-side override, and re-scores the original plan

**Checkpoint**: US5 functional — all 5 user stories independently working.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: UI consistency, error states, and quickstart validation.

- [ ] T040 [P] Add loading skeleton to food log panel while `getFoodLog` query is in loading state in `frontend/app/(app)/recommendations/page.tsx` using shadcn `Skeleton` component
- [ ] T041 [P] Add error toast when `createFoodLog` mutation fails (e.g., network error) in `frontend/app/(app)/recommendations/page.tsx` using existing toast pattern
- [ ] T042 [P] Add empty state to food log panel ("Nothing logged for this day yet — search for foods above and tap Add to Today") when log is empty for selected date in `frontend/app/(app)/recommendations/page.tsx`
- [ ] T043 [P] Add `GET /api/recommendations/food-log/dates` integration test confirming it returns only dates for the authenticated user and never for other users in `services/recommendation-service/tests/integration/test_food_log.py`
- [ ] T044 Run all 9 quickstart.md validation scenarios against the locally running stack and fix any failures before marking this feature complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately; T002 and T003 can run in parallel
- **Foundational (Phase 2)**: Depends on Phase 1 (model must exist before service/endpoints) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — MVP; can start once Foundational is complete
- **US2 (Phase 4)**: Depends on Foundational only; can run in parallel with US1 (different concern: label display)
- **US3 (Phase 5)**: Depends on US1 (food log must exist to add shortcuts to)
- **US4 (Phase 6)**: Depends on US1 (pie chart must exist for "log this meal" to update it)
- **US5 (Phase 7)**: Depends on Foundational only (workout editing is independent of food log)
- **Polish (Phase 8)**: Depends on all user stories complete

### User Story Dependencies

- **US1 (P1)**: No story dependencies — start after Foundational
- **US2 (P1)**: No story dependencies — can run in parallel with US1
- **US3 (P2)**: Depends on US1 (food log must exist)
- **US4 (P2)**: Depends on US1 (pie chart must exist for "log this meal")
- **US5 (P2)**: No story dependencies — can run in parallel with US1/US2

### Within Each User Story

- Tests MUST be written and verified to FAIL before implementation
- Schemas before service → service before endpoint → endpoint before frontend
- Backend complete before frontend integration
- Invalidate TanStack Query cache after every mutation to keep pie chart live

### Parallel Opportunities

- T002 and T003 in Phase 1 can run in parallel
- T004–T008 in Phase 2: T004 (schemas) → T005 (service) → T006 (endpoints); T007+T008 (frontend types/client) in parallel with T004
- US1 and US2 can be developed in parallel after Foundational
- US5 can be developed in parallel with US3 and US4
- All test tasks within a phase marked [P] can run in parallel

---

## Parallel Example: Phase 2 Foundational

```bash
# Run in parallel (no dependencies between them):
Task: "Add FoodLogEntryIn/Out schemas to recommendation.py (T004)"
Task: "Add TypeScript types + API client to api.ts (T007, T008)"

# Then sequentially:
Task: "Implement FoodLogService in food_log_service.py (T005)"  # needs T004
Task: "Add 4 endpoints to recommendations.py (T006)"           # needs T005
```

## Parallel Example: P1 Stories (US1 + US2)

```bash
# After Foundational complete, run in parallel:
Developer A: US1 tasks T009–T018 (food log panel + pie chart)
Developer B: US2 tasks T019–T023 (restaurant label badge)
```

---

## Implementation Strategy

### MVP (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup (T001–T003)
2. Complete Phase 2: Foundational (T004–T008)
3. Complete Phase 3: US1 (food log + pie chart) — validate independently
4. Complete Phase 4: US2 (restaurant labels) — validate independently
5. **STOP and VALIDATE**: Users can log food, see macro pie chart update, and restaurant items are labelled
6. Ship as MVP

### Incremental Delivery

1. Setup + Foundational → DB + API ready
2. + US1 → food log panel + macro pie chart working
3. + US2 → restaurant labels in search results
4. + US3 → saved meal shortcuts
5. + US4 → "Log this meal" on AI diet plan + live macro preview
6. + US5 → live workout quality score on plan edit
7. + Polish → error states, empty states, quickstart validation

---

## Notes

- [P] tasks = different files, no blocking dependencies — safe to parallelize
- [Story] label maps task to spec.md user story for traceability
- Tests marked ⚠️ must FAIL before implementation — confirm failure before writing production code
- All test tasks are MANDATORY per project constitution Principle IV
- The food log is the single source of truth for the pie chart — no server-side aggregation
- Never add `WHERE` clauses without `user_id` filter on `daily_food_log_entries`
- Restaurant data (USDA Branded) requires no backend changes — `brand` field already returned
