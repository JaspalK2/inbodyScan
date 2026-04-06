# Tasks: Plan Save Flow and Workout UX Fixes

**Input**: Design documents from `/specs/006-plan-save-workout-ux/`  
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ui.md ✓, quickstart.md ✓

**Tests**: Mandatory per Constitution Principle IV (NON-NEGOTIABLE for this project).

**Organization**: All 5 user stories are pure frontend changes to `frontend/app/(app)/recommendations/page.tsx`. US1–US4 are P1. US5 is P2.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1 / US2 / US3 / US4 / US5 per spec.md priorities

---

## Phase 1: Setup

**Purpose**: Verify no new dependencies required; confirm existing test infrastructure.

- [X] T001 Confirm no new npm packages needed: verify `frontend/package.json` already has TanStack Query v5, React 18, and all required UI components — no installs required
- [X] T002 [P] Confirm frontend test setup: verify `frontend/` has Jest + React Testing Library configured (check `package.json` for `@testing-library/react` and `jest` entries); create `frontend/app/(app)/recommendations/page.test.tsx` placeholder if it doesn't exist

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No new backend or shared infrastructure is needed. This feature is purely frontend changes to a single page. Phase 2 is minimal — just understanding the current state of the primary file.

- [X] T003 Read and understand `frontend/app/(app)/recommendations/page.tsx` focusing on: (a) `DietDayRow` component and its current "Save day" button handler, (b) `FoodMealsTab` saved sub-tab and the "Day Plans" section added in 005, (c) `WorkoutPlanCard` exercise view/edit rendering, (d) `WorkoutTab` split builder and its score display

**Checkpoint**: Implementation can now begin across all user stories.

---

## Phase 3: User Story 1 — Save Day Creates Day Plan + Individual Meals (Priority: P1) 🎯 MVP

**Goal**: "Save Day" on a generated diet plan day simultaneously creates one `DayPlan` record AND one `CustomMeal` per non-empty meal slot, named `"Day Planner — {Slot}"`.

**Independent Test**: Generate diet plan → click "Save Day" on Day 1 → navigate to Food & Meals → Saved Meals → confirm "Day Planner — Breakfast", "Day Planner — Lunch" etc. appear → navigate to Day Planner tab → confirm the day plan record appears.

### Tests for User Story 1

- [X] T004 [P] [US1] Write unit test in `frontend/app/(app)/recommendations/page.test.tsx` for the Save Day composite mutation logic: given a diet day with 3 non-empty meal slots, assert that `createMeal` is called 3 times with names `"Day Planner — Breakfast"`, `"Day Planner — Lunch"`, `"Day Planner — Dinner"` AND `createDayPlan` is called once with the correct entries
- [X] T005 [P] [US1] Write unit test in `frontend/app/(app)/recommendations/page.test.tsx` for the empty-day validation: given a day where all meal slots have empty foods arrays, assert that neither `createDayPlan` nor `createMeal` is called and an error state is set

### Implementation for User Story 1

- [X] T006 [US1] In `DietDayRow` inside `frontend/app/(app)/recommendations/page.tsx`, update the "Save day" button's `saveDayMutation` (or add `saveDayCompositeMutation`) so that after `createDayPlan` succeeds, it calls `recommendations.createMeal` via `Promise.all` for each non-empty meal slot (where `meal.foods.length > 0`), using name `"Day Planner — {capitalised slot}"` (e.g. `"Day Planner — Breakfast"`), description `"Saved from Day {N} diet plan"`, and items mapped from `meal.foods` with per-food macros from `meal._mf`
- [X] T007 [US1] In `DietDayRow` inside `frontend/app/(app)/recommendations/page.tsx`, add validation before the save: if all meal slots have `(meal.foods ?? []).length === 0`, show an error toast "No meals to save — add foods first" and abort without making any API calls
- [X] T008 [US1] In the Save Day `onSuccess` handler in `DietDayRow` inside `frontend/app/(app)/recommendations/page.tsx`, invalidate both `["day-plans"]` and `["custom-meals"]` query keys so both tabs refresh automatically; show success toast "Day saved — {N} meals added to Saved Meals" where N = count of non-empty slots
- [X] T009 [US1] In `DietDayRow` inside `frontend/app/(app)/recommendations/page.tsx`, add partial-failure handling: if `createDayPlan` succeeds but some `createMeal` calls fail (caught from `Promise.allSettled`), show a warning toast listing which meal slots failed; day plan record is kept

**Checkpoint**: After T006–T009, clicking "Save Day" creates both records. Verify via Scenario 1 in quickstart.md.

---

## Phase 4: User Story 2 — Tab Content Clarity: Remove Day Plans from Food & Meals Tab (Priority: P1)

