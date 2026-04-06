# Data Model: Workout & Diet UX Fixes (009)

No new database tables or columns are required for this feature. All changes are to existing data shapes, frontend state, or backend prompt/scoring logic.

---

## Modified Entities

### WorkoutRecommendation (existing, backend)

| Field | Type | Change |
|-------|------|--------|
| `structured_plan` | JSON | Shape changes: `{ weeks: [...] }` → `{ days: [...] }` (one week only) |
| `score` | float (not persisted) | Computed dynamically; floor enforced at generation time (≥ 90) |

**New `structured_plan` schema** (single-week):
```json
{
  "days": [
    {
      "day": "Monday",
      "focus": "Push",
      "exercises": [
        {
          "name": "Bench Press",
          "sets": 4,
          "reps": "8-10",
          "rest_seconds": 90
        }
      ]
    }
  ]
}
```

**Previous schema** (4-week, now deprecated for new generations):
```json
{
  "weeks": [
    {
      "week_number": 1,
      "days": [ ... ]
    }
  ]
}
```

> **Migration note**: Existing saved workout recommendations with the 4-week schema should still render. The frontend renderer must handle both `plan.days` (new) and `plan.weeks[0].days` (legacy fallback).

---

## New Frontend State Shapes

### Workout Plan Editor State

```typescript
interface WorkoutPlanEditorState {
  plan: SingleWeekPlan;           // current (potentially edited) plan
  originalScore: number;          // score at generation time — frozen, never mutated
  currentScore: number;           // recomputed client-side on each edit
  scoreDelta: number;             // currentScore − originalScore (signed)
}

interface SingleWeekPlan {
  days: WorkoutDay[];
}

interface WorkoutDay {
  day: string;          // e.g., "Monday"
  focus: string;        // e.g., "Push"
  exercises: Exercise[];
}

interface Exercise {
  name: string;
  sets: number;
  reps: string;         // e.g., "8-10"
  rest_seconds: number;
}
```

### MacroBar Color Map

```typescript
const MACRO_COLOR_MAP: Record<string, string> = {
  cyan:   "#06b6d4",
  green:  "#22c55e",
  amber:  "#f59e0b",
  purple: "#a855f7",
  red:    "#ef4444",
};
```

### Day Planner Meal Selector State

```typescript
// Existing — no change to shape, only to how options are grouped
type MealSlots = Record<MealSlot, string | null>;  // slot → savedMealId | null

type MealSlot = "breakfast" | "lunch" | "dinner" | "snack";
```

---

## Client-Side Scoring Dimension Weights

Derived from `workout_scorer.py` — used for local score recomputation on edits:

| Dimension | Max Points |
|-----------|-----------|
| Coverage  | 25 |
| Volume    | 30 |
| Balance   | 20 |
| Cardio    | 15 |
| Frequency | 10 |
| **Total** | **100** |

These weights MUST stay in sync with `workout_scorer.py`. If backend weights change, the frontend constant must be updated in the same PR.
