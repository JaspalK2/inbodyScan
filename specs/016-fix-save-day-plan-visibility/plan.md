# Implementation Plan: Fix Save Diet Day Plan Visibility

**Branch**: `016-fix-save-day-plan-visibility` | **Date**: 2026-04-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/016-fix-save-day-plan-visibility/spec.md`

## Summary

The "Save day" button silently fails due to three root causes identified via code inspection of `frontend/app/(app)/recommendations/page.tsx`:

1. **Silent error swallowing** — `saveDayPlan` has `try/finally` but no `catch`. Any error from `createDayPlan` (network, 4xx, 5xx) is swallowed silently. The `qc.invalidateQueries` call inside `try` is unreachable on error.
2. **Alert-based empty-meals guard** — The guard shows `alert()` which is blocking and easy to miss; users may dismiss it and assume the save worked.
3. **No success feedback** — On a successful save there is no visible confirmation, so users cannot tell if the action worked.

Since all components share one `QueryClientProvider`, the `["day-plans"]` invalidation is structurally correct — it just never runs when the API call fails silently. The fix is minimal: add `catch`, move feedback to inline state, and add a success indicator.

## Technical Context

**Language/Version**: TypeScript 5.x / Next.js 15
**Primary Dependencies**: React 18, TanStack Query v5, Tailwind CSS + shadcn/ui (all existing)
**Storage**: No schema change — backend endpoint unchanged
**Testing**: Vitest (already installed in frontend/)
**Target Platform**: Web browser (Next.js App Router)
**Project Type**: Frontend-only fix — single function in one component
**Constraints**: No new dependencies; must not break existing DayPlannerTab save flow (line ~1252)

## Constitution Check

| Principle | Gate | Status |
|-----------|------|--------|
| I. Extensibility | Error types are handled via a single state string — new error cases addable without touching happy path | PASS |
| II. Algorithm Efficiency | No new loops; O(1) state updates only | PASS |
| III. License Compliance | No new dependencies | PASS |
| IV. Mandatory Test Coverage | Unit tests for error path and success path required | PASS — test tasks included |
| V. UI/UX Consistency | Inline state pattern matches existing savingDay boolean; no new UI primitives | PASS |

## Project Structure

### Source Code

```text
frontend/
├── app/(app)/recommendations/
│   └── page.tsx              ← PRIMARY CHANGE: saveDayPlan in DietDayRow
└── __tests__/recommendations/
    └── saveDayPlan.test.ts   ← NEW: unit tests for error/success state logic
```

## Phase 0: Research

### Decision 1: Error handling pattern
- **Decision**: Add `catch (err)` block; set local `saveError: string | null` state; display inline below the button
- **Rationale**: Follows the existing `savingDay` boolean pattern already in DietDayRow; no new dependencies needed
- **Alternatives**: `alert()` for errors (rejected — blocking, inconsistent UX); toast library (rejected — no existing infrastructure)

### Decision 2: Success feedback
- **Decision**: Add `saveSuccess: boolean` state; set true on resolve; auto-clear after 3s via `setTimeout`; display inline "Day saved" message
- **Rationale**: Same lightweight state pattern; 3-second auto-dismiss avoids cluttering the UI
- **Alternatives**: Permanently change button text (rejected — confusing for re-saves)

### Decision 3: Empty-meals guard UX
- **Decision**: Replace `alert("No meals to save…")` with `setSaveError("No meals to save — add foods first.")` so the message appears inline
- **Rationale**: `alert()` is jarring and can be missed; inline state is being added anyway for the catch path — reuse it

### Decision 4: Cache invalidation
- **Decision**: No structural change needed — `qc.invalidateQueries` is already correctly placed after the await. The fix is ensuring the catch block prevents the try-block success path from being hidden.
- **Rationale**: Since all three tabs (`DietTab`, `FoodMealsTab`, `DayPlannerTab`) call `useQueryClient()` from the same provider, invalidating `["day-plans"]` propagates to all three.

## Phase 1: UI Contract

### New state in DietDayRow

| State | Type | Initial | Trigger |
|-------|------|---------|---------|
| `saveError` | `string \| null` | `null` | Guard fires OR API throws |
| `saveSuccess` | `boolean` | `false` | API resolves; auto-clears after 3s |

### Updated saveDayPlan control flow

```
1. nonEmptyMeals = meals filtered by normaliseMeal(m).foods.length > 0
2. If empty → setSaveError("No meals to save — add foods first.") → return
3. setSavingDay(true), setSaveError(null), setSaveSuccess(false)
4. try:
     await createDayPlan(...)
     qc.invalidateQueries(["day-plans"])
     setSaveSuccess(true)
     setTimeout(() => setSaveSuccess(false), 3000)
   catch:
     setSaveError("Failed to save — please try again.")
   finally:
     setSavingDay(false)
```

### Rendering additions (below "Save day" button row)

- `saveError` truthy → `<p className="text-xs text-red-400 mt-1">{saveError}</p>`
- `saveSuccess` truthy → `<p className="text-xs text-green-400 mt-1">Day saved ✓</p>`

## Quickstart

### Scenario 1 — Happy path
1. Generate a diet plan, expand Day 1, click "Save day"
2. **Expected**: Spinner → "Day saved ✓" (green, 3s) → switch to Food & Meals → Saved tab → "Day 1 meal plan" visible

### Scenario 2 — Network error
1. Disable network → click "Save day"
2. **Expected**: Spinner → "Failed to save — please try again." (red) → plan does NOT appear in list

### Scenario 3 — Empty meals guard
1. (Edge case) All 4 meal slots have zero foods → click "Save day"
2. **Expected**: Inline "No meals to save" message appears; no spinner; no API call

### Scenario 4 — Day Planner reflects saved plan
1. Save Day 3 → navigate to Day Planner tab (no reload)
2. **Expected**: "Day 3 meal plan" listed in saved plans immediately

## Complexity Tracking

No violations — minimal targeted fix, no new dependencies, two new local state variables.
