# Tasks: Plans UX Fixes and Workout Insights

**Input**: Design documents from `/specs/011-plans-fixes-workout-insight/`  
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Note**: Tests are MANDATORY per project constitution (Principle IV). All P1 and P2 user stories require end-to-end test coverage.

---

## Phase 1: Setup

**Purpose**: No new infrastructure required — this feature only modifies existing files. One shared helper is extracted.

- [X] T001 Extract `computeDayTotals(meals)` helper function in `frontend/app/(app)/recommendations/page.tsx` (or `frontend/lib/plan-utils.ts` if preferred)

**Checkpoint**: Helper available; all other tasks can proceed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend DELETE endpoint and frontend API method must exist before frontend delete UI can be built.

- [X] T002 Add `DELETE /api/recommendations/workout/{rec_id}` route to `services/recommendation-service/src/routers/recommendations.py` (ownership check: 404 if not found/not owned; 204 on success)
- [X] T003 Add `deleteWorkout: (id: string) => request(...)` method to `frontend/lib/api.ts`

**Checkpoint**: Backend delete endpoint operational; frontend API method callable.

---

## Phase 3: User Story 1 — Diet Plan Calorie Accuracy (Priority: P1) 🎯 MVP

**Goal**: Every diet plan day displays totals computed from actual meal values — no more AI-provided `day_totals` mismatch.

**Independent Test**: Open any diet plan, sum meal calories manually, confirm displayed total matches.

### Tests for User Story 1

- [X] T004 [P] [US1] Unit test for `computeDayTotals` helper covering: normal sum, missing meal fields (default 0), empty meals array — in `services/recommendation-service/tests/test_diet_macro_display.py` (or frontend test file)

### Implementation for User Story 1

- [X] T005 [US1] Replace all reads of `day.day_totals` in the diet plan display view with `computeDayTotals(day.meals)` in `frontend/app/(app)/recommendations/page.tsx` (depends on T001)
- [X] T006 [US1] Verify calorie, protein, carbs, and fat totals are all derived from meal-level values (not the AI-returned aggregate) in `frontend/app/(app)/recommendations/page.tsx`

**Checkpoint**: Diet plan day totals always match meal sums. User Story 1 independently testable.

---

## Phase 4: User Story 2 — Activity Level Auto-Populated from Profile (Priority: P2)

**Goal**: Plans page has no activity level selector; profile value is used automatically.

**Independent Test**: Navigate to Plans page — no `<select>` for activity level visible; generate plan and verify macro targets reflect profile's activity level.

### Tests for User Story 2

- [X] T007 [P] [US2] Unit test verifying `profile.activity_level ?? "moderately_active"` fallback logic — in `services/recommendation-service/tests/test_activity_level_fallback.py`

### Implementation for User Story 2

- [X] T008 [US2] Remove `activityLevel` state variable and the activity level `<select>` element from `frontend/app/(app)/recommendations/page.tsx` (approx. lines 334, 418-425)
- [X] T009 [US2] Read `profile?.activity_level ?? "moderately_active"` from the existing `useQuery(["profile"])` result and pass it to `calculateMacros()` call in `frontend/app/(app)/recommendations/page.tsx`
- [X] T010 [US2] Pass same profile activity level value to `generateDiet()` call in `frontend/app/(app)/recommendations/page.tsx`

**Checkpoint**: Activity level selector gone; plan generation uses profile value. User Story 2 independently testable.

---

## Phase 5: User Story 3 — Saved Day Plans Visible (Priority: P2)

**Goal**: Logged day plans appear in "My Saved Meals" sub-tab and Day Planner view.

**Independent Test**: Log a diet plan day, open "My Saved Meals" — plan is listed. Open Day Planner — plan is available.

### Tests for User Story 3

- [X] T011 [P] [US3] Integration test for `GET /api/recommendations/day-plans` — verify returns saved plans for authenticated user — in `services/recommendation-service/tests/test_day_plans.py`

### Implementation for User Story 3

- [X] T012 [US3] In "My Saved Meals" sub-tab: render `dayPlans` list (from `useQuery(["day-plans"])` result) directly, showing plan name and date, in `frontend/app/(app)/recommendations/page.tsx`
- [X] T013 [US3] In Day Planner view: read from `dayPlans` query result instead of filtering custom meals by description prefix in `frontend/app/(app)/recommendations/page.tsx`
- [X] T014 [US3] Add empty state message for "My Saved Meals" when both `dayPlans` and custom meals are empty in `frontend/app/(app)/recommendations/page.tsx`

**Checkpoint**: Saved day plans visible in both surfaces. User Story 3 independently testable.

---

## Phase 6: User Story 4 — Delete Workout Plans (Priority: P3)

**Goal**: Users can delete any AI-generated workout plan with confirmation.

**Independent Test**: Generate two workout plans; delete one via confirm flow; verify it disappears.

### Tests for User Story 4

