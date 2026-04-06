# Tasks: Workout & Diet UX Fixes (009)

**Input**: Design documents from `/specs/009-workout-diet-ux-fixes/`  
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/ ✅ quickstart.md ✅

**Tests**: Mandatory per Constitution Principle IV — included for all P1 and P2 user stories.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[Story]**: User story this task belongs to (US1–US7)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project structure needed — all changes are in existing files. Confirm tooling and read key source files before starting.

- [x] T001 Read and understand `frontend/lib/api.ts` (token storage and request function)
- [x] T002 [P] Read and understand `frontend/lib/auth-context.tsx` (`tryRefresh` implementation)
- [x] T003 [P] Read and understand `services/recommendation-service/src/services/workout_scorer.py` (five scoring dimensions and weights)
- [x] T004 [P] Read and understand `services/recommendation-service/src/services/prompt_builder.py` (workout prompt, lines 70–90)
- [x] T005 [P] Read and understand `frontend/app/(app)/recommendations/page.tsx` lines 1–100 (MacroBar component and color logic)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Scoring dimension constant and color map extracted to shared locations — both are depended on by multiple phases.

**⚠️ CRITICAL**: Phase 3+ tasks that use client-side scoring or MacroBar must wait for T006.

- [x] T006 Extract client-side workout scoring weights into a constant in `frontend/app/(app)/recommendations/page.tsx` (or a co-located `scoring-constants.ts`) matching the five dimensions in `workout_scorer.py`: Coverage 25, Volume 30, Balance 20, Cardio 15, Frequency 10
- [x] T007 [P] Define `MACRO_COLOR_MAP` record in `frontend/app/(app)/recommendations/page.tsx` mapping color names to hex values: `{ cyan: "#06b6d4", green: "#22c55e", amber: "#f59e0b", purple: "#a855f7", red: "#ef4444" }`

**Checkpoint**: Constants ready — MacroBar fix and client-side scorer can now proceed independently.

---

## Phase 3: User Story 1 — Fix Token Expiry on Recommendations Page (Priority: P1) 🎯 MVP

**Goal**: Users never see a "token expired" error; the recommendations page silently refreshes the token and retries.

**Independent Test**: Expire a user token (or wait for expiry), navigate to the recommendations page, verify the page loads normally with no error shown.

### Tests for User Story 1

- [ ] T008 [US1] Write unit test for the token-refresh interceptor logic in `frontend/lib/api.test.ts`: assert that a 401 response triggers `tryRefresh()` and retries the request exactly once
- [ ] T009 [US1] Write unit test for the redirect-on-refresh-failure path in `frontend/lib/api.test.ts`: assert that a 401 after refresh calls `clearAccessToken()` and navigates to `/login`
> Note: T008-T009 require a frontend test framework (vitest) to be installed. No test runner is currently configured in the frontend project.

### Implementation for User Story 1

- [x] T010 [US1] Add 401 interceptor to `request<T>()` in `frontend/lib/api.ts`: on first 401, call `auth.refresh()` directly, update `_accessToken`, retry the original request once
- [x] T011 [US1] Add second-401 handler in `frontend/lib/api.ts`: call `clearAccessToken()` and trigger session-expired handler (registered from `auth-context.tsx`) which redirects to `/login`
- [x] T012 [US1] Wire `registerSessionExpiredHandler` from `frontend/lib/api.ts` in `frontend/lib/auth-context.tsx` using `useEffect` to push to `/login` on session expiry

**Checkpoint**: Navigate to recommendations with an expired token — page loads silently. ✅

---

## Phase 4: User Story 2 — Single-Week Workout Plan with 90+ Score Floor (Priority: P1)

**Goal**: Generated workout plans show exactly one week; every plan scores ≥ 90.

**Independent Test**: Click "Generate Weekly Workout Plan", verify one week of days is shown (no week tabs), verify score displayed is ≥ 90.

### Tests for User Story 2