**Goal**: The Food & Meals → Saved Meals sub-tab shows only individual `CustomMeal` records. The "Day Plans" section added in feature 005 is removed. Day-planner-sourced meals automatically appear here because US1 creates them as `CustomMeal` records.

**Independent Test**: Navigate to Food & Meals → Saved Meals — confirm no "Day Plans" section exists; only individual meal cards appear (including "Day Planner — [Slot]" auto-saved meals). Navigate to Day Planner tab — confirm only whole day plan records appear.

### Tests for User Story 2

- [X] T010 [P] [US2] Write render test in `frontend/app/(app)/recommendations/page.test.tsx`: mock `listMeals` returning 2 meals (one user-named, one "Day Planner — Breakfast") and mock `listDayPlans` returning 1 plan; render `FoodMealsTab` in "saved" sub-tab; assert both meals appear, assert NO "Day Plans" heading is present in the saved sub-tab

### Implementation for User Story 2

- [X] T011 [US2] In `FoodMealsTab` inside `frontend/app/(app)/recommendations/page.tsx`, locate the `saved` sub-tab render block and remove the entire "Day Plans" section (the `<div className="space-y-3">` block containing the `<h3>Day Plans</h3>` heading and `dayPlans.map(...)` rendering that was added in feature 005) — the `useQuery` for `["day-plans"]` inside `FoodMealsTab` should also be removed since it is no longer needed in this tab
- [X] T012 [US2] In `FoodMealsTab` inside `frontend/app/(app)/recommendations/page.tsx`, update the empty state message in the `saved` sub-tab from "No saved meals yet." to "No saved meals yet. Build a meal in the search tab or save a generated diet day."
- [X] T013 [US2] In `FoodMealsTab` inside `frontend/app/(app)/recommendations/page.tsx`, remove the wrapping outer `<div className="space-y-6">` that was added in 005 to contain both the meals section and the now-removed day plans section, and restore the original `<div className="space-y-3">` wrapper with the "Saved Meals" `<h3>` heading also removed (return to the flat list layout with no heading)

**Checkpoint**: After T011–T013, verify Scenario 2 in quickstart.md — each tab shows only its correct content type.

---

## Phase 5: User Story 3 — Exercise Field Labels in View and Edit Mode (Priority: P1)

**Goal**: Every exercise row in any workout plan or custom split shows labelled fields (Sets, Reps, Weight, Rest) in both view and edit modes. No unlabelled numbers.

**Independent Test**: Open any workout plan → expand a training day → confirm each exercise shows "Sets: 3 · Reps: 8–12 · Weight: 60 kg · Rest: 90 s" style labels → enter edit mode → confirm input fields have labels or descriptive placeholders.

### Tests for User Story 3

- [X] T014 [P] [US3] Write render test in `frontend/app/(app)/recommendations/page.test.tsx` for the exercise view row: given exercise `{ name: "Bench Press", sets: 3, reps: "8-12", weight_kg: 60, rest_seconds: 90 }`, assert that the rendered output contains the text "Sets:", "Reps:", "Weight:", "Rest:" as labels alongside their values
- [X] T015 [P] [US3] Write render test in `frontend/app/(app)/recommendations/page.test.tsx` for the exercise view row with null fields: given `{ name: "Push-up", sets: 3, reps: "15", weight_kg: null, rest_seconds: null }`, assert that "Weight:" and "Rest:" are NOT rendered (omit null fields)

### Implementation for User Story 3

- [X] T016 [US3] In `WorkoutPlanCard` inside `frontend/app/(app)/recommendations/page.tsx`, update the view-mode exercise rendering (the `<p key={ei} className="text-xs text-muted-foreground ml-2">` element) to show labelled fields: replace the current `"· {ex.name} — {ex.sets}×{ex.reps}..."` format with a structured display showing `"· {ex.name}"` on one line and `"Sets: {ex.sets} · Reps: {ex.reps}{ ex.weight_kg ? ' · Weight: '+ex.weight_kg+' kg' : ''}{ ex.rest_seconds ? ' · Rest: '+ex.rest_seconds+' s' : ''}"` on a second line using `<div>` layout; omit weight and rest fields when null/zero
- [X] T017 [US3] In `WorkoutPlanCard` inside `frontend/app/(app)/recommendations/page.tsx`, update the edit-mode exercise input grid to add visible labels above (or alongside) each input using `<Label>` component: add `<Label className="text-xs">Sets</Label>` above the sets input, `<Label className="text-xs">Reps</Label>` above reps input, `<Label className="text-xs">Weight (kg)</Label>` above weight input, `<Label className="text-xs">Rest (s)</Label>` above rest input — adjust grid layout to accommodate labels (use `<div className="space-y-1">` wrappers per column)
- [X] T018 [US3] In `WorkoutTab` split builder inside `frontend/app/(app)/recommendations/page.tsx`, apply the same label treatment to the exercise input fields in the custom split day editor (each exercise row in the days editor): add `<Label>` components with "Sets", "Reps", "Weight (kg)", "Rest (s)" above or alongside each input field; also update any view-mode exercise display in `SplitCard` or equivalent component to show labelled fields matching the WorkoutPlanCard format

