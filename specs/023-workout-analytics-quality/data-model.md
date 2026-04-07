# Data Model: Workout Score Accuracy, Analytics Depth & Quality Polish

## No Schema Changes Required

All data needed for this feature already exists. Changes are algorithmic and presentational only.

---

## Entities Used (unchanged)

### workout_splits / WorkoutExercise

| Field | Type | Notes |
|-------|------|-------|
| id | VARCHAR(36) | PK |
| user_id | VARCHAR(36) | FK |
| exercises | JSON/related | List of exercises with sets, reps, duration_seconds, rest_seconds, muscle_group |

**Change**: `workout_engine.py` validation loop enforces minimum score of 95 before accepting a generated plan.

**Change**: Frontend scoring in `recommendations/page.tsx` now recomputes whenever sets, reps, duration, or rest fields change (not only on exercise add/remove).

---

### scan_metrics (analytics)

| Column | Type | Notes |
|--------|------|-------|
| metric_key | VARCHAR | e.g., `segmental_lean_right_arm_kg` |
| metric_value | FLOAT | Nullable |
| scan_id | VARCHAR(36) | FK → scans.id |

**Change**: None. Analytics enhancements compute muscle balance and summary cards from existing metric values in the `analytics.dashboard` response.

---

## Computed Structures (frontend-only, not persisted)

### MuscleBalanceResult (derived in frontend)

```typescript
interface MuscleBalanceResult {
  pair: "arms" | "legs";
  leftValue: number;
  rightValue: number;
  imbalancePct: number;     // |left - right| / max(left, right) * 100
  isImbalanced: boolean;    // imbalancePct > 10
  dominantSide: "left" | "right" | "balanced";
}
```

Computed from `segmental_lean_left_arm_kg`, `segmental_lean_right_arm_kg`, `segmental_lean_left_leg_kg`, `segmental_lean_right_leg_kg` in the latest scan's delta data.

### BodyCompositionSummary (derived in frontend)

```typescript
interface BodyCompositionSummary {
  label: string;         // "Athletic" | "Healthy" | "Above Average" | "High Body Fat"
  bodyFatPct: number;
  smmKg: number;
  bmi: number;
  interpretation: string; // Plain-language sentence
}
```

Thresholds (general adult reference ranges):
- Body fat %: Athletic <15% (M) / <22% (F), Healthy 15–24% (M) / 22–31% (F), High >24% (M) / >31% (F)
- Since gender may not always be set, fallback to a gender-neutral "Low / Moderate / High" range.

---

## Optimistic Update State (frontend-only)

No new database entities. The optimistic state lives in TanStack Query's in-memory cache:

- `["restrictions"]` cache is updated immediately on mutation, then reconciled on `onSettled`
- `["goal"]` cache is updated immediately on mutation, then reconciled on `onSettled`