- [X] T015 [P] [US4] Integration test: `DELETE /api/recommendations/workout/{rec_id}` — 204 on valid owned plan in `services/recommendation-service/tests/test_workout_delete.py`
- [X] T016 [P] [US4] Integration test: `DELETE /api/recommendations/workout/{rec_id}` — 404 when plan not found or belongs to another user in `services/recommendation-service/tests/test_workout_delete.py`
- [X] T017 [P] [US4] Integration test: `DELETE /api/recommendations/workout/{rec_id}` — 401 when unauthenticated in `services/recommendation-service/tests/test_workout_delete.py`

### Implementation for User Story 4

- [X] T018 [US4] Add `deletingWorkoutId` state (string | null) and `deleteWorkout` mutation (calling `api.deleteWorkout`) in `frontend/app/(app)/recommendations/page.tsx` (depends on T003)
- [X] T019 [US4] Add Delete button to each workout plan card in `frontend/app/(app)/recommendations/page.tsx`; on click: set `deletingWorkoutId = plan.id`
- [X] T020 [US4] When `deletingWorkoutId === plan.id`: show inline "Confirm / Cancel" buttons; on Confirm call `deleteWorkout.mutate(plan.id)` and invalidate `["workout-recommendations"]` query in `frontend/app/(app)/recommendations/page.tsx`
- [X] T021 [US4] Add empty state for workout AI Generated Plans section when plan list is empty after deletion in `frontend/app/(app)/recommendations/page.tsx`

**Checkpoint**: Workout plans deletable with confirmation. User Story 4 independently testable.

---

## Phase 7: User Story 5 — Workout Plan Body-Composition Explanation (Priority: P3)

**Goal**: Each new workout plan shows a "Why this plan?" paragraph at the top, referencing the user's scan data.

**Independent Test**: Generate a workout plan; verify a non-empty explanation paragraph appears at the top before the exercise list.

### Tests for User Story 5

- [X] T022 [P] [US5] Unit test: verify updated `build_workout_prompt()` includes `plan_explanation` field in the requested JSON schema in `services/recommendation-service/tests/test_prompt_builder.py`

### Implementation for User Story 5

- [X] T023 [US5] Update `build_workout_prompt()` in `services/recommendation-service/src/services/prompt_builder.py` to include `plan_explanation` as a required top-level key in the requested JSON structure, with instruction to reference user's scan body composition metrics
- [X] T024 [US5] In expanded workout plan view, read `plan.structured_plan.plan_explanation ?? plan.structured_plan.summary` and render it at the TOP of the plan before the day/exercise list in `frontend/app/(app)/recommendations/page.tsx`
- [X] T025 [US5] Style the explanation block with a "Why this plan?" label in `text-xs text-muted-foreground` and a `glass-card p-3 mb-4` container in `frontend/app/(app)/recommendations/page.tsx`
- [X] T026 [US5] Guard: if neither `plan_explanation` nor `summary` exists (older plans), render nothing — no crash, no empty container in `frontend/app/(app)/recommendations/page.tsx`

**Checkpoint**: New workout plans show body-composition explanation at top. User Story 5 independently testable.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T027 [P] Run full pytest suite in `services/recommendation-service/` and confirm all tests pass
- [X] T028 [P] TypeScript type-check frontend: `cd frontend && npx tsc --noEmit`
- [X] T029 Run all 6 quickstart.md manual scenarios and verify each passes
- [X] T030 Review all changed files for user-scoped data access (constitution security check)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — blocks US4 only
- **US1 (Phase 3)**: Depends on Phase 1 (T001) only — can start after T001
- **US2 (Phase 4)**: Independent of all other user stories — can run in parallel with US1/US3
- **US3 (Phase 5)**: Independent of all other user stories — can run in parallel with US1/US2
- **US4 (Phase 6)**: Depends on Phase 2 (T002, T003) — can proceed after foundational backend/API work
- **US5 (Phase 7)**: Independent of all other user stories — can run in parallel
- **Polish (Phase 8)**: Depends on all desired stories being complete

### Parallel Opportunities

```bash
# After T001 completes, these can all run simultaneously:
Task: US1 — Fix diet day totals (T004–T006)
Task: US2 — Remove activity level selector (T007–T010)
Task: US3 — Fix saved day plans visibility (T011–T014)
Task: US5 — Workout explanation prompt + display (T022–T026)

# After T002+T003 complete:
Task: US4 — Delete workout plan UI (T015–T021)
```

---

## Implementation Strategy

### MVP (US1 + US2 only — critical fixes)

1. T001 — extract helper
2. T004–T006 — fix diet totals
3. T007–T010 — remove activity level selector
4. **VALIDATE**: Both fixes working; diet shows accurate calories; no redundant selector

### Full Delivery Order

1. Phase 1 → Phase 2 (foundation)
2. US1 + US2 + US3 in parallel (all frontend-only or data-fetch fixes)
3. US4 (requires foundational backend work from Phase 2)
4. US5 (backend prompt change + frontend display)
5. Phase 8 (polish + full test run)

---

## Notes

- 30 tasks total across 8 phases
- US1 (4 tasks), US2 (4 tasks), US3 (4 tasks), US4 (7 tasks), US5 (5 tasks)
- No DB migrations required
- Heaviest change is in `frontend/app/(app)/recommendations/page.tsx` — all 5 stories touch this file; implement sequentially within the file to avoid conflicts
- Mark each task `[X]` when complete