**Checkpoint**: After T016–T018, verify Scenario 3 in quickstart.md — all exercise fields are labelled.

---

## Phase 6: User Story 4 — Add and Remove Exercises in Generated Workout Plan Edit Mode (Priority: P1)

**Goal**: In edit mode for a generated AI workout plan, users can add new exercise rows to any non-rest day and remove any existing exercise. Score updates within 1 second of each change.

**Independent Test**: Open generated workout plan → Edit → expand Week 1 Day 1 → click "+ Add exercise" → confirm new row appears → click remove on existing exercise → confirm it disappears → score updates within 1 second.

### Tests for User Story 4

- [X] T019 [P] [US4] Write unit test in `frontend/app/(app)/recommendations/page.test.tsx` for the add-exercise state mutation: given a plan with `weeks[0].days[0].exercises = [ex1]`, when addExercise is called for weekIdx=0, dayIdx=0, assert the resulting plan has `weeks[0].days[0].exercises.length === 2` and the new exercise has default values `{ name: "", sets: 3, reps: "8-12", weight_kg: null, rest_seconds: 60 }`
- [X] T020 [P] [US4] Write unit test in `frontend/app/(app)/recommendations/page.test.tsx` for the remove-exercise state mutation: given a plan with `weeks[0].days[0].exercises = [ex1, ex2]`, when removeExercise is called for weekIdx=0, dayIdx=0, exIdx=0, assert the resulting plan has `weeks[0].days[0].exercises = [ex2]`

### Implementation for User Story 4

- [X] T021 [US4] In `WorkoutPlanCard` inside `frontend/app/(app)/recommendations/page.tsx`, add a "+ Add exercise" button below the last exercise row on each non-rest day in edit mode: the button calls `onPlanChange` with the plan updated to append `{ name: "", sets: 3, reps: "8-12", weight_kg: null, rest_seconds: 60 }` to `plan.weeks[wi].days[di].exercises` using nested `.map` spread (the same immutable pattern used by the existing exercise name/sets/reps change handlers); button is NOT shown when `d.is_rest === true`
- [X] T022 [US4] In `WorkoutPlanCard` inside `frontend/app/(app)/recommendations/page.tsx`, add a remove button (X icon using existing `<X className="h-3 w-3" />` from lucide-react) to each exercise row in edit mode: clicking it calls `onPlanChange` with the plan updated to filter out the exercise at index `ei` from `plan.weeks[wi].days[di].exercises`; the existing score debounce (`onPlanChange` triggers `useEffect` → 300ms → `scoreGeneratedPlan`) fires automatically

**Checkpoint**: After T021–T022, verify Scenario 4 and 5 in quickstart.md.

---

## Phase 7: User Story 5 — Live Score in Custom Split Builder (Priority: P2)

**Goal**: The custom split builder (`WorkoutTab`) shows a live quality score that updates within 1 second whenever exercises, sets, or reps change — matching the behaviour already present in `WorkoutPlanCard`.

**Independent Test**: Navigate to Workout → Split tab → add exercises to Monday → confirm live score panel appears → change sets on any exercise → confirm score updates within 1 second.

### Tests for User Story 5

- [X] T023 [P] [US5] Write unit test in `frontend/app/(app)/recommendations/page.test.tsx` for the split builder score trigger: mock `recommendations.scoreSplit`; simulate adding an exercise to the `days` state; assert `scoreSplit` is called with the updated days payload after 300ms debounce (use fake timers)

### Implementation for User Story 5

