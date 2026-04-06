# Implementation Plan: Fix Diet Plan Rendering Crash

**Branch**: `014-fix-diet-meal-render` | **Date**: 2026-04-06 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/014-fix-diet-meal-render/spec.md`

## Summary

The new algorithmic diet engine (feature 013) produces a different meal schema than what the frontend `DietDayRow` component expects. The frontend crashes at line 759 of `page.tsx` because `meal.meal` is `undefined` — the new engine uses `meal_name` instead. Additional schema mismatches exist for food item lists (`items` vs `foods`) and macro fields (`meal_totals` object vs flat fields). The fix normalises the meal data at the point of rendering (and at the point of use in helper functions), fully preserving backwards compatibility with old LLM-format plans.

## Technical Context

**Language/Version**: TypeScript 5.x / Next.js 15 (Turbopack)  
**Primary Dependencies**: React 18, TanStack Query v5, existing Tailwind CSS + shadcn/ui component library  
**Storage**: No schema change — plan JSON is already stored in `structured_plan` / `edited_plan` columns; fix is rendering-only  
**Testing**: Jest / React Testing Library (frontend unit tests); existing pytest suite unaffected  
**Target Platform**: Web browser (Next.js App Router)  
**Project Type**: Web application (frontend-only fix)  
**Performance Goals**: No regression — render time unchanged  
**Constraints**: Must not break old LLM-format plans already stored in the database; no backend changes  
**Scale/Scope**: One component file (`frontend/app/(app)/recommendations/page.tsx`); ~8 targeted line changes

## Constitution Check

| Principle | Gate for this feature | Status |
|-----------|----------------------|--------|
| I. Extensibility | Normalisation helper must be a named function, not an inline expression, so future schema versions can be handled by extending it | ✓ PASS — plan includes `normaliseMeal()` helper |
| II. Algorithm Efficiency | All normalisations are O(1) per meal or O(n) per item list — no nested loops over large data | ✓ PASS |
| III. License Compliance | No new dependencies introduced | ✓ PASS |
| IV. Mandatory Test Coverage | Unit tests required for the `normaliseMeal` helper covering both old and new schema inputs | ✓ PASS — test tasks included |
| V. UI/UX Consistency | No visual change to the rendered output; existing design tokens used throughout | ✓ PASS |

## Project Structure

### Documentation (this feature)

```text
specs/014-fix-diet-meal-render/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── contracts/           # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
frontend/
├── app/(app)/recommendations/
│   └── page.tsx          ← PRIMARY CHANGE: DietDayRow + helpers normalised
└── __tests__/recommendations/
    └── normaliseMeal.test.ts   ← NEW: unit tests for normalisation helper
