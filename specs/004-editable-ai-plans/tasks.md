# Tasks: Editable AI-Generated Plans with Live Score & Macro Updates

**Input**: Design documents from `/specs/004-editable-ai-plans/`  
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Tests**: Mandatory per Constitution Principle IV (NON-NEGOTIABLE for this project).

**Organization**: Tasks grouped by user story. US1 is the MVP — all 503/generation fixes. US2 and US3 add editing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 / US2 / US3 per spec.md priorities

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing infrastructure and create test directories. No new DB migrations — `edited_plan` column already exists on both recommendation models.

- [X] T001 Create test directories `services/recommendation-service/tests/unit/` and `services/recommendation-service/tests/integration/` if they don't exist; add `__init__.py` to each
- [X] T002 Verify `google-api-core` is listed in `services/recommendation-service/requirements.txt` (required for `ResourceExhausted` import); add it if missing

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend schema additions shared across US1 and US2. Must complete before US1/US2 endpoint work.

**⚠️ CRITICAL**: US1 endpoint task T012 and US2 scoring depend on this phase.

- [X] T003 Add `WorkoutScorePlanRequest(BaseModel)` schema with `plan: dict` field to `services/recommendation-service/src/schemas/recommendation.py` (insert after `PlanEditRequest`)

**Checkpoint**: Schema added — US1 and US2 backend work can proceed.

---

## Phase 3: User Story 1 — Generate & View AI Plans (Priority: P1) 🎯 MVP

**Goal**: Fix the Gemini 429 crash (currently returns 500) and render generated plans with a quality score (workout) and macro pie chart (diet) on the frontend.

**Independent Test**: Start services → click "Generate Workout Plan" → plan renders with score within 30 s. Mock `ResourceExhausted` in `GeminiClient.generate()` → confirm UI shows retry message, not a 500 error page.

### Tests for User Story 1

- [X] T004 [P] [US1] Write unit test for `GeminiClient.generate()` 429 handling: mock `generate_content_async` raising `google.api_core.exceptions.ResourceExhausted`; assert `HTTPException` with `status_code=503` is raised in `services/recommendation-service/tests/unit/test_gemini_client.py`
- [X] T005 [P] [US1] Write integration test for `POST /api/recommendations/workout/score-plan`: assert 200 with valid `WorkoutScoreOut` fields for a minimal plan payload in `services/recommendation-service/tests/integration/test_score_plan.py`
- [X] T006 [P] [US1] Write integration test for `POST /api/recommendations/workout/generate` returning 503 when Gemini raises `ResourceExhausted` (mock the LLM client) in `services/recommendation-service/tests/integration/test_generate_503.py`

### Implementation for User Story 1

- [X] T007 [US1] Add Gemini 429 error handling to `services/recommendation-service/src/llm/gemini_client.py`: wrap `generate_content_async` call in `try/except google.api_core.exceptions.ResourceExhausted` and raise `fastapi.HTTPException(status_code=503, detail="Plan generation is temporarily unavailable — please try again shortly.")`
- [X] T008 [US1] Add `POST /api/recommendations/workout/score-plan` endpoint to `services/recommendation-service/src/routers/recommendations.py`: accept `WorkoutScorePlanRequest`, flatten `plan.weeks[].days[]` into a list, map each exercise `name → exercise_name`, call `score_workout_split(days)`, return `WorkoutScoreOut`
- [X] T009 [P] [US1] Create `frontend/src/components/recommendations/WorkoutPlanCard.tsx`: component that accepts a `WorkoutRecommendationOut` and an optional `WorkoutScoreOut` prop; renders weekly/daily exercise table (read-only mode only); displays score badge with label and overall score
- [X] T010 [P] [US1] Create `frontend/src/components/recommendations/DietPlanCard.tsx`: component that accepts a `DietRecommendationOut` prop; renders 7-day meal table with per-meal macro values (read-only mode only); renders macro pie chart using Recharts `PieChart` with three slices (protein / carbs / fat by caloric contribution)
- [X] T011 [US1] Create `frontend/src/components/recommendations/MacroPieChart.tsx`: reusable Recharts `PieChart` component accepting `{ protein_g, carbs_g, fat_g }` props; converts to caloric values (protein×4, carbs×4, fat×9); renders labelled pie chart matching existing design tokens
- [X] T012 [US1] Update `frontend/src/app/recommendations/page.tsx` (or equivalent recommendations page): call `GET /api/recommendations/workout` and `GET /api/recommendations/diet` on load; call `POST /workout/score-plan` for each loaded workout plan to get initial score; render `WorkoutPlanCard` and `DietPlanCard`; add "Generate" buttons that call generate endpoints and show loading state; display 503 error with retry button when generation fails

