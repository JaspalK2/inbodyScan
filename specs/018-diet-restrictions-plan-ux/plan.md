# Implementation Plan: Fix Dietary Restriction Enforcement & Redesign Diet Plan Saved Meals UX

**Branch**: `018-diet-restrictions-plan-ux` | **Date**: 2026-04-06 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/018-diet-restrictions-plan-ux/spec.md`

## Summary

**US1 (P0 — Safety)**: Fix a data-quality defect in `foods.json` where 6 food items containing meat, fish, or seafood are incorrectly flagged `vegetarian: true` and `vegan: true`, causing them to bypass the dietary restriction filter. The filter logic and data-passing flow are both correct; only the food data needs correction. Add a dedicated test file to prevent regression.

**US2 (P1 — UX)**: Replace the manual per-day "Save day" button with auto-save of all 7 days on plan generation. Redesign the "My Saved Meals" section to display generated plans as date-stamped collapsible plan blocks (grouped by recommendation ID stored in `day_plans.notes`), each expandable to reveal Day 1–7 rows, each day further expandable to show meal-level macros from `items_snapshot`.

**No schema changes required.** All fixes are in `foods.json`, `test_diet_restrictions.py` (new), and `frontend/app/(app)/recommendations/page.tsx`.

---

## Technical Context

| Concern | Detail |
|---------|--------|
| Backend language | Python 3.13 |
| Frontend | TypeScript 5.x / Next.js 15, React 18, TanStack Query v5, Tailwind CSS, shadcn/ui |
| Data file | `services/recommendation-service/src/data/foods.json` |
| Filter logic | `services/recommendation-service/src/services/diet_engine.py::_filter_foods` |
| Test file | `services/recommendation-service/tests/test_diet_restrictions.py` (new) |
| Frontend page | `frontend/app/(app)/recommendations/page.tsx` |
| Existing save API | `POST /api/recommendations/day-plans` (unchanged) |
| Grouping key | `day_plans.notes` stores recommendation_id UUID |
| New dependencies | None |

---

## Constitution Check

| Principle | Gate | Status |
|-----------|------|--------|
| I. Extensibility | No existing interfaces modified; new test file only; foods.json data fix is additive correction | ✅ |
| II. Algorithm Efficiency | No algorithm changes; `_filter_foods` is O(n) per slot; no new queries | ✅ |
| III. License Compliance | No new dependencies | ✅ |
| IV. Mandatory Tests | New `test_diet_restrictions.py` with parametrized restriction tests; frontend Vitest tests for auto-save flow | ✅ |
| V. UI/UX Consistency | Redesigned UI uses existing shadcn/ui components and Tailwind tokens; no new UI primitives introduced | ✅ |
| Security | No PII exposure; user-scoped data access unchanged; auto-save calls use existing authenticated endpoints | ✅ |

---

## File Structure

```
services/recommendation-service/
  src/data/foods.json                          ← fix 6 incorrect restriction flags
  tests/test_diet_restrictions.py              ← NEW: restriction enforcement tests

frontend/app/(app)/recommendations/page.tsx    ← remove "Save day" button, add auto-save,
                                                  redesign FoodMealsTab saved plans section
```

---

## Complexity Tracking

| Item | Complexity | Justification |
|------|-----------|---------------|
| foods.json data fix | Low | 6 targeted bool corrections |
| test_diet_restrictions.py | Low | Pattern mirrors existing test_diet_engine.py tests |
| Auto-save on generation | Medium | 7 sequential API calls in mutation onSuccess; must handle partial failure gracefully |
| Saved plans UI redesign | Medium | Group-by rec_id + nested expand/collapse; uses existing DayPlanCard pattern |
| Remove "Save day" button | Low | Delete function + JSX; invalidate existing cache keys |

---

## Phase 1: US1 — Data Fix (P0 Safety)

### Step 1: Correct foods.json restriction flags

**File**: `services/recommendation-service/src/data/foods.json`

Fix the `restrictions` object for these 6 entries (change `vegetarian` and `vegan` from `true` to `false`):

1. `Chicken, thighs, frozen, breaded, reheated`
2. `ON THE BORDER, soft taco with ground beef, cheese and lettuce`
3. `Fish oil, salmon`
4. `Snacks, shrimp cracker`
5. `APPLEBEE'S, Double Crunch Shrimp`
6. `DENNY'S, golden fried shrimp`

