# Tasks: Fix Save Diet Day Plan Visibility

**Input**: Design documents from `/specs/016-fix-save-day-plan-visibility/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, quickstart.md ✓

**Organization**: Tasks grouped by user story. All changes are in a single component (`DietDayRow`) inside `frontend/app/(app)/recommendations/page.tsx`. US1 and US2 are delivered by the same code change (cache invalidation runs on success); US3 adds inline feedback UI on top.

---

## Phase 1: Setup

**Purpose**: Confirm the target file and locate the exact code blocks to change before writing any code.

- [X] T001 Read `frontend/app/(app)/recommendations/page.tsx` and locate the `DietDayRow` component — confirm the `saveDayPlan` function signature, the `savingDay` state, the `qc.invalidateQueries` call, the `alert("No meals…")` guard, and the "Save day" button JSX

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add the two new state variables that both US1/US2 and US3 depend on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T00X In `DietDayRow` in `frontend/app/(app)/recommendations/page.tsx`, add `const [saveError, setSaveError] = useState<string | null>(null)` and `const [saveSuccess, setSaveSuccess] = useState(false)` alongside the existing `savingDay` state

**Checkpoint**: Foundation ready — error/success state available for all stories

---

## Phase 3: User Story 1 & 2 — Saved plan appears in Food & Meals and Day Planner tabs (Priority: P1) 🎯 MVP

**Goal**: After a successful save the `["day-plans"]` cache is invalidated and both tabs refresh without a page reload.

**Independent Test**: Generate a diet plan → expand Day 1 → click "Save day" → switch to Food & Meals → Saved tab → "Day 1 meal plan" appears; switch to Day Planner → same plan appears.

### Implementation for User Story 1 & 2

- [X] T00X [US1] In `saveDayPlan` in `frontend/app/(app)/recommendations/page.tsx`, replace the `alert("No meals to save…")` guard with `setSaveError("No meals to save — add foods first."); return` (also reset `saveSuccess`)
- [X] T00X [US1] In `saveDayPlan`, wrap the existing `try/finally` body so it becomes `try { … await createDayPlan(…); qc.invalidateQueries({ queryKey: ["day-plans"] }); setSaveSuccess(true); setTimeout(() => setSaveSuccess(false), 3000); } catch { setSaveError("Failed to save — please try again.") } finally { setSavingDay(false) }` — adding the missing `catch` block and moving `invalidateQueries` inside the `try` success path in `frontend/app/(app)/recommendations/page.tsx`
- [X] T00X [US1] At the start of `saveDayPlan`, reset stale state: `setSaveError(null); setSaveSuccess(false)` (after the guard check, before `setSavingDay(true)`) in `frontend/app/(app)/recommendations/page.tsx`

**Checkpoint**: US1 & US2 complete — save now invalidates cache on success, shows error on failure; both tabs update.

---

## Phase 4: User Story 3 — Save action provides user feedback (Priority: P2)

**Goal**: Inline success and error messages appear below the "Save day" button row.

**Independent Test**: Click "Save day" → spinner while saving → green "Day saved ✓" for 3 s → auto-clears. Disable network → red "Failed to save — please try again." appears.

### Implementation for User Story 3

- [X] T00X [US3] In the JSX of `DietDayRow` in `frontend/app/(app)/recommendations/page.tsx`, add below the "Save day" button row: `{saveError && <p className="text-xs text-red-400 mt-1">{saveError}</p>}` and `{saveSuccess && <p className="text-xs text-green-400 mt-1">Day saved ✓</p>}`

**Checkpoint**: US3 complete — users see inline feedback for all outcomes.

---

## Phase 5: Tests

**Goal**: Unit-test the `saveDayPlan` control-flow logic (error state, success state, guard) without mounting the full component.

- [X] T00X [P] Create `frontend/__tests__/recommendations/saveDayPlan.test.ts` with Vitest unit tests covering: (a) empty meals guard sets `saveError` and does NOT call `createDayPlan`; (b) successful save calls `invalidateQueries` and sets `saveSuccess`; (c) failed save (rejected promise) sets `saveError` and clears `savingDay`; (d) success message clears after 3 s via fake timers

---

## Phase 6: Polish & Validation

- [X] T00X Run the quickstart scenarios from `specs/016-fix-save-day-plan-visibility/quickstart.md` manually (or via `cd frontend && node_modules/.bin/vitest run __tests__/recommendations/ --no-coverage`) to confirm all 4 scenarios pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on T001 — BLOCKS all user story work
- **US1/US2 (Phase 3)**: Depends on Phase 2 (T002)
- **US3 (Phase 4)**: Depends on Phase 2 (T002); can start in parallel with Phase 3
- **Tests (Phase 5)**: Can start after Phase 3 is complete
- **Polish (Phase 6)**: Depends on all phases

### Within Each Phase

- T003 → T004 → T005 must run sequentially (same function, same file)
- T006 can run in parallel with T003-T005 (different JSX block)
- T007 can run in parallel after T003-T005 (test file only)

### Parallel Opportunities

```bash
# After T002 completes:
Task A: T003 → T004 → T005 (saveDayPlan logic)
Task B: T006 (JSX feedback rendering) — different lines, no conflict
```

---

## Implementation Strategy

### MVP First (US1 + US2 — one code change)

1. T001: Read and locate
2. T002: Add state vars
3. T003 → T004 → T005: Fix `saveDayPlan`
4. **STOP and VALIDATE**: Save a day → check Food & Meals and Day Planner tabs update
5. T006: Add feedback JSX (US3)
6. T007: Add unit tests
7. T008: Run quickstart validation

---

## Notes

- All changes are in a single file: `frontend/app/(app)/recommendations/page.tsx`
- The `["day-plans"]` invalidation is already correct — the only fix needed is adding `catch` and resetting state
- Do NOT use `alert()` anywhere in the updated flow
- `setTimeout` return value should be stored in a `useRef` and cleared on unmount to prevent state updates on unmounted components (see research.md Decision 3)