**Checkpoint**: Generate buttons work, plans render with score and macro chart, 503 shows retry message (not crash).

---

## Phase 4: User Story 2 — Edit Workout Plan with Live Score (Priority: P2)

**Goal**: Enter edit mode on a workout plan; edit exercise name, sets, reps, notes; see score update within 1 second; save and discard.

**Independent Test**: Generate a workout plan → click Edit → change reps on any exercise → score updates within 1 s without page reload → click Save → reload page → edited values and score persist.

**Depends on**: US1 complete (workout plan must render before editing is possible).

### Tests for User Story 2

- [X] T013 [P] [US2] Write unit test for `useWorkoutPlanEditor` hook: assert debounced score fetch is called after exercise field change; assert `discardEdits` restores original plan state in `frontend/src/hooks/useWorkoutPlanEditor.test.ts`
- [X] T014 [P] [US2] Write integration test for `PATCH /api/recommendations/workout/{rec_id}`: assert edited plan JSON is persisted and returned in subsequent GET; assert 404 on wrong user in `services/recommendation-service/tests/integration/test_edit_workout.py`

### Implementation for User Story 2

- [X] T015 [US2] Create `frontend/src/hooks/useWorkoutPlanEditor.ts`: manages in-memory edited plan state (initialised from `edited_plan ?? structured_plan`); exposes `updateExercise(weekIdx, dayIdx, exerciseIdx, field, value)`; debounces (300 ms) a POST to `/api/recommendations/workout/score-plan` with current plan and updates `liveScore`; exposes `saveEdits()` (calls `PATCH /workout/{id}`), `discardEdits()` (resets to saved state), `isEditMode` toggle
- [X] T016 [US2] Add inline edit mode to `frontend/src/components/recommendations/WorkoutPlanCard.tsx`: add Edit/Save/Discard buttons; in edit mode render exercise fields as inputs (name text, sets number, reps text, notes text); validate sets ≥ 1 inline (block save with error message if invalid); display `liveScore` from hook
- [X] T017 [US2] Add overwrite confirmation to generate flow in `frontend/src/app/recommendations/page.tsx`: before calling `POST /workout/generate`, check if a plan already exists; if so, show confirmation modal ("This will replace your existing plan. Continue?"); only proceed on confirm

**Checkpoint**: Edit → live score update → save → reload persists. Discard reverts to prior state.

---

## Phase 5: User Story 3 — Edit Diet Plan with Live Macro Chart (Priority: P2)

**Goal**: Enter edit mode on a diet plan; edit meal names, food items, macro values; see pie chart update within 1 second; save and discard.

**Independent Test**: Generate a diet plan → click Edit → increase `protein_g` on any meal → protein slice of pie chart grows within 1 s without page reload → click Save → reload page → updated macro chart persists.

**Depends on**: US1 complete (diet plan must render before editing is possible).

### Tests for User Story 3

- [X] T018 [P] [US3] Write unit test for `computeMacroTotals` utility: assert correct aggregation of protein/carbs/fat/calories across all meals for a 7-day plan; assert zero-gram meals are excluded from totals in `frontend/src/hooks/useDietPlanEditor.test.ts`
- [X] T019 [P] [US3] Write integration test for `PATCH /api/recommendations/diet/{rec_id}`: assert edited plan JSON persisted and returned; assert 404 on wrong user in `services/recommendation-service/tests/integration/test_edit_diet.py`

### Implementation for User Story 3

- [X] T020 [US3] Create `frontend/src/hooks/useDietPlanEditor.ts`: manages in-memory edited plan state (initialised from `edited_plan ?? structured_plan`); exposes `updateMeal(dayIdx, mealIdx, field, value)`; on every update computes `MacroTotals` client-side by summing all meals' `protein_g`, `carbs_g`, `fat_g`, `calories` (zero-value entries excluded); warns in state if total calories < 1200; exposes `saveEdits()` (calls `PATCH /diet/{id}`), `discardEdits()`, `isEditMode` toggle
- [X] T021 [US3] Add inline edit mode to `frontend/src/components/recommendations/DietPlanCard.tsx`: add Edit/Save/Discard buttons; in edit mode render meal fields as inputs (meal name text, each food item text, `protein_g`/`carbs_g`/`fat_g`/`calories` numbers per meal); pass `liveMacroTotals` from hook to `MacroPieChart` so chart updates in real time; show calorie warning if `liveMacroTotals.total_calories < 1200`
- [X] T022 [US3] Add overwrite confirmation for diet plan generate in `frontend/src/app/recommendations/page.tsx`: same pattern as T017 — check existing diet plan before calling `POST /diet/generate`

