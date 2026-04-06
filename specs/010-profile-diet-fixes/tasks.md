# Tasks: Profile & Diet Fixes (010)

**Input**: Design documents from `/specs/010-profile-diet-fixes/`  
**Prerequisites**: plan.md ✅ spec.md ✅ research.md ✅ data-model.md ✅ contracts/ ✅ quickstart.md ✅

**Tests**: Mandatory per Constitution Principle IV — included for all P1 and P2 user stories.

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[Story]**: User story this task belongs to (US1–US6)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Read key source files before starting — all changes target existing files.

- [x] T001 Read `frontend/components/nav.tsx` (sidebar structure, navItems array, Sign Out button placement)
- [x] T002 [P] Read `frontend/app/(app)/profile/page.tsx` (form schema, mutations, goal/restriction rendering)
- [x] T003 [P] Read `services/user-service/src/models/profile.py` and `services/user-service/src/schemas/user.py` (UserProfile model + ProfileOut/ProfileUpdate schemas)
- [x] T004 [P] Read `services/recommendation-service/src/services/recommendation_service.py` (generate_diet_recommendation function, existing retry pattern for workout)
- [x] T005 [P] Read `frontend/app/(app)/recommendations/page.tsx` lines 849–960 (FoodMealsTab structure, existing queries, saved sub-tab rendering)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add `activity_level` to DB model and schemas — required by US2 (profile save) and US5 (macro accuracy). Must complete before US2 and US5 phases start.

**⚠️ CRITICAL**: US2 and US5 tasks that pass `activity_level` depend on T006–T008.

- [x] T006 Add `activity_level: Mapped[str | None] = mapped_column(String(30))` to `UserProfile` class in `services/user-service/src/models/profile.py`
- [x] T007 [P] Add `activity_level: str | None = None` to both `ProfileOut` and `ProfileUpdate` Pydantic models in `services/user-service/src/schemas/user.py`
- [x] T008 [P] Add `activity_level: string | null` to `UserProfile` TypeScript interface in `frontend/lib/api.ts`

**Checkpoint**: DB model and TS interface updated — US2 and US5 frontend tasks can now proceed.

---

## Phase 3: User Story 2 — Profile Inputs Save Correctly (Priority: P1) 🎯 MVP

**Goal**: Profile form data (including new activity_level field) persists to DB and reloads correctly; save failures show a clear error message.

**Independent Test**: Fill all profile fields including Activity Level, click Save, reload page — all values reappear. Disconnect user-service, try saving — error message appears and form retains values.

### Tests for User Story 2

- [x] T009 [US2] Write pytest test in `services/user-service/src/tests/test_schemas.py`: assert `ProfileUpdate` schema accepts `activity_level: "very_active"` and rejects unknown values; assert `ProfileOut` includes `activity_level` field

### Implementation for User Story 2

- [x] T010 [US2] Add `activity_level` to `profileSchema` zod object in `frontend/app/(app)/profile/page.tsx`: `activity_level: z.enum(["sedentary", "lightly_active", "moderately_active", "very_active", "extra_active"]).optional()`
- [x] T011 [US2] Add Activity Level `<select>` field to profile form grid in `frontend/app/(app)/profile/page.tsx` (after gender select, same styling: `w-full rounded-md bg-white/5 border border-white/10 text-foreground px-3 py-2 text-sm`; options: Sedentary, Lightly Active, Moderately Active, Very Active, Extra Active)
- [x] T012 [US2] Add `activity_level: profile.activity_level ?? undefined` to the `reset({...})` call inside `useEffect([profile, reset])` in `frontend/app/(app)/profile/page.tsx`
- [x] T013 [US2] Add `onError` handler to `updateProfile` useMutation in `frontend/app/(app)/profile/page.tsx`: add `const [saveError, setSaveError] = useState<string | null>(null)` state; set error message on failure; clear on success; display `{saveError && <span className="text-sm text-red-400">{saveError}</span>}` next to the Save button

**Checkpoint**: Save profile with all fields → reloads correctly. Error state visible on failure.

---

