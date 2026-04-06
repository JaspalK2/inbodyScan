# Implementation Plan: Plan Save Flow and Workout UX Fixes

**Branch**: `006-plan-save-workout-ux` | **Date**: 2026-04-03 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/006-plan-save-workout-ux/spec.md`

## Summary

This feature is a pure frontend fix across the Recommendations page. Five user stories:

1. **Save Day composite action**: Clicking "Save Day" on a generated diet day now simultaneously creates a `DayPlan` record AND one `CustomMeal` per non-empty meal slot (named "Day Planner — [Slot]").
2. **Tab content clarity**: Food & Meals → Saved Meals shows only individual `CustomMeal` records. The "Day Plans" section added in 005 is removed. Day Planner tab shows only `DayPlan` records.
3. **Exercise field labels**: Every exercise row in view and edit mode carries visible labels (Sets, Reps, Weight, Rest).
4. **Add/remove exercises in generated plans**: Edit mode gains "+ Add exercise" per non-rest day and a remove button per exercise row.
5. **Live score in custom split builder**: The `WorkoutTab` split builder gains the same 300ms-debounced live score panel already used in `WorkoutPlanCard`.

No backend changes. No new dependencies. No schema migrations.

## Technical Context

**Language/Version**: TypeScript 5.x / Next.js 15 (frontend only)  
**Primary Dependencies**: React 18, TanStack Query v5, existing UI component library (Button, Input, Label, Loader2, etc.)  
**Storage**: Supabase PostgreSQL — no schema changes; existing `custom_meals`, `day_plans`, `workout_recommendations`, `workout_splits` tables  
**Testing**: Jest + React Testing Library (frontend unit/render tests); existing pytest integration tests unchanged  
**Target Platform**: Web browser (desktop-first, responsive)  
**Project Type**: Web application — single-page feature within existing Next.js app  
**Performance Goals**: Score update ≤ 1 second from exercise change; Save Day composite action ≤ 3 seconds  
**Constraints**: No new npm packages; all UI uses existing design tokens (purple-400, cyan-300, etc.) and existing components  
**Scale/Scope**: Single file primary change (`frontend/app/(app)/recommendations/page.tsx`); existing API client (`frontend/lib/api.ts`) unchanged

## Constitution Check

| Principle | Gate | Status |
|-----------|------|--------|
| I. Extensibility | New "Save Day" composite action is additive to existing `DietDayRow`; no existing interfaces modified. Exercise add/remove extends existing plan state mutation pattern. | ✅ PASS |
| II. Algorithm Efficiency | Exercise add/remove uses O(W×D) nested map over 4 weeks × 7 days — effectively O(1). Score debounce prevents excessive API calls. | ✅ PASS |
| III. License Compliance | No new dependencies. All changes use existing MIT/Apache 2.0 licensed packages. | ✅ PASS |
| IV. Mandatory Test Coverage | Unit tests for Save Day mapping logic, exercise add/remove state mutation, label rendering. Integration tests: existing backend tests unchanged. | ✅ REQUIRED — tasks include tests |
| V. UI/UX Consistency | All new UI elements (add exercise button, labels, score panel) use existing design tokens and component primitives. No new inline colors. | ✅ PASS |

## Project Structure

### Documentation (this feature)

```text
specs/006-plan-save-workout-ux/
├── plan.md              # This file
├── research.md          # Phase 0 output ✓
├── data-model.md        # Phase 1 output ✓
├── quickstart.md        # Phase 1 output ✓
├── contracts/
│   └── ui.md            # Phase 1 output ✓
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (files changed)

```text
frontend/
├── app/(app)/recommendations/
│   └── page.tsx          # PRIMARY: all 5 user stories implemented here
└── lib/
    └── api.ts            # No changes required (all endpoints already exist)
```

### Key Components Affected

| Component | Change |
|-----------|--------|
| `DietDayRow` | "Save Day" button triggers composite mutation: createDayPlan + N×createMeal |
| `FoodMealsTab` | Remove "Day Plans" section from saved sub-tab |
| `WorkoutPlanCard` | Exercise view labels + add/remove exercise in edit mode |
| `WorkoutTab` (split builder) | Add live score panel with 300ms debounce on `days` state |

## Complexity Tracking

No constitution violations. No complexity overrides required.

## Phase 0 Research Summary

See [research.md](research.md) for full findings. Key decisions:

- **Save Day**: Sequential mutation — `createDayPlan` first, then `Promise.all` for meal saves. Partial failure shows warning but preserves day plan.
- **Exercise naming prefix**: `"Day Planner — {Slot}"` using em-dash for visual clarity.
- **Immutable exercise state**: Nested `.map` spread — consistent with existing code in `WorkoutPlanCard`.
- **Live score**: Same `useRef` debounce + `useEffect` pattern already in `WorkoutPlanCard`; extend to `WorkoutTab`.

## Phase 1 Design Summary

- **No new entities** — all data stored in existing `CustomMeal` and `DayPlan` structures.
- **No new API contracts** — all existing endpoints reused.
- **UI contracts** defined in [contracts/ui.md](contracts/ui.md):
  - Exercise view mode label format
  - Edit mode label/placeholder requirements
  - Add/remove exercise behaviour
  - Live score panel behaviour in split builder
- **Integration scenarios** in [quickstart.md](quickstart.md): 7 scenarios covering all user stories.