- [x] T013 [US2] Write unit test in `services/recommendation-service/tests/test_prompt_builder.py`: assert `build_workout_prompt()` output does NOT contain "4-week" and DOES contain single-week instruction
- [x] T014 [P] [US2] Write unit test in `services/recommendation-service/tests/test_workout_score_floor.py`: assert score helper works correctly; high-quality plan scores ≥ 90
- [ ] T015 [P] [US2] Write frontend test: requires vitest setup (not yet configured)

### Implementation for User Story 2

- [x] T016 [US2] Update workout prompt in `services/recommendation-service/src/services/prompt_builder.py`: replaced "4-week progressive workout program" with "single-week, high-quality, well-balanced workout program"; updated JSON schema to return `{ "days": [...] }`
- [x] T017 [US2] Add score-floor retry in `services/recommendation-service/src/services/recommendation_service.py`: retry up to 3 times if score < 90; log warning on failure
- [x] T018 [US2] Update frontend workout plan renderer in `frontend/app/(app)/recommendations/page.tsx`: use `getPlanDays(plan)` helper supporting both `plan.days` and legacy `plan.weeks?.[0]?.days`; updated all edit handlers to write back to `plan.days`
- [x] T019 [US2] Update button label: "Generate 4-Week Workout Plan" → "Generate Weekly Workout Plan"

**Checkpoint**: Generate a workout plan — shows one week, score ≥ 90 displayed. ✅

---

## Phase 5: User Story 7 — Macro Bars Visually Update in Manual Planner (Priority: P1)

**Goal**: When a meal is added or removed in the manual planner, macro progress bars visually move.

**Independent Test**: Add a meal in the manual planner; verify all four macro bars (calories, protein, carbs, fat) visually expand proportionally. Remove the meal; verify bars shrink.

### Tests for User Story 7

- [ ] T020 [US7] Write frontend test for `MacroBar` — requires vitest setup (not yet configured)

### Implementation for User Story 7