## Phase 4: User Story 3 — Goal Buttons Show Selected State (Priority: P1)

**Goal**: Goal buttons display visually distinct active state and persist selection; errors surface to user.

**Independent Test**: Click "Build Muscle", reload — button remains highlighted purple. Verify no silent failure when setGoal API is called.

**Note**: Selected state logic (`goal?.goal_type === g.value`) is already implemented. Root fix is error visibility so the user knows if the save failed.

### Tests for User Story 3

- [x] T014 [US3] Write pytest test in `services/user-service/src/tests/test_schemas.py`: assert `HealthGoalSet` schema accepts valid goal types (`lose_fat`, `build_muscle`, `maintain`, `improve_endurance`, `general_health`) and `HealthGoalOut` includes `goal_type` field

### Implementation for User Story 3

- [x] T015 [US3] Add `onError` handler to `setGoal` useMutation in `frontend/app/(app)/profile/page.tsx`: add `const [goalError, setGoalError] = useState<string | null>(null)` state; show `{goalError && <p className="text-xs text-red-400 mt-1">{goalError}</p>}` below the goal buttons div; clear on success

**Checkpoint**: Click a goal → button highlights immediately. Error visible if API fails.

---

## Phase 5: User Story 4 — Dietary Restriction Buttons Save and Show Selected State (Priority: P1)

**Goal**: Restriction toggles persist, show active state, and pass restrictions to diet generation.

**Independent Test**: Toggle "Vegetarian" → cyan active state shown. Reload → still active. Generate diet → plan contains no meat.

**Note**: Active state logic and diet generation passing are already implemented. Fix is error visibility and verifying the query chain.

### Tests for User Story 4

- [x] T016 [US4] Write pytest test in `services/user-service/src/tests/test_schemas.py`: assert `DietaryRestrictionAdd` schema accepts valid `restriction_type` values and `DietaryRestrictionOut` includes `id`, `restriction_type`, `notes` fields

### Implementation for User Story 4

- [x] T017 [US4] Add `onError` handlers to both `addRestriction` and `removeRestriction` useMutations in `frontend/app/(app)/profile/page.tsx`: add `const [restrictionError, setRestrictionError] = useState<string | null>(null)` state; show `{restrictionError && <p className="text-xs text-red-400 mt-1">{restrictionError}</p>}` below the restrictions div; clear on success of either mutation
- [x] T018 [US4] Verify `FoodMealsTab` in `frontend/app/(app)/recommendations/page.tsx` line ~348 already queries `useQuery({ queryKey: ["restrictions"], queryFn: userApi.getDietaryRestrictions })` and passes result to `generateDiet` — no code change needed if confirmed; add the query if missing

**Checkpoint**: Toggle restriction → cyan active shown. Generate diet → restricted foods absent.

---

## Phase 6: User Story 5 — Diet Recommendations Hit Macro Targets (Priority: P1)

**Goal**: Generated diet plans have day totals within ±10% of macro targets; activity_level drives accurate TDEE calculation.

**Independent Test**: Generate a diet plan → sum Day 1 calories from all meals → value is within ±10% of stated daily target. Repeat for protein, carbs, fat.

### Tests for User Story 5

- [x] T019 [US5] Write pytest tests in `services/recommendation-service/tests/test_diet_macro_retry.py`:
  - `test_validate_diet_macros_pass`: plan where all days within ±10% → returns `True`
  - `test_validate_diet_macros_fail_calories`: day with calories 50% below target → returns `False`
  - `test_validate_diet_macros_fail_protein`: day with protein 20% over target → returns `False`
  - `test_validate_diet_macros_empty_days`: empty days list → returns `True` (vacuously valid)
  - `test_validate_diet_macros_zero_target`: target calories=0 → skips that macro check, returns `True`

### Implementation for User Story 5

