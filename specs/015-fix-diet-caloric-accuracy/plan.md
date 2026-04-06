# Implementation Plan: Fix Diet Plan Caloric Accuracy

**Branch**: `015-fix-diet-caloric-accuracy` | **Date**: 2026-04-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/015-fix-diet-caloric-accuracy/spec.md`

## Summary

The algorithmic diet engine (`diet_engine.py`) deviates up to 26% from the user's caloric target. Root cause: `_scale_item` clamps gram portions to `[30, 400]`. When a food item's ideal portion falls outside this range (e.g. calorie-dense nuts where the ideal 110-cal portion would be ~18g, clamped to 30g → delivers ~165 cal instead), the actual calories exceed the per-item target. No correction step exists after meal assembly, so the day total drifts.

The fix adds a day-level proportional correction pass in `_build_day`: after all meals are assembled, compute `actual_total / target_total`. If the ratio is outside [0.95, 1.05], apply a uniform scale factor to every item's gram quantity (clamped per FR-004 to [20, 600]). Also widens the pre-clamp bounds from [30, 400] to [20, 600] per spec.

## Technical Context

**Language/Version**: Python 3.13
**Primary Dependencies**: No new dependencies — stdlib `math` only (all existing)
**Storage**: No schema change — correction is purely computational in the engine
**Testing**: pytest (existing in `services/recommendation-service/tests/`)
**Target Platform**: Linux server (recommendation-service)
**Project Type**: Backend algorithmic engine — single file change
**Constraints**: Correction must be O(n) and deterministic; no external calls

## Constitution Check

| Principle | Gate | Status |
|-----------|------|--------|
| I. Extensibility | Fix is internal to `_build_day` / `_scale_item`; no public interface changes | PASS |
| II. Algorithm Efficiency | Day-level correction is O(items) — one extra pass per day | PASS |
| III. License Compliance | No new dependencies | PASS |
| IV. Mandatory Test Coverage | Tests in `test_diet_engine.py` MUST assert ±5% for all goal types and restriction combos — already partially covered; new assertions required | PASS (tests in task list) |
| V. UI/UX Consistency | No UI change; deviation badge already in place | PASS |

## Project Structure

### Documentation (this feature)

```text
specs/015-fix-diet-caloric-accuracy/
├── plan.md              ← This file
├── research.md          ← Phase 0 output
├── quickstart.md        ← Phase 1 output
└── tasks.md             ← Phase 2 output (/speckit.tasks)
```

### Source Code

```text
services/recommendation-service/
├── src/services/diet_engine.py          ← PRIMARY CHANGE
└── tests/test_diet_engine.py            ← TEST UPDATES
```

## Phase 0: Research

### Decision 1: Correction strategy — where to apply the fix

- **Decision**: Day-level proportional rescaling in `_build_day` after all meals are assembled
- **Rationale**: Per-item clamping is the proximate cause, but fixing only the clamp bounds doesn't guarantee ±5% in all sparse-food scenarios. A post-hoc correction pass is the only provably ±5% approach. It is O(n), deterministic, and does not require changing the item-selection logic.
- **Alternatives considered**:
  - Widen clamp bounds only (30→20 min, 400→600 max): reduces deviation but doesn't guarantee ±5% when all items hit the bound simultaneously
  - Per-meal redistribution: more complex, same end result as day-level; rejected — day total is what matters for FR-001
  - Iterative refinement (select different foods if target missed): O(n²) worst case, nondeterministic — rejected per Constitution II

### Decision 2: Clamp bounds

- **Decision**: Change `_scale_item` clamp from `[30, 400]` to `[20, 600]` per FR-004
- **Rationale**: FR-004 explicitly specifies minimum 20g and maximum 600g. Wider bounds mean the correction pass has more headroom, reducing how aggressively scaling must be applied.

### Decision 3: Correction tolerance

- **Decision**: Correct if day total deviates more than 1% from target (`ratio outside [0.99, 1.01]`), to account for floating-point rounding. The spec requires ±5%; correcting to ±1% provides margin.
- **Rationale**: Always correcting (even when within ±5%) is simpler and ensures test assertions at ±2% pass easily.

### Decision 4: Redistribution when a slot has zero foods (FR-005)

- **Decision**: In `_build_day`, after building all meals, collect the caloric shortfall from empty slots and add it to non-empty slots proportionally (by their original slot ratio). This is done before the day-level correction pass.
- **Rationale**: FR-005 requires shortfall redistribution. Doing this before correction means the correction pass only needs to handle scaling inaccuracies, not missing slots.

## Phase 1: Design

### No data model changes

No new database entities, tables, or migrations are needed. The fix is purely in the plan generation algorithm.

### No API contract changes

The response schema for `GET /recommendations/{id}` is unchanged — `day_totals.calories` was already present. The value will now be accurate.

### Correction Algorithm (pseudocode)

```python
def _build_day(...):
    # 1. Build meals as before (may have clamping-induced inaccuracy)
    meals = [_build_meal(slot, ratio, ...) for slot, ratio in MEAL_SLOT_RATIOS.items()]

    # 2. Redistribute empty-slot shortfall (FR-005)
    empty_cal = sum(macro_targets.calories * ratio
                    for meal, (slot, ratio) in zip(meals, MEAL_SLOT_RATIOS.items())
                    if not meal["items"])
    non_empty_meals = [(meal, ratio) for meal, (slot, ratio) in ... if meal["items"]]
    # scale non-empty meals up proportionally to absorb empty_cal

    # 3. Day-level correction pass (Decision 1)
    actual_total = sum(m["meal_totals"]["calories"] for m in meals)
    target_total = macro_targets.calories
    ratio = actual_total / target_total if target_total > 0 else 1.0
    if not (0.99 <= ratio <= 1.01):
        scale = target_total / actual_total
        for meal in meals:
            for item in meal["items"]:
                new_grams = max(20.0, min(600.0, item["grams"] * scale))
                # recalculate calories/macros from new_grams
            # recalculate meal_totals
    # 4. Recompute day_totals from corrected meals
```

### Quickstart test

```bash
cd services/recommendation-service
python -c "
from src.services.diet_engine import generate_diet_plan
from dataclasses import dataclass

@dataclass
class M:
    calories: float = 2200
    protein_g: float = 165
    carbs_g: float = 248
    fat_g: float = 73

plan = generate_diet_plan(M(), [], 'general_health')
for day in plan['days']:
    cal = day['day_totals']['calories']
    dev = abs(cal - 2200) / 2200 * 100
    print(f\"Day {day['day']}: {cal:.0f} kcal  ({dev:.1f}% deviation)\")
    assert dev <= 5.0, f'Day {day[\"day\"]} deviation {dev:.1f}% exceeds 5%'
print('All days within ±5% ✓')
"
```

## Complexity Tracking

No violations — single file change, O(n) extra pass, no new dependencies.