- [X] T024 [US5] In `WorkoutTab` inside `frontend/app/(app)/recommendations/page.tsx`, add a `liveScore` state (`useState<WorkoutScore | null>(null)`) and a `scoreDebounce` ref (`useRef<ReturnType<typeof setTimeout> | undefined>(undefined)`); add a `useEffect` that watches the `days` state: when days change, clear the debounce timer and set a new 300ms timer that calls `recommendations.scoreSplit({ name: splitName || "draft", days: days.map(d => ({ day_label: d.label, focus: d.focus || undefined, is_rest: d.isRest, exercises: d.isRest ? [] : d.exercises.map(e => ({ exercise_name: e.name, sets: parseInt(e.sets)||undefined, reps: e.reps||undefined, weight_kg: parseFloat(e.weight)||undefined, rest_seconds: parseInt(e.rest)||undefined })) })) })` and stores the result in `liveScore`; the effect cleanup clears the timer
- [X] T025 [US5] In `WorkoutTab` inside `frontend/app/(app)/recommendations/page.tsx`, render the live score panel below the days editor when `liveScore !== null` using the same score card JSX already used in `WorkoutPlanCard` (the `rounded-lg bg-white/5 p-3 space-y-2` div with overall score, sub-score grid for Cov/Vol/Bal/Card/Freq, and feedback bullets); hide the panel when all days have 0 exercises (check `days.every(d => d.isRest || d.exercises.length === 0)`)

**Checkpoint**: After T024–T025, verify Scenario 6 in quickstart.md.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [X] T026 [P] Run all frontend lint checks: `cd frontend && npx tsc --noEmit` — fix any TypeScript errors introduced by the changes
- [X] T027 [P] Validate all 7 quickstart.md scenarios manually against the local running stack
- [X] T028 [P] Verify all new UI elements use only existing design token classes (purple-400, cyan-300, amber-300, green-400, bg-white/5, text-muted-foreground etc.) and existing components (Button, Label, Input, X, Trash2, Loader2, BookmarkPlus) — no inline colours or reimplemented primitives

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — read-only investigation, no code changes
- **US1 (Phase 3)**: No blocking prerequisites beyond Phase 2 — start immediately
- **US2 (Phase 4)**: No dependencies on US1 — fully independent removal task; start immediately
- **US3 (Phase 5)**: No dependencies on US1 or US2 — fully independent label task; start immediately
- **US4 (Phase 6)**: No dependencies — start immediately after Phase 2
- **US5 (Phase 7)**: No dependencies — start immediately after Phase 2
- **Polish (Phase 8)**: Depends on all prior phases

### User Story Dependencies

All 5 user stories are independent of each other — they touch different parts of `page.tsx` with no overlapping state or handlers. They CAN be implemented in parallel by a single developer (sequentially) or by multiple developers simultaneously.

### Within Each User Story

- Tests MUST be written first (TDD per Constitution Principle IV)
- Implementation tasks are sequential within each story
- Each story is independently testable after its implementation tasks complete

### Parallel Opportunities

- T004 + T005 can run in parallel (different test cases, same file — write both together)
- T010 + T014 + T015 + T019 + T020 + T023 can all be written in parallel (all test tasks across all stories — different `describe` blocks)
- T011 + T012 + T013 are sequential (T013 cleans up structure from T011)
- T016 + T017 + T018 can be tackled sequentially within US3
- T021 + T022 are sequential within US4
- T024 + T025 are sequential within US5
- T026 + T027 + T028 can run in parallel (Polish)

---

## Parallel Example: All Test Tasks

```bash
# Write all test cases first (across all user stories):
T004: Save Day composite mutation — 3 meal saves + 1 day plan save
T005: Save Day empty-day validation — no API calls
T010: FoodMealsTab saved sub-tab — no "Day Plans" section
T014: Exercise view labels — labelled fields present
T015: Exercise view labels — null fields omitted
T019: Add exercise state mutation — appends with defaults
T020: Remove exercise state mutation — filters correct index
T023: Split builder score debounce — scoreSplit called after 300ms
```

---

## Implementation Strategy

### MVP First (User Story 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (read-only)
3. Complete Phase 3: US1 — Save Day composite action
4. Complete Phase 4: US2 — Tab content cleanup
5. **STOP and VALIDATE**: Scenarios 1 + 2 from quickstart.md
6. Deploy/demo: users can now save generated meal days and find them in the right places

### Incremental Delivery

1. Setup + Foundational → understand current state
2. US1 → Save Day creates both records → **Demo: meal save flow works**
3. US2 → Tab content correct → **Demo: navigation makes sense**
4. US3 → Labels on exercise fields → **Demo: workout plan readable**
5. US4 → Add/remove exercises → **Demo: generated plan is editable**
6. US5 → Live score in split builder → **Demo: split building has feedback**

---

## Notes

- All changes are in `frontend/app/(app)/recommendations/page.tsx` (single file)
- No backend changes, no API changes, no schema migrations
- The `["custom-meals"]` query key invalidation from US1 automatically makes day-planner-sourced meals appear in the Saved Meals tab — no special rendering logic needed for US2 beyond the section removal
- The `Promise.allSettled` pattern (vs `Promise.all`) in T009 ensures partial meal save failures don't hide the day plan success
- Constitution Principle IV: ALL test tasks (T004, T005, T010, T014, T015, T019, T020, T023) are MANDATORY