- [x] T020 [US5] Add `_validate_diet_macros(plan: dict, macro_targets) -> bool` helper function in `services/recommendation-service/src/services/recommendation_service.py` (per contract in `contracts/diet-generation.md` — checks calories, protein_g, carbs_g, fat_g for each day within ±10%)
- [x] T021 [US5] Wrap LLM call in `generate_diet_recommendation()` with retry loop (up to 3 attempts) in `services/recommendation-service/src/services/recommendation_service.py`: call `_validate_diet_macros(structured, macro_targets)` after each attempt; return on first passing result; log warning if all 3 fail; return best attempt on exhaustion
- [x] T022 [US5] Pass `activity_level: profile?.activity_level ?? "moderately_active"` to `recommendations.calculateMacros({...})` call in `FoodMealsTab` in `frontend/app/(app)/recommendations/page.tsx` (line ~868)
- [x] T023 [US5] Pass `activity_level: profile?.activity_level ?? "moderately_active"` to `recommendations.generateDiet({...})` call in `FoodMealsTab` in `frontend/app/(app)/recommendations/page.tsx` (line ~367)

**Checkpoint**: Generate diet → Day 1 macro totals within ±10% of targets shown. Activity level affects calorie target.

---

## Phase 7: User Story 1 — Profile Navigation Moved Near Sign Out (Priority: P2)

**Goal**: Profile link removed from main content tabs; appears directly above Sign Out button in sidebar.

**Independent Test**: Open app → sidebar shows Dashboard, Scans, Analytics, Plans only (no Profile). Bottom of sidebar shows Profile link above Sign Out button.

### Tests for User Story 1

- [x] T024 [US1] Verify by inspection (no automated test for nav layout): open app after change, confirm Profile absent from top nav items, present above Sign Out

### Implementation for User Story 1

- [x] T025 [US1] Remove `{ href: "/profile", label: "Profile", icon: User }` entry from `navItems` array in `frontend/components/nav.tsx`
- [x] T026 [US1] Add Profile `<Link>` directly above the Sign Out `<Button>` in the bottom section of `frontend/components/nav.tsx`:
  ```tsx
  <Link href="/profile">
    <div className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-all ${pathname.startsWith("/profile") ? "bg-purple-500/20 text-purple-300 border border-purple-500/30" : "text-muted-foreground hover:bg-white/5 hover:text-foreground"}`}>
      <User className="h-4 w-4" />
      Profile
    </div>
  </Link>
  ```

**Checkpoint**: Sidebar shows Profile above Sign Out, not in main nav list.

---

## Phase 8: User Story 6 — Saved Days Visible in "My Saved Meals" Tab (Priority: P2)

**Goal**: "Food & Meals" tab "Saved" sub-tab shows a "Saved Day Plans" section above individual saved meals.

**Independent Test**: Save a day plan in Day Planner → navigate to Food & Meals → Saved sub-tab → "Saved Day Plans" section shows the plan with name and meal slot summary.

### Tests for User Story 6

- [x] T027 [US6] Write pytest test in `services/recommendation-service/tests/test_day_plans.py` (create if not exists): assert `GET /api/recommendations/day-plans` returns only the authenticated user's plans (user-scoped); assert empty list for new user

### Implementation for User Story 6

- [x] T028 [US6] Add `const { data: dayPlans } = useQuery({ queryKey: ["day-plans"], queryFn: recommendations.listDayPlans })` to `FoodMealsTab` in `frontend/app/(app)/recommendations/page.tsx` (after the existing `savedMeals` query)
- [x] T029 [US6] In `FoodMealsTab` saved sub-tab render in `frontend/app/(app)/recommendations/page.tsx`, add a "Saved Day Plans" section above the saved meals section:
  - Show section header `<h3>Saved Day Plans</h3>` only if `(dayPlans ?? []).length > 0`
  - For each day plan: render name, date (if set), and a compact list of entry slot names (`plan.entries.map(e => e.meal_slot).join(" · ")`)
  - Empty state: "No saved day plans yet" if `dayPlans` is empty or undefined
  - Use existing `glass-card`, `p-3`, `text-sm` styling consistent with `SavedMealCard`

**Checkpoint**: Day plan saved in Day Planner tab appears in Food & Meals → Saved → "Saved Day Plans" section.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [x] T030 [P] TypeScript type-check passes with zero errors: `cd frontend && npx tsc --noEmit`
- [x] T031 [P] Backend ruff linting passes on modified files: `cd services/user-service && ruff check src/` and `cd services/recommendation-service && ruff check src/`
- [x] T032 [P] All backend tests pass: `cd services/user-service && python -m pytest src/tests/` and `cd services/recommendation-service && python -m pytest tests/test_diet_macro_retry.py`
- [x] T033 Manually validate all 6 scenarios in `specs/010-profile-diet-fixes/quickstart.md` against the running app

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately, all reads in parallel
- **Phase 2 (Foundational)**: Depends on Phase 1 reads; T006–T008 can run in parallel
- **Phase 3 (US2)**: Depends on Phase 2 (T006–T008 for activity_level)
- **Phase 4 (US3)**: Independent of Phase 2; can start after Phase 1
- **Phase 5 (US4)**: Independent of Phase 2; can start after Phase 1
- **Phase 6 (US5)**: Depends on Phase 2 (T008 for activity_level TS interface)
- **Phase 7 (US1)**: Independent; can start after Phase 1
- **Phase 8 (US6)**: Independent; can start after Phase 1
- **Phase 9 (Polish)**: Depends on all phases complete

### User Story Dependencies

- **US2 (Profile Save)**: Depends on Phase 2 (activity_level schema)
- **US3 (Goal Buttons)**: No story dependencies
- **US4 (Restrictions)**: No story dependencies
- **US5 (Macro Accuracy)**: Depends on Phase 2 (activity_level TS interface)
- **US1 (Profile Nav)**: No story dependencies
- **US6 (Saved Days)**: No story dependencies

### Parallel Opportunities

After Phase 1, these groups can run concurrently:
- **Track A**: Phase 2 (T006–T008) → then Phase 3 (US2) and Phase 6 (US5)
- **Track B**: Phase 4 (US3) — independent
- **Track C**: Phase 5 (US4) — independent
- **Track D**: Phase 7 (US1) — independent
- **Track E**: Phase 8 (US6) — independent

---

## Parallel Execution Example

```
After Phase 1 reads complete:

