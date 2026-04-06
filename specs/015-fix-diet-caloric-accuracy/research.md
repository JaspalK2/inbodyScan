# Research: Fix Diet Plan Caloric Accuracy (015)

## Decision 1: Correction strategy

- **Decision**: Day-level proportional rescaling in `_build_day` after meal assembly
- **Rationale**: The only provably ±5% approach. Per-item clamping cannot be eliminated (portion size must remain realistic), so a post-hoc correction scale factor is needed. Applying it at the day level is O(n), deterministic, and doesn't require changing food selection.
- **Alternatives**: Widening clamp bounds only (rejected — insufficient guarantee), iterative food re-selection (rejected — O(n²), non-deterministic)

## Decision 2: Clamp bounds

- **Decision**: `[20, 600]` grams (was `[30, 400]`)
- **Rationale**: FR-004 specifies these bounds. Wider range gives the correction pass more headroom.

## Decision 3: Apply correction when deviation > 1%

- **Decision**: Always apply scale factor when `actual/target` outside `[0.99, 1.01]`
- **Rationale**: Correcting to ±1% provides ±4% headroom before the spec's ±5% limit is breached. Simpler than conditional logic.

## Decision 4: Empty-slot shortfall redistribution (FR-005)

- **Decision**: Before the correction pass, add the caloric share of empty meal slots to non-empty slots in proportion to their original ratios
- **Rationale**: Ensures the day total isn't inherently under-target due to missing foods before scaling is even applied. Runs once per day, O(slots).
