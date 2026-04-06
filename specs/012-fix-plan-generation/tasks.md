# Tasks: Fix Plan Generation Availability

**Input**: Design documents from `/specs/012-fix-plan-generation/`
**Branch**: `012-fix-plan-generation`

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)

---

## Phase 1: Setup

**Purpose**: No new dependencies or project structure changes needed — this is a logic-only fix.

- [X] T001 Verify current branch is `012-fix-plan-generation` and working directory is clean

---

## Phase 2: Foundational

**Purpose**: Understand the exact retry/error flow in both generation functions before changing anything.

- [X] T002 Read `services/recommendation-service/src/services/recommendation_service.py` and identify the exact point where a rate-limit HTTPException from a retry attempt bubbles up as a 503 to the user (lines ~66–78 for diet, ~127–142 for workout)

---

## Phase 3: User Story 1 — Plan Generation Always Delivers a Plan (Priority: P1) 🎯 MVP

**Goal**: When the AI service responds successfully to at least one request, the user always receives a plan — even if subsequent quality-retry attempts fail with a rate-limit error.

**Independent Test**: Trigger plan generation while mocking the LLM to succeed on attempt 1 (returns a plan) but raise a rate-limit error on attempt 2; verify a plan is returned to the user, not a 503.

### Implementation for User Story 1

- [X] T003 [US1] In `services/recommendation-service/src/services/recommendation_service.py` function `generate_diet_recommendation` (lines ~66–78): wrap the inner `llm.generate(prompt)` call in a try/except that catches `HTTPException` with status 503; on catch, break out of the retry loop and use whatever `structured` dict was produced on the prior successful attempt (or fall through to saving an empty/parse-error plan). Set `best_structured` to track the last valid parse before each attempt.
- [X] T004 [US1] In `services/recommendation-service/src/services/recommendation_service.py` function `generate_workout_recommendation` (lines ~127–142): apply the same pattern — catch 503 `HTTPException` during retry attempts and fall back to the best plan received so far. If `best_structured` is empty (first attempt itself failed), re-raise the exception so the user sees the real error.
- [X] T005 [US1] In `services/recommendation-service/src/services/recommendation_service.py`, add a 1-second `asyncio.sleep(1)` delay between retry attempts in both diet and workout loops to reduce rate-limit pressure on subsequent calls.
- [X] T006 [P] [US1] Add unit test in `services/recommendation-service/tests/test_plan_generation_resilience.py` that verifies: (a) when attempt 1 succeeds and attempt 2 raises HTTPException(503), the service returns the plan from attempt 1; (b) when attempt 1 itself raises HTTPException(503), the 503 propagates to the caller.

**Checkpoint**: Plan generation now returns the best available plan even when retries are rate-limited. Verify by running `pytest tests/test_plan_generation_resilience.py`.

---

## Phase 4: User Story 2 — Retry Button in UI (Priority: P2)

**Goal**: When a genuine failure occurs (first attempt itself fails), the user sees a friendly error with a "Try Again" button that re-triggers generation without a page reload.

**Independent Test**: Simulate a total LLM failure on the Plans page; verify a non-technical message appears with a "Try Again" button; click it and verify the generation restarts.

### Implementation for User Story 2

- [X] T007 [US2] In `frontend/app/(app)/recommendations/page.tsx`, locate the diet generation error state display (search for `generateDietMutation.isError` or similar). Ensure the error message shown is "Service is currently busy — please try again in a few minutes." and add a "Try Again" button that calls `generateDietMutation.reset()` followed by re-triggering the mutation.
- [X] T008 [US2] In `frontend/app/(app)/recommendations/page.tsx`, apply the same pattern for workout generation error state (`generateWorkoutMutation.isError`): friendly error message + "Try Again" button.

**Checkpoint**: Both diet and workout error states show a friendly message with a functional retry button.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T009 Run full test suite: `cd services/recommendation-service && .venv/bin/pytest tests/test_plan_generation_resilience.py tests/test_diet_macro_display.py tests/test_workout_delete.py tests/test_prompt_builder.py -v` and confirm all pass
- [X] T010 [P] Update `specs/012-fix-plan-generation/tasks.md` marking all completed tasks as [X]

---

## Dependencies & Execution Order

- **T001–T002**: Sequential setup
- **T003–T006**: All US1 tasks; T003 and T004 can be done in parallel (different functions, same file is fine — they're non-overlapping edits); T005 depends on T003/T004 edits being in place; T006 is independent [P]
- **T007–T008**: US2 tasks, independent of each other [P], can start after T003/T004 are done (no functional dependency but logically follow)
- **T009–T010**: Polish, after all implementation tasks

---

## Implementation Strategy

### MVP First (US1 only)

1. T001–T002: Confirm setup
2. T003–T005: Fix retry resilience in backend (15 min)
3. T006: Write unit test to lock in the behavior
4. **STOP and VALIDATE**: Confirm plan generation works end-to-end
5. Add US2 (retry button) as a UI polish step

### Key Code Locations

- Backend retry loop (diet): `services/recommendation-service/src/services/recommendation_service.py` lines ~66–78
- Backend retry loop (workout): same file, lines ~127–142
- Frontend error state: `frontend/app/(app)/recommendations/page.tsx` (search `isError`)