Track A:  T006 → T007/T008 [parallel] → T009-T013 (US2) → T019-T023 (US5)
Track B:  T014 → T015 (US3)
Track C:  T016 → T017-T018 (US4)
Track D:  T024 → T025-T026 (US1)
Track E:  T027 → T028-T029 (US6)

All tracks → Phase 9 Polish
```

---

## Implementation Strategy

### MVP First (P1 stories: US2, US3, US4, US5)

1. Complete Phase 1 (Setup reads)
2. Complete Phase 2 (Foundational — activity_level)
3. Complete Phase 3 (US2 — profile save)
4. Complete Phase 4 (US3 — goal buttons)
5. Complete Phase 5 (US4 — dietary restrictions)
6. Complete Phase 6 (US5 — macro accuracy)
7. **STOP and VALIDATE**: All P1 stories independently functional
8. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → activity_level schema ready
2. US2 (profile save) → form persists all fields including activity_level ✅
3. US3 (goal buttons) → selected state visible on reload ✅
4. US4 (dietary restrictions) → toggles persist, diet respects them ✅
5. US5 (macro accuracy) → diet plans hit targets within ±10% ✅
6. US1 (nav relocation) → profile near Sign Out ✅
7. US6 (saved days) → day plans visible in My Saved Meals ✅
8. Polish → all checks pass ✅

---

## Notes

- [P] tasks = different files or no shared dependencies; safe to run in parallel
- [Story] label maps each task to its user story for traceability
- Tests are mandatory (Constitution Principle IV) — write before implementing
- US3 and US4 selected states are already implemented in UI code — root fix is error visibility from the mutations
- US4 dietary restriction passing to `generateDiet` is already implemented — verify it's present, add if missing
- `activity_level` defaults to `"moderately_active"` in frontend when profile field is null (no breaking change)
- Backward-compat: `activity_level: null` in DB is valid — existing users unaffected until they save a value
