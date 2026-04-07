# Implementation Plan: Workout Score Accuracy, Analytics Depth & Quality Polish

**Branch**: `023-workout-analytics-quality` | **Date**: 2026-04-07 | **Spec**: specs/023-workout-analytics-quality/spec.md

## Summary

Four interrelated improvements: (1) enforce ≥95% score on generated workout plans and make the score reactive to rep/set/duration/rest edits; (2) enhance the analytics page with delta indicators, plain-language summary cards, and muscle balance analysis; (3) convert profile page mutations to optimistic updates; (4) unbounded full-stack iterative quality pass until the webapp reaches production quality.

## Technical Context

**Language/Version**: Python 3.13 (recommendation-service), TypeScript 5.x / Next.js 15 (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 async (backend); React 18, TanStack Query v5, Recharts, Tailwind CSS (frontend)
**Storage**: No schema changes — all data already exists
**Testing**: Manual smoke tests via quickstart.md
**Target Platform**: Vercel (frontend), Railway/Fly (backend)
**Project Type**: Web application (microservices backend + Next.js frontend)
**Performance Goals**: Score reactivity < 100ms; profile interactions < 50ms to reflect on screen
**Constraints**: No new API endpoints for analytics (all data in existing dashboard response); no DB migrations
**Scale/Scope**: Affects all users; additive/corrective changes only

## Constitution Check

- ✅ No new services or databases introduced
- ✅ No schema migrations required
- ✅ Changes are additive and backward-compatible
- ✅ Algorithm change (score enforcement) follows Principle II (Algorithm Efficiency) — retry loop is O(n) bounded by MAX_RETRIES=10
- ✅ Optimistic updates reduce latency, consistent with Principle II
- ✅ Iterative quality pass aligns with Principle I (Extensibility by Design) by fixing rough edges before they become blockers

## Project Structure

### Documentation (this feature)

```text
specs/023-workout-analytics-quality/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   ├── workout-score.md
│   └── analytics-ui.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (affected files)

```text
services/
└── recommendation-service/
    └── src/
        └── services/
            └── workout_engine.py          # Enforce >=95 score in generation loop

frontend/
└── app/
    └── (app)/
        ├── recommendations/
        │   └── page.tsx                   # Score reactivity: watch reps/sets/duration/rest
        ├── analytics/
        │   └── page.tsx                   # Full analytics enhancement
        └── profile/
            └── page.tsx                   # Optimistic updates for restrictions + goal
```

## Implementation Notes

### US1 — Workout Score >=95% + Reactivity

**Backend (`workout_engine.py`)**: The plan generation loop must validate `score.overall >= 95` after scoring. If below 95, boost the lowest-scoring muscle groups (add sets proportionally) and re-score. Retry up to 10 times. The `workout_scorer.py` formula itself does not change.

**Frontend (`recommendations/page.tsx`)**: The client-side scoring `useMemo` (lines ~138-189) currently recomputes when the exercise list changes. It needs to also recompute when individual exercise fields change. The dependency array or state structure needs to include sets/reps/duration/rest values, not just the exercise list reference.

### US2 — Analytics Enhancement

All data is already in `analytics.dashboard` response (`history`, `deltas`). Frontend-only changes to `analytics/page.tsx`:

1. **Delta cards row**: Map `data.deltas` to a row of cards at top for body_weight_kg, body_fat_percentage, skeletal_muscle_mass_kg, BMI. Show current value + delta with colour (green = improvement, red = decline direction depending on metric).
2. **Summary card**: Derive plain-language text from current body fat %, SMM. Simple threshold rules (see data-model.md). Gender-neutral fallback unless profile.gender is set.
3. **Muscle balance section**: Compute `imbalancePct` for left/right arm and leg from latest segmental metrics. Show comparison bar + flag if >10%.
4. **Trend charts**: Show all metrics from `data.history` grouped into primary/secondary sections (not just first 4).

### US3 — Optimistic Updates

`profile/page.tsx` mutations converted to TanStack Query v5 optimistic pattern:
- `addRestriction`: `onMutate` adds item to `["restrictions"]` cache; `onError` reverts; `onSettled` reconciles
- `removeRestriction`: `onMutate` removes item from cache; `onError` reverts; `onSettled` reconciles
- `setGoal`: `onMutate` sets new goal in `["goal"]` cache; `onError` reverts; `onSettled` reconciles

### US4 — Iterative Quality Pass

After US1-US3 are complete, systematically walk every user-facing page and fix all issues found. Each batch of confirmed fixes gets its own commit and merge to main. Continue until:
- All pages have empty states with CTA
- All async operations have loading indicators
- No backend errors silently swallowed
- No raw IDs or debug text visible to users
- No layout issues at 375px width
- No operations taking >500ms

Known issues to address in first iteration cycle:
- Dashboard: verify empty state with 0 scans
- Scans page: verify empty state and upload button prominence
- Plans page: verify empty states for Diet, Workout, Saved tabs
- Profile page: verify all sections have loading/saving states
- Nav: already fixed (022) but verify name shows correctly end-to-end

## Complexity Tracking

No constitution violations. The retry loop in workout_engine.py is bounded (MAX_RETRIES=10). No new abstractions — existing patterns extended.
