# Contract: Workout Score Enforcement

## Backend — workout_engine.py generation loop

**Invariant**: Any plan returned by the generation engine MUST have `score.overall >= 95`.

**Enforcement pseudocode**:
```python
MAX_RETRIES = 10
for attempt in range(MAX_RETRIES):
    plan = generate_plan(...)
    score = score_workout_split(plan)
    if score.overall >= 95:
        return plan
    # Redistribute: add sets to lowest-scoring muscle groups
    plan = boost_underserved_groups(plan, score)
raise PlanGenerationError("Could not reach 95+ score after retries")
```

## Frontend — recommendations/page.tsx live scoring

**Invariant**: The displayed percentage recalculates on any change to:
- Exercise list (add/remove) — already implemented
- `sets` field on any exercise — NEW
- `reps` field on any exercise — NEW
- `duration_seconds` field on any exercise — NEW
- `rest_seconds` field on any exercise — NEW

**Trigger**: The `useMemo` (or equivalent) that computes the score must depend on the full exercise list including all mutable fields, not just the list length.
