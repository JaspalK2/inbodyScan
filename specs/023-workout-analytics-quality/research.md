# Research: Workout Score Accuracy, Analytics Depth & Quality Polish

## Workout Volume Score — Current Algorithm

**Decision**: The score is computed in `services/recommendation-service/src/services/workout_scorer.py` across 5 dimensions summing to 100:

| Dimension | Points |
|-----------|--------|
| Coverage (muscle groups covered) | 25 |
| Volume Adequacy (sets vs targets) | 30 |
| Push/Pull Balance | 20 |
| Cardio Inclusion | 15 |
| Training Frequency | 10 |

**5% Tolerance Fix**: The generation engine (`workout_engine.py`) already validates plans by calling `score_workout_split()`. The fix is to enforce a minimum score of 95 in `workout_engine.py`'s validation loop — if the generated plan scores below 95, redistribute volume (add sets to under-served groups) until it reaches ≥95. The score formula itself does not need to change.

**Score Reactivity Fix**: The frontend has a duplicate scoring implementation at `frontend/app/(app)/recommendations/page.tsx` lines ~138-189. Currently the score recalculates only when exercises are added/removed (list changes). It does NOT recalculate when reps, sets, duration, or rest values are edited inline. The fix is to include all these mutable fields in the computation's dependency tracking (state-level: whenever any field of any exercise changes, recompute).

**Rationale**: Keeping the scoring logic in both backend (source of truth) and frontend (live preview) is an existing pattern. The frontend duplicate only needs the set/rep/duration fields to trigger recomputation.

---

## Analytics Page — Current State & Enhancement Strategy

**Current state** (`frontend/app/(app)/analytics/page.tsx`, 153 lines):
- Line charts for first 4 metrics from `data.history`
- Segmental bar chart (left/right arm/leg/trunk)
- Radial body composition chart
- Empty state exists

**What `analytics.dashboard` already returns**:
```
history: [{metric_key, points: [{scan_date, value}]}]  — all metrics over time
deltas:  [{metric_key, current_value, previous_value, delta, delta_pct}]  — change since last scan
```

**Decision**: All enhancements are purely frontend. No new API endpoints needed — all data is already in the dashboard response.

**Enhancement plan**:
1. **Delta indicators**: `data.deltas` is already returned but not fully surfaced per-metric. Add delta cards above charts.
2. **Muscle balance analysis**: Compute left/right imbalance from segmental data already in history. If `|leftArm - rightArm| / max(leftArm, rightArm) > 0.10`, flag as imbalance. Same logic for legs.
3. **Plain-language summary cards**: Derive text from key metric values using simple threshold rules (e.g., body fat % range → "Healthy / Athletic / High").
4. **More trend charts**: Show all available metrics, not just the first 4.
5. **Better layout**: Reorganise from current 3-section grid to a tabbed or sectioned dashboard.

**Rationale**: All data is already available in the dashboard API response. No schema changes. No new endpoints. Pure frontend enhancement.

---

## Optimistic Updates — Profile Page

**Current state**: `frontend/app/(app)/profile/page.tsx` mutations use `onSuccess: () => qc.invalidateQueries(...)` — full refetch on server confirmation. This causes visible lag.

**Decision**: Use TanStack Query v5's `onMutate` / `onError` / `onSettled` pattern for optimistic updates on:
- Dietary restriction add (`addRestriction`)
- Dietary restriction remove (`removeRestriction`)
- Health goal change (`setGoal`)

**Pattern**:
```typescript
onMutate: async (newItem) => {
  await qc.cancelQueries({ queryKey });
  const previous = qc.getQueryData(queryKey);
  qc.setQueryData(queryKey, optimisticNewValue);
  return { previous };
},
onError: (_err, _vars, ctx) => {
  qc.setQueryData(queryKey, ctx.previous);  // revert
},
onSettled: () => qc.invalidateQueries({ queryKey }),  // sync with server
```

**Rationale**: This is the standard TanStack Query v5 optimistic update pattern. The `onSettled` ensures eventual consistency regardless of success/failure. No backend changes needed.

---

## Iterative Quality Pass — Scope

**Decision**: The pass covers the entire webapp (frontend + backend) and is unbounded — it continues until no meaningful improvements remain. Issues to look for in each iteration cycle:
- Missing empty states (any page with no data shows blank)
- Missing loading indicators
- Backend errors silently swallowed (no user-facing message)
- Slow endpoints (any query taking >500ms)
- Missing error boundaries
- Layout issues at mobile width (375px)
- Inconsistent button/label styles
- Raw IDs or technical strings visible to users

**Approach**: After implementing US1–US3, systematically walk each page and fix discovered issues, merging to main when a batch of confirmed fixes is complete.

---

## No Schema Changes Required

All enhancements use existing data:
- Workout score: existing `WorkoutScore`, `WorkoutSplit`, `WorkoutExercise` models unchanged
- Analytics: existing `dashboard` endpoint response already includes all required data
- Profile optimistic updates: no backend changes at all