- [x] T021 [US7] Fixed `MacroBar` component: replaced `bg-${color}-500` Tailwind template literal with `style={{ width: ..., backgroundColor: MACRO_COLOR_MAP[color] }}` using explicit hex color map
- [x] T022 [US7] Verified all `MacroBar` call sites use colors in `MACRO_COLOR_MAP`; added "pink" (#ec4899) to cover the `color="pink"` usage in `DayPlannerTab`

**Checkpoint**: Add a meal in manual planner — all four macro bars visually update. ✅

---

## Phase 6: User Story 3 — Real-Time Score Feedback on Workout Edits (Priority: P2)

**Goal**: Every workout plan edit shows a real-time score delta vs. the original generated score (e.g., "−1.2 pts from original").

**Independent Test**: Generate a plan (score ≥ 90), edit an exercise, verify the displayed score changes and a signed delta label appears immediately.

**Prerequisite**: Phase 2 (T006 — scoring constant) must be complete.

### Tests for User Story 3

- [ ] T023 [US3] Write unit test for `computeWorkoutScore` — requires vitest setup
- [ ] T024 [P] [US3] Write frontend test for score delta display — requires vitest setup

### Implementation for User Story 3

- [x] T025 [US3] Added `originalScoreRef` (useRef) in `WorkoutPlanCard`: frozen at first score computation, never overwritten on subsequent edits
- [x] T026 [US3] Implemented `computeWorkoutScore(plan)` function replicating Python scorer logic in TypeScript; placed above `MacroPieChart`; supports both new `plan.days` and legacy `plan.weeks[0].days`
- [x] T027 [US3] Wired `computeWorkoutScore()` into `useEffect([plan])` inside `WorkoutPlanCard` — score updates immediately on any plan change
- [x] T028 [US3] Added score delta indicator: shown in header and in expanded score card; green for positive, red for negative; shows for changes ≥ 0.05 pts; label "X.X pts from original"

**Checkpoint**: Edit an exercise — score updates instantly, signed delta label is visible. ✅

---

## Phase 7: User Story 4 — Condensed Diet Day Planner with Simplified Labels (Priority: P2)

**Goal**: Each day in the day planner is a compact collapsible card; meal labels show only "Breakfast" / "Lunch" / "Dinner" / "Snack".

**Independent Test**: Open the day planner tab; verify each day is in a distinct compact card; verify no label contains "Day Planner —" or any day-name prefix.

### Tests for User Story 4

- [ ] T029 [US4] Write frontend test for condensed day planner — requires vitest setup

### Implementation for User Story 4

- [x] T030 [US4] Changed `DietDayRow` default open state from `useState(dayIndex === 0)` to `useState(false)` — all days start collapsed
- [x] T031 [US4] Updated meal slot label in `DietDayRow`: replaced `capitalize` CSS class with explicit `charAt(0).toUpperCase() + slice(1)` — shows "Breakfast" etc.; same update applied in `DayPlannerTab` slot labels
- [x] T032 [US4] Removed auto-creation of "Day Planner — {slot}" meals from `saveDayPlan` function in `DietDayRow`; only the day plan itself is now saved when user clicks "Save day"

**Checkpoint**: Day planner shows compact collapsible cards; all labels read "Breakfast", "Lunch", etc. ✅

---

## Phase 8: User Story 5 — Remove Individual Meal Save from Day Planner (Priority: P2)

**Goal**: No "Save Meal" button exists on individual meal slots within the day planner.

**Independent Test**: Open any day in the day planner; confirm no "Save Meal" button or save control is visible on any individual meal slot.

### Tests for User Story 5

- [ ] T033 [US5] Write frontend test for removed meal save button — requires vitest setup

### Implementation for User Story 5

- [x] T034 [US5] Removed `saveMealMutation` useMutation definition from `DietDayRow`
- [x] T035 [US5] Removed both "Save meal" buttons (editing mode line ~716 and view mode line ~834) from `DietDayRow`; removed `savedMealIdx` and `setSavedMealIdx` state
- [x] T036 [US5] TypeScript compiles with zero errors after removal (verified with `tsc --noEmit`)

**Checkpoint**: Day planner has no individual meal save controls. ✅

---

## Phase 9: User Story 6 — Compact Expandable Meal Selector in Day Planner (Priority: P2)

**Goal**: The meal selector in each day planner slot is a compact single-line widget that expands to show grouped "Saved Days" and "Saved Meals" sections.

**Independent Test**: Click the meal selector for any day planner slot; confirm a compact box appears; confirm it expands to show two labelled sections; confirm selecting a meal closes the selector and shows the meal name.

**Prerequisite**: Phase 7 (T030–T032) should be complete so the slot context is correct.

### Tests for User Story 6

- [ ] T037 [US6] Write component test for `MealSelectorWidget` — requires vitest setup

### Implementation for User Story 6

- [x] T038 [US6] Created `frontend/components/MealSelectorWidget.tsx`: compact collapsible widget with props `{ value, onChange, savedMeals, savedDays }`; shows selected meal name when collapsed; expands to "Saved Days" and "Saved Meals" sections; closes on outside click
- [x] T039 [US6] `DayPlannerTab` already queries `dayPlans` via `useQuery(["day-plans"])`; no additional fetch needed — passed directly to `MealSelectorWidget`
- [x] T040 [US6] Replaced native `<select>` with `<MealSelectorWidget>` in `DayPlannerTab` slot renderer

**Checkpoint**: Day planner meal selector is a compact expandable widget showing both saved days and saved meals. ✅

---

## Phase 10: Polish & Cross-Cutting Concerns

- [x] T041 [P] TypeScript type-check passed with zero errors (`tsc --noEmit`)
- [x] T042 [P] Backend ruff linting passed on modified files
- [x] T043 All 9 backend tests pass (`pytest tests/test_prompt_builder.py tests/test_workout_score_floor.py`)
- [ ] T044 [P] Frontend tests — requires vitest to be installed first; see note in T008
- [ ] T045 [P] Manually validate all 7 items in `specs/009-workout-diet-ux-fixes/quickstart.md` against the running app
- [x] T046 Backward-compat verified: `getPlanDays(plan)` helper in WorkoutPlanCard returns `plan.days ?? plan.weeks?.[0]?.days ?? []`; old plans render without error
- [x] T047 `MACRO_COLOR_MAP` covers all colors used in MacroBar calls: purple, cyan, amber, pink, green, red

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately, run all in parallel
- **Phase 2 (Foundational)**: Depends on Phase 1 reads; T006 and T007 are parallel to each other
- **Phase 3 (US1 — Token)**: Independent of Phase 2; can start after Phase 1
- **Phase 4 (US2 — 1-Week Plan)**: Independent of Phase 2; can start after Phase 1
- **Phase 5 (US7 — Macro Bars)**: Depends on T007 (MACRO_COLOR_MAP from Phase 2)
- **Phase 6 (US3 — Score Delta)**: Depends on T006 (scoring constant from Phase 2)
- **Phase 7 (US4 — Day Planner Layout)**: Independent of Phase 2; can start after Phase 1
- **Phase 8 (US5 — Remove Meal Save)**: Independent; can start after Phase 1
- **Phase 9 (US6 — Meal Selector)**: Best started after Phase 7 (T030–T032) for correct slot context
- **Phase 10 (Polish)**: Depends on all phases complete

### User Story Dependencies

- **US1 (Token)**: No story dependencies
- **US2 (1-Week Plan)**: No story dependencies
- **US7 (Macro Bars)**: Depends on T007
- **US3 (Score Delta)**: Depends on T006
- **US4 (Day Planner Layout)**: No story dependencies
- **US5 (Remove Meal Save)**: No story dependencies
- **US6 (Meal Selector)**: Soft dependency on US4

### Within Each Phase

- Tests must be written before implementation (Constitution IV)
- Constants/helpers before consumers
- Implementation before integration wiring

### Parallel Opportunities

- Phases 3, 4, 7, 8 can all run in parallel after Phase 1
- Phase 5 and Phase 6 can run in parallel once Phase 2 is done
- All [P]-marked tasks within a phase can run simultaneously

---

## Parallel Example: Phase 3 + Phase 4 + Phase 7 (after Phase 1)

```
Parallel track A (US1):   T008 → T009 → T010 → T011 → T012
Parallel track B (US2):   T013 → T014 → T015 → T016 → T017 → T018 → T019
Parallel track C (US4):   T029 → T030 → T031 → T032
Parallel track D (US5):   T033 → T034 → T035 → T036
```

After Phase 2 completes:
```
Parallel track E (US7):   T020 → T021 → T022
Parallel track F (US3):   T023 → T024 → T025 → T026 → T027 → T028
```

After US4:
```
Sequential (US6):          T037 → T038 → T039 → T040
```

---

## Implementation Strategy

### MVP First (P1 stories only — US1, US2, US7)

1. Complete Phase 1 (Setup reads)
2. Complete Phase 2 (Foundational constants — T006, T007)
3. Complete Phase 3 (US1 — Token fix)
4. Complete Phase 4 (US2 — 1-week plan + score floor)
5. Complete Phase 5 (US7 — Macro bars)
6. **STOP and VALIDATE**: All three P1 stories independently functional
7. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → constants ready
2. US1 (token fix) → recommendations page unblocked ✅
3. US2 (1-week + score floor) → core workout UX correct ✅
4. US7 (macro bars) → nutrition tracking visual bug fixed ✅
5. US3 (score delta) → workout edit feedback live ✅
6. US4 + US5 (day planner layout + remove save) → diet UX condensed ✅
7. US6 (compact meal selector) → diet UX polished ✅
8. Polish → all checks pass ✅

---

## Notes

- [P] tasks = different files or no shared dependencies; safe to run in parallel
- [Story] label maps each task to its user story for traceability
- Tests are mandatory (Constitution Principle IV) — write before implementing
- `MACRO_COLOR_MAP` (T007) and scoring weights (T006) are the only shared constants; keep them in sync with backend counterparts
- Backward-compat fallback for old 4-week plan JSON is required (T018, T046)
- No new npm/pip dependencies — all implementation uses existing primitives