### Step 2: Add test_diet_restrictions.py

**File**: `services/recommendation-service/tests/test_diet_restrictions.py` (new)

Tests:
- `test_vegetarian_plan_contains_no_meat_or_fish` — generate plan with `restrictions=["vegetarian"]`, assert no item name matches known meat/fish names from foods.json
- `test_vegan_plan_contains_no_animal_products` — generate plan with `restrictions=["vegan"]`, assert no non-vegan items
- `test_multiple_restrictions_satisfied_simultaneously` — generate with `["vegetarian", "gluten_free"]`, assert both satisfied
- `test_no_restrictions_generates_full_plan` — empty restrictions list, plan generates with ≥1 item per day

### Step 3: Run tests

```bash
cd services/recommendation-service
python3 -m pytest tests/test_diet_restrictions.py tests/test_diet_engine.py -v
```

All tests must pass.

---

## Phase 2: US2 — Auto-Save & UI Redesign (P1)

### Step 4: Auto-save all 7 days on generation (frontend)

**File**: `frontend/app/(app)/recommendations/page.tsx`

In the `generateDietMutation` (currently around line 369), add an `onSuccess` callback that:
1. Receives the `DietRecommendationOut` response (has `.id` and `.structured_plan.days`)
2. Calls `recommendations.createDayPlan()` for each of the 7 days, passing:
   - `name`: `"AI Plan ${dateStr} (Day ${day.day})"`
   - `plan_date`: today's date
   - `notes`: `rec.id` (recommendation ID — grouping key)
   - `entries`: array of 4 meal slots with `meal_slot`, `custom_meal_name`, macro totals, and `items_snapshot`
3. After all 7 saves, invalidates `["day-plans"]` query
4. Show a brief "Plan saved!" success indicator (not a per-day button)

Remove `saveDayPlan` function and the "Save day" `<Button>` from `DietDayRow`.

### Step 5: Redesign FoodMealsTab saved plans section

**File**: `frontend/app/(app)/recommendations/page.tsx` — `FoodMealsTab` component

Replace the current flat list of saved day plan cards with a grouped view:

1. Group `dayPlans` array by `notes` field (recommendation_id). Each group = one plan block.
2. Sort groups by the `created_at` of their earliest entry, newest first.
3. For each group, render a `<PlanBlock>` (inline component):
   - **Collapsed**: Shows date label (formatted from `created_at`) + goal type/calorie summary + expand chevron + delete button
   - **Expanded**: Shows 7 `<DayRow>` components sorted by day number extracted from `name`
4. Each `DayRow`:
   - **Collapsed**: Shows "Day N" + day-level macro totals (sum of entry `calories_kcal` etc.) + expand chevron
   - **Expanded**: Shows each `entry` as a `<MealRow>` with meal slot name, macro totals, and collapsed `items_snapshot` list

Delete button on a plan block calls `deleteDayPlan` for all 7 day IDs in the group, then invalidates `["day-plans"]`.

### Step 6: Frontend tests

**File**: `frontend/__tests__/recommendations/autoSavePlan.test.ts` (new)

Tests:
- `auto-saves 7 days on successful generation` — mock generateDiet returning a rec with 7 days; assert createDayPlan called 7 times with correct notes=rec.id
- `does not auto-save if generation fails` — mock failure; assert createDayPlan not called
- `groups day plans by notes field` — render FoodMealsTab with mock dayPlans sharing a notes value; assert one plan block rendered with 7 children

### Step 7: Run full test suite

```bash
# Backend
cd services/recommendation-service
python3 -m pytest tests/ -v

# Frontend
cd frontend
npx vitest run __tests__/
```

---

## Implementation Order

```
T001 Fix foods.json (6 entries)
T002 Write test_diet_restrictions.py
T003 Run backend tests — all must pass
T004 Remove "Save day" button from DietDayRow
T005 Add auto-save to generateDietMutation onSuccess
T006 Redesign FoodMealsTab saved plans section (PlanBlock grouping)
T007 Write frontend autoSavePlan.test.ts
T008 Run all tests
```

T001 and T002 are independent (parallel). T003 depends on both. T004 and T005 are independent (parallel). T006 depends on T004. T007 depends on T005+T006.