```

---

## Phase 0: Research

### Decision 1: Where to normalise — frontend vs backend

**Decision**: Normalise in the **frontend rendering layer**, not in the backend.

**Rationale**: The backend already stores the new schema in the DB. Changing it would require a migration for all existing rows, or maintaining two code paths in the engine. The frontend already uses `any` types for the plan payload and is the only consumer that needs this mapped. A small `normaliseMeal()` helper at the top of `DietDayRow` is the minimal-blast-radius fix.

**Alternatives considered**:
- Normalise in `diet_engine.py` output to match old schema — rejected: would break the clean new schema and create a permanent inconsistency between what is stored and what the engine produces
- Add a data migration to rewrite stored plans — rejected: overkill for a display bug; stored plans may be in `edited_plan` (user-modified) and should not be touched

### Decision 2: Normalisation approach

**Decision**: Introduce a pure function `normaliseMeal(meal: any): NormalisedMeal` at the top of `DietDayRow` that maps both schemas to a single internal structure used throughout the component.

**Rationale**: Single normalisation point — all downstream code (name display, food list, macro display, save flow, edit flow) reads from the normalised object. This removes scattered `meal.meal ?? meal.meal_name` expressions across 8+ call sites and keeps the fix to one function.

**Internal `NormalisedMeal` shape**:
```ts
{
  mealLabel: string           // "Breakfast" (capitalised)
  mealSlot: string            // "breakfast" (lower, used for day-plan save)
  foods: string[]             // ["Oats rolled 93g", ...]
  calories: number
  protein_g: number
  carbs_g: number
  fat_g: number
  fiber_g: number
  _mf?: { c: number; p: number; cb: number; f: number }[]  // per-item macro cache
}
```

**Mapping rules**:
- `mealLabel`: `meal.meal_name` → already capitalised; `meal.meal` → capitalise first char; fallback `"Meal"`
- `mealSlot`: `meal.meal` if present; else `(meal.meal_name ?? "").toLowerCase()`
- `foods`: if `meal.foods` (string[]) present, use as-is; else if `meal.items` (object[]) present, map each to `"${item.food_name} ${item.grams}g"`
- `calories`: `meal.calories ?? meal.meal_totals?.calories ?? 0`
- `protein_g`: `meal.protein_g ?? meal.meal_totals?.protein_g ?? 0`
- `carbs_g`: `meal.carbs_g ?? meal.meal_totals?.carbs_g ?? 0`
- `fat_g`: `meal.fat_g ?? meal.meal_totals?.fat_g ?? 0`
- `fiber_g`: `meal.fiber_g ?? meal.meal_totals?.fiber_g ?? 0`

### Decision 3: Totals computation fix

**Decision**: Update the `totals` reducer at line 641 to read from the normalised meal object, so the day-level calorie summary also works for new-format plans.

**Rationale**: The reducer currently reads `m.calories`, `m.protein_g`, etc. directly. With new-format plans these are `undefined`, so the day header shows "0 kcal" even if content is present.

---

## Phase 1: Contracts

### UI Rendering Contract

The `DietDayRow` component accepts a `day` object where `day.meals` is an array of meal objects in **either** the old LLM schema or the new algorithmic schema. After normalisation, the component MUST display:

| Field | Old schema source | New schema source | Fallback |
|-------|------------------|------------------|----------|
| Meal label | `meal.meal` (capitalised) | `meal.meal_name` | `"Meal"` |
| Food list (display) | `meal.foods` string[] | `meal.items[].food_name + grams` | `[]` |
| Calories | `meal.calories` | `meal.meal_totals.calories` | `0` |
| Protein | `meal.protein_g` | `meal.meal_totals.protein_g` | `0` |
| Carbs | `meal.carbs_g` | `meal.meal_totals.carbs_g` | `0` |
| Fat | `meal.fat_g` | `meal.meal_totals.fat_g` | `0` |

The `mealSlot` value used when saving to day plans (`saveDayPlan`) MUST be the lowercase slot name (e.g. `"breakfast"`), derived from whichever field is available.

### No API contract changes

No backend endpoints are added, removed, or modified. The fix is purely in the frontend rendering layer.

---

## Phase 1: Quickstart

### Scenario 1 — New algorithmic plan renders correctly

1. Generate a diet plan (POST `/api/recommendations/diet/generate`)
2. Navigate to Recommendations → Diet tab
3. Expand Day 1 → Breakfast, Lunch, Dinner, Snack all visible with meal names
4. Calorie and macro totals shown per meal and in the day header

### Scenario 2 — Old LLM plan still renders correctly

1. Retrieve an old plan from DB (or use the test fixture with `meal.meal: "breakfast"`)
2. Navigate to Diet tab
3. All meals render correctly — identical visual output to before this fix

### Scenario 3 — Editing mode works for new-format plan

1. Enter editing mode on a new algorithmic plan
2. Food items displayed as formatted strings ("Chicken breast tenders 45g")
3. Remove food button works; macro totals update
4. Food search → add food → totals update correctly

### Scenario 4 — Save day plan works for new-format plan

1. Expand Day 1, click "Save day"
2. Day plan saved with correct `meal_slot` values (breakfast/lunch/dinner/snack)
3. No crash; success state shown

---

## Complexity Tracking

No constitution violations — this is a minimal targeted fix with no new dependencies, no new data models, and a single-file change.