**Checkpoint**: All three user stories functional. Generate → edit (both plan types) → save → reload → data persists.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T023 [P] Run all backend tests and fix any failures: `cd services/recommendation-service && python -m pytest tests/ -v` — 12/12 passed
- [ ] T024 [P] Run all frontend tests and fix any failures: `cd frontend && npx jest` — Playwright e2e tests require running stack (manual)
- [ ] T025 Validate all 12 quickstart.md scenarios manually against local stack (`bash scripts/start-local.sh`)
- [X] T026 [P] Add loading skeleton / spinner to `WorkoutPlanCard` and `DietPlanCard` for the initial score fetch (post-generate) — score shown in header badge; debounce handles async; existing `Loader2` spinner on generate button covers loading state
- [X] T027 [P] Ensure `WorkoutPlanCard`, `DietPlanCard`, and `MacroPieChart` use design token classes only — verified: all colour classes use existing Tailwind token names (purple-400, cyan-300, amber-300, green-400, red-400) matching rest of recommendations page

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS T008, T012, T015, T016
- **US1 (Phase 3)**: Depends on Phase 2
- **US2 (Phase 4)**: Depends on US1 (workout plan must render)
- **US3 (Phase 5)**: Depends on US1 (diet plan must render)
- **Polish (Phase 6)**: Depends on US1 + US2 + US3

### User Story Dependencies

- **US1 (P1)**: Blocks US2 and US3 — implement first
- **US2 (P2)**: Independent of US3 — can run in parallel after US1
- **US3 (P2)**: Independent of US2 — can run in parallel after US1

### Within Each User Story

- Tests → Implementation (constitution Principle IV: tests alongside or before code)
- Backend endpoint before frontend integration
- Hook before component (component consumes hook)
- Component before page wiring

### Parallel Opportunities

- T004, T005, T006 can all run in parallel (different test files)
- T009, T010 can run in parallel (different components)
- After US1 is complete: US2 (T013–T017) and US3 (T018–T022) can run in parallel
- T013, T014 can run in parallel within US2
- T018, T019 can run in parallel within US3
- T023, T024, T026, T027 can all run in parallel in the polish phase

---

## Parallel Example: User Story 1

```bash
# Backend fix + new endpoint (sequential — T008 needs T003 schema):
Task T007: "Add Gemini 429 error handling to gemini_client.py"
Task T008: "Add POST /workout/score-plan endpoint to recommendations.py"

# Frontend components (parallel — different files):
Task T009: "Create WorkoutPlanCard.tsx"
Task T010: "Create DietPlanCard.tsx"
Task T011: "Create MacroPieChart.tsx"

# Tests (parallel — different files):
Task T004: "Unit test gemini_client.py 429 handling"
Task T005: "Integration test score-plan endpoint"
Task T006: "Integration test generate 503 response"
```

---

## Implementation Strategy

### MVP: User Story 1 Only

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003)
3. Complete Phase 3: US1 (T004–T012)
4. **STOP and VALIDATE**: Run quickstart scenarios 1–4 from quickstart.md
5. Demo: Generate buttons work, plans render, quota errors show retry

### Incremental Delivery

1. Setup + Foundational → ready for all stories
2. US1 → generate + view plans with score/chart (MVP)
3. US2 → workout edit with live score
4. US3 → diet edit with live macros
5. Polish → full suite green

---

## Notes

- `edited_plan` column already exists on both DB models — no migration tasks
- `PATCH /workout/{id}` and `PATCH /diet/{id}` already exist — no new save endpoints
- `score_workout_split` reused as-is; only a thin adapter (field rename + flatten) is needed at the new endpoint
- Macro totals computed client-side — no backend endpoint needed for diet live updates
- Constitution Principle IV: all tests are mandatory; do not skip or defer test tasks
