# Tasks: Fix Diet Plan Caloric Accuracy

**Input**: Design documents from `/specs/015-fix-diet-caloric-accuracy/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, quickstart.md ✓

**Organization**: All changes are in a single backend file (`diet_engine.py`) plus tests. US1 (caloric accuracy) is the only meaningful phase; US2 (accuracy displayed to user) is already satisfied by existing UI code once the backend is fixed.

---

## Phase 1: Setup

**Purpose**: Confirm the current behaviour and read the target file before writing.

- [X] T001 Read `services/recommendation-service/src/services/diet_engine.py` and confirm the locations of `_scale_item` (clamp bounds), `_build_meal` (cal_per_item distribution), and `_build_day` (day totals assembly) — no code changes yet

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Write the failing test that proves the current deviation exceeds 5% and must pass after the fix. Constitution IV mandates tests.

- [X] T002 In `services/recommendation-service/tests/test_diet_engine.py`, add a parametrized test `test_caloric_accuracy_within_5_percent` that calls `generate_diet_plan` with five caloric targets (1200, 1800, 2200, 3000, 4000 kcal) and asserts every day's `day_totals.calories` deviates ≤5% from the target — this test MUST FAIL before the fix is applied

**Checkpoint**: Test exists and fails → ready to implement

---

## Phase 3: User Story 1 — Generated Diet Plan Hits Caloric Target (Priority: P1) 🎯 MVP

**Goal**: Every day in every generated plan lands within ±5% of the user's daily caloric target.

**Independent Test**: Run `pytest tests/test_diet_engine.py::test_caloric_accuracy_within_5_percent -v` — all parametrized cases must pass.

### Implementation for User Story 1

- [X] T003 [US1] In `_scale_item` in `services/recommendation-service/src/services/diet_engine.py`, change the gram clamp from `max(30.0, min(400.0, ...))` to `max(20.0, min(600.0, ...))` per FR-004
- [X] T004 [US1] In `_build_day` in `services/recommendation-service/src/services/diet_engine.py`, add empty-slot shortfall redistribution: after building all meals, identify meals with no items, compute their caloric share (`macro_targets.calories * slot_ratio`), and distribute that shortfall proportionally across the non-empty meals by scaling each non-empty meal's items' gram quantities before the correction pass (per FR-005)
- [X] T005 [US1] In `_build_day` in `services/recommendation-service/src/services/diet_engine.py`, add the day-level correction pass: after all meals are assembled (including shortfall redistribution), compute `scale = macro_targets.calories / actual_day_calories`; if `scale` is outside `[0.99, 1.01]`, multiply every item's `grams` by `scale` (clamped to `[20.0, 600.0]`), then recompute each item's `calories`, `protein_g`, `carbs_g`, `fat_g`, `fiber_g` from the new grams, and recompute `meal_totals` and `day_totals` from the corrected items
- [X] T006 [US1] Run `pytest services/recommendation-service/tests/test_diet_engine.py -v` to confirm `test_caloric_accuracy_within_5_percent` now passes for all 5 caloric targets and all existing tests still pass in `services/recommendation-service/tests/test_diet_engine.py`

**Checkpoint**: US1 complete — all 5 caloric targets produce plans within ±5%.

---

## Phase 4: User Story 2 — Caloric Accuracy Displayed to User (Priority: P1)

**Goal**: The deviation badge on the Diet tab reflects accurate values (≤5%) now that the backend engine is fixed.

**Independent Test**: Generate a plan in the UI → expand Day 1 → deviation badge shows ≤5% in green.

### Implementation for User Story 2

- [X] T007 [US2] Verify that `frontend/app/(app)/recommendations/page.tsx` `DietDayRow` already reads `day.day_totals.calories` from the response and computes deviation against `macros.calories` — no code change should be needed; confirm by reading the relevant section (lines ~600–660) and adding a note confirming it works correctly with the now-accurate backend data

**Checkpoint**: US2 complete — no frontend change needed; deviation badge reads from corrected data automatically.

---

## Phase 5: Additional Tests (Constitution IV — Mandatory)

- [X] T008 [P] In `services/recommendation-service/tests/test_diet_engine.py`, add `test_caloric_accuracy_with_restrictions` that calls `generate_diet_plan` with dietary restrictions `["vegetarian"]` and `["vegan"]` at 2200 kcal and asserts ±5% accuracy per FR-003
- [X] T009 [P] In `services/recommendation-service/tests/test_diet_engine.py`, add `test_portion_bounds` that calls `generate_diet_plan` at 1200 and 4000 kcal and asserts no item's `grams` falls below 20g or exceeds 600g per FR-004
- [X] T010 In `services/recommendation-service/tests/test_diet_engine.py`, run the full test suite with `pytest tests/test_diet_engine.py -v` to confirm all new and existing tests pass

---

## Phase 6: Polish & Validation

- [X] T011 Run the quickstart validation script from `specs/015-fix-diet-caloric-accuracy/quickstart.md` to confirm all 5 caloric targets and the vegetarian restriction case pass end-to-end in `services/recommendation-service/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on T001 (must understand the code before writing the failing test)
- **US1 (Phase 3)**: Depends on T002 (failing test must exist first — TDD)
  - T003 → T004 → T005 must run sequentially (same function, same file)
  - T006 validates T003–T005
- **US2 (Phase 4)**: Depends on T005 completion (backend must be accurate)
- **Tests (Phase 5)**: T008 and T009 can run in parallel (different test functions, same file); T010 sequentially after both
- **Polish (Phase 6)**: Depends on T010

### Within Phase 3

- T003 (clamp bounds) must come before T005 (correction pass uses the new bounds)
- T004 (shortfall redistribution) must come before T005 (correction pass assumes redistribution already done)
- T005 (correction pass) is the core fix

---

## Parallel Opportunities

```bash
# Phase 5 — after T005 completes:
Task A: T008 — restriction accuracy tests
Task B: T009 — portion bounds tests
# Then T010 sequentially
```

---

## Implementation Strategy

### MVP (US1 only — 4 tasks)

1. T001: Read and confirm code structure
2. T002: Write failing test
3. T003 → T004 → T005: Apply fix
4. T006: Confirm test passes
5. **STOP and VALIDATE**: All 5 caloric targets within ±5%

### Full delivery

Add T007–T011 for restriction coverage, bounds checks, and quickstart validation.

---

## Notes

- The correction pass in T005 must recompute ALL derived values (calories, macros, meal_totals, day_totals) from the new gram quantities — do not just adjust the totals directly
- The `_item_fields` helper in `meal_service.py` is unrelated — do not touch it
- `_build_day` currently uses a dict comprehension to sum totals; the correction pass should replace or follow this, not duplicate it
- No changes to `generate_diet_plan`, `_build_meal`, `_pick_items`, or `_filter_foods` signatures
