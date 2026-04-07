# Tasks: Workout Score Accuracy, Analytics Depth & Quality Polish

**Input**: Design documents from `/specs/023-workout-analytics-quality/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

---

## Phase 1: Setup

**Purpose**: Read current implementations before modifying.

- [X] T001 Read `services/recommendation-service/src/services/workout_engine.py` to understand current plan generation and validation loop
- [X] T002 [P] Read `frontend/app/(app)/recommendations/page.tsx` lines 130–200 to understand current frontend scoring useMemo and what state changes trigger it
- [X] T003 [P] Read `frontend/app/(app)/analytics/page.tsx` full file to understand current layout and data usage
- [X] T004 [P] Read `frontend/app/(app)/profile/page.tsx` full file to understand current mutation structure for restrictions and goal

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No shared infrastructure changes needed. Phases 3+ can proceed independently after Phase 1 reads.

**Checkpoint**: Phase 1 reads complete — all four stories can proceed in parallel.

---

## Phase 3: User Story 1 — Workout Score ≥95% + Reactivity (Priority: P1) 🎯 MVP

**Goal**: Generated plans always score ≥95%. Score updates immediately when reps, sets, duration, or rest are edited.

**Independent Test**: Generate a plan → confirm score is 95–100%. Edit any set/rep/duration/rest field → confirm score updates immediately without page reload.

### Implementation for User Story 1

- [X] T005 [US1] Update `services/recommendation-service/src/services/workout_engine.py`: in the plan generation/validation function, after calling `score_workout_split(plan)`, if `score.overall < 95` boost sets on the lowest-scoring muscle groups (proportional to their gap to target) and re-score; retry up to 10 times; if still below 95 after retries raise a generation error with descriptive message
- [X] T006 [US1] Update `frontend/app/(app)/recommendations/page.tsx`: find the `useMemo` or scoring computation (lines ~138-189) that calculates the displayed score; ensure it depends on every mutable exercise field (sets, reps, duration_seconds, rest_seconds) not just the exercise list reference — if state stores exercises as an array of objects, the memo must be keyed on a serialisation of all fields (e.g. `JSON.stringify(exercises)`) so any field edit triggers recalculation

**Checkpoint**: Score is always ≥95% on generation; inline edits update the score immediately.

---

## Phase 4: User Story 2 — Enhanced Analytics Page (Priority: P1)

**Goal**: Analytics page shows delta cards, plain-language summary, muscle balance analysis, and full metric trends.

**Independent Test**: With 2+ scans, open Analytics — confirm delta cards row, summary card, balance section, and full trend charts are all visible. With 0 scans, confirm empty state with CTA.

### Implementation for User Story 2

- [X] T007 [US2] Update `frontend/app/(app)/analytics/page.tsx`: add a delta cards row at the top of the page mapping `data.deltas` to cards for body_weight_kg, body_fat_percentage, skeletal_muscle_mass_kg, and BMI — each card shows the metric label, current value, and delta with a ▲/▼ coloured indicator (green for improvement, red for decline; note: for body_fat_percentage, a decrease is improvement)
- [X] T008 [US2] Update `frontend/app/(app)/analytics/page.tsx`: add a plain-language body composition summary card below the delta row — derive text from the latest body_fat_percentage and skeletal_muscle_mass_kg values using gender-neutral thresholds (body fat: <18% = "Athletic", 18–25% = "Healthy", 25–30% = "Above Average", >30% = "High Body Fat"); show as a highlighted card with an interpretation sentence
- [X] T009 [US2] Update `frontend/app/(app)/analytics/page.tsx`: add a muscle balance section using the latest scan's segmental lean mass values (segmental_lean_left_arm_kg, segmental_lean_right_arm_kg, segmental_lean_left_leg_kg, segmental_lean_right_leg_kg from `data.deltas`); compute imbalance as `|left - right| / max(left, right) * 100`; if >10% show a warning badge with the dominant side and percentage difference; show a simple comparison bar for arms and legs even without imbalance
- [X] T010 [US2] Update `frontend/app/(app)/analytics/page.tsx`: expand trend charts to show ALL metrics from `data.history` (not just the first 4); group into "Primary" (body_weight_kg, body_fat_percentage, skeletal_muscle_mass_kg, BMI) shown first, and "Body Composition Details" (fat_free_mass_kg, visceral_fat_level, basal_metabolic_rate_kcal, total_body_water_l) shown in a collapsible or secondary section below
- [X] T011 [US2] Update `frontend/app/(app)/analytics/page.tsx`: handle the 0-scan and 1-scan states — with 0 scans show "Upload your first InBody scan to see analytics" with a link to /scans; with exactly 1 scan show the summary card and segmental snapshot but replace trend charts with a prompt "Upload a second scan to unlock progress tracking"

**Checkpoint**: Analytics page is richly informative for users with data; graceful for users without.

---

## Phase 5: User Story 3 — Optimistic UI Updates for Profile (Priority: P2)

**Goal**: Dietary restriction and health goal changes reflect instantly on screen; server syncs in background.

**Independent Test**: Click a dietary restriction — highlight appears before any network activity. Click health goal — highlights immediately. On simulated network failure, UI reverts with inline error.

### Implementation for User Story 3

- [X] T012 [US3] Update `frontend/app/(app)/profile/page.tsx` `addRestriction` mutation: add `onMutate: async (restrictionType) => { await qc.cancelQueries({ queryKey: ["restrictions"] }); const previous = qc.getQueryData(["restrictions"]); qc.setQueryData(["restrictions"], (old) => [...(old ?? []), { id: "optimistic-" + Date.now(), user_id: "", restriction_type: restrictionType, notes: null }]); return { previous }; }` and `onError: (_err, _vars, ctx) => { qc.setQueryData(["restrictions"], ctx?.previous); }` and `onSettled: () => qc.invalidateQueries({ queryKey: ["restrictions"] })` — remove the existing `onSuccess` invalidation
- [X] T013 [US3] Update `frontend/app/(app)/profile/page.tsx` `removeRestriction` mutation: add `onMutate: async (id) => { await qc.cancelQueries({ queryKey: ["restrictions"] }); const previous = qc.getQueryData(["restrictions"]); qc.setQueryData(["restrictions"], (old) => (old ?? []).filter((r) => r.id !== id)); return { previous }; }` and `onError`/`onSettled` as above
- [X] T014 [US3] Update `frontend/app/(app)/profile/page.tsx` `setGoal` mutation: add `onMutate: async (goalType) => { await qc.cancelQueries({ queryKey: ["goal"] }); const previous = qc.getQueryData(["goal"]); qc.setQueryData(["goal"], (old) => old ? { ...old, goal_type: goalType } : { id: "optimistic", user_id: "", goal_type: goalType }); return { previous }; }` and `onError`/`onSettled` as above

**Checkpoint**: Profile interactions feel instant. Error states revert correctly.

---

## Phase 6: User Story 4 — Full-Stack Iterative Quality Pass (Priority: P2)

**Goal**: Every page reaches production quality. Pass continues until no meaningful improvements remain.

**Independent Test**: Walk all pages as a first-time user (no data) and as a returning user (with data). All empty states, loading states, error states present. No layout breaks at 375px.

### Iteration 1 — Known issues (first pass)

- [X] T015 [US4] Read `frontend/app/(app)/dashboard/page.tsx` and fix any missing empty state (0 scans), add CTA to upload first scan, ensure loading skeleton is shown while data fetches
- [X] T016 [P] [US4] Read `frontend/app/(app)/scans/page.tsx` and fix any missing empty state, ensure upload button is prominent when no scans exist, verify loading state
- [X] T017 [P] [US4] Review `frontend/app/(app)/recommendations/page.tsx` Diet/Workout/Saved tab empty states — ensure each tab shows a helpful message and action when no data exists (e.g., "Generate your first diet plan" with a button)
- [X] T018 [P] [US4] Review `frontend/app/(app)/profile/page.tsx` — ensure all form sections (name, body metrics, goal, restrictions) show a saving/loading indicator while mutations are in flight; ensure error messages are shown inline next to the relevant section

### Iteration 2 — Systematic page review

- [X] T019 [US4] Run `npx tsc --noEmit` in `frontend/` and fix any TypeScript errors introduced by US1–US3 changes
- [X] T020 [US4] Read and review `frontend/app/login/page.tsx` — verify the Create Account / Sign In toggle works cleanly at 375px, all error messages are visible, no layout overflow
- [X] T021 [P] [US4] Audit all pages for raw metric keys visible to users (e.g., "skeletal_muscle_mass_kg" instead of "Skeletal Muscle Mass") — fix any unlabelled metric keys found
- [X] T022 [P] [US4] Check `services/recommendation-service/src/routers/recommendations.py` for any endpoint that returns a 500 without a user-friendly detail message — add appropriate HTTP error responses with descriptive `detail` strings where missing

### Iteration 3 — Additional quality improvements discovered during review

- [X] T023 [US4] After completing T015–T022, do a final walk-through of all six main pages and fix any remaining issues discovered (document each fix inline in the commit message); continue adding sub-iterations as needed until no improvements remain

---

## Phase 7: Polish & Validation

- [X] T024 [P] Run `npx tsc --noEmit` in `frontend/` to confirm zero TypeScript errors
- [ ] T025 [P] Run all 10 smoke test scenarios from `specs/023-workout-analytics-quality/quickstart.md` manually and confirm all pass
- [ ] T026 Commit and merge confirmed working changes to main per Constitution Principle VI

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — reads only
- **Phase 2**: Empty — US1–US4 are all independent after Phase 1
- **Phase 3 (US1)**: T001+T002 reads required first
- **Phase 4 (US2)**: T003 read required first; independent of US1
- **Phase 5 (US3)**: T004 read required first; independent of US1/US2
- **Phase 6 (US4)**: Depends on US1–US3 complete (builds on top of quality baseline)
- **Phase 7 (Polish)**: Depends on all phases complete

### User Story Dependencies

- **US1**: Independent (backend + frontend score fix)
- **US2**: Independent (frontend analytics only)
- **US3**: Independent (frontend profile mutations only)
- **US4**: Should run after US1–US3 to assess overall quality with those fixes in place

### Parallel Opportunities

After Phase 1 reads complete, US1–US3 can all run simultaneously:
- T005+T006 (US1 score fix)
- T007–T011 (US2 analytics)
- T012–T014 (US3 optimistic updates)
- T015–T018 (US4 first iteration — can also run alongside US1–US3)

---

## Implementation Strategy

### MVP First (US1 + US2 — both P1)

1. Phase 1: Read existing files
2. Phase 3: Fix workout score (backend + frontend reactivity)
3. Phase 4: Enhance analytics page
4. **STOP and VALIDATE**: Smoke test scenarios 1–5 from quickstart.md
5. Merge to main if passing

### Full Delivery

1. MVP (US1 + US2) → merge to main
2. US3 (optimistic updates) → merge to main
3. US4 (quality pass, iterative) → merge each confirmed batch to main
4. Repeat US4 iterations until no improvements remain

---

## Notes

- The workout scoring formula in `workout_scorer.py` does NOT change — only the enforcement threshold in `workout_engine.py`
- The frontend score `useMemo` must depend on `JSON.stringify(exercises)` or equivalent to catch field-level changes
- Analytics enhancements are all frontend-computed from existing `data.deltas` and `data.history` — zero backend changes for US2
- For optimistic restriction add, use a temporary `id` (e.g., `"optimistic-" + Date.now()`) that gets replaced when `onSettled` refetches
- US4 is explicitly unbounded — T023 represents the continuing iteration loop, not a single task
