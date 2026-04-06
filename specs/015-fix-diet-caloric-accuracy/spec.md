# Feature Specification: Fix Diet Plan Caloric Accuracy

**Feature Branch**: `015-fix-diet-caloric-accuracy`  
**Created**: 2026-04-06  
**Status**: Draft  
**Input**: Generated diet plans deviate up to 26% from the user's target caloric intake. Plans must land within ±5% of the target.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Generated Diet Plan Hits Caloric Target (Priority: P1)

A user receives a generated diet plan. The total daily calories across all four meals must be within ±5% of their personalised caloric target, every day of the 7-day plan.

**Why this priority**: A 26% caloric deviation is nutritionally significant — it can mean hundreds of calories too few or too many per day, undermining the user's health goal and eroding trust in the app's recommendations. This is the primary defect.

**Independent Test**: Generate a diet plan for a user with a known caloric target (e.g. 2200 kcal). For every one of the 7 days, the `day_totals.calories` value must fall between 2090 and 2310 kcal (within ±5%).

**Acceptance Scenarios**:

1. **Given** a user with a caloric target of 2200 kcal/day, **When** a diet plan is generated, **Then** every day's total calories is between 2090 and 2310 kcal (within ±5%)
2. **Given** a user with a caloric target of 1800 kcal/day, **When** a diet plan is generated, **Then** every day's total calories is between 1710 and 1890 kcal (within ±5%)
3. **Given** any supported goal type (lose_fat, build_muscle, general_health, maintain, improve_endurance), **When** a plan is generated, **Then** the ±5% accuracy requirement is met for that goal's caloric target
4. **Given** a user with dietary restrictions (e.g. vegetarian), **When** a plan is generated, **Then** the ±5% accuracy is maintained even with the restricted food set

---

### User Story 2 — Caloric Accuracy Displayed to User (Priority: P2)

The Recommendations page diet plan view shows the deviation from the caloric target so users can immediately see how close their plan is to their goal.

**Why this priority**: Once accuracy is fixed, users should be able to verify it at a glance. The existing deviation display (e.g. "+3% vs target") is already present in the UI — it must now reflect a tight, trustworthy number.

**Independent Test**: With an accurate plan generated, expand Day 1 on the Diet tab. The deviation badge must show ≤5% (positive or negative) and display in green.

**Acceptance Scenarios**:

1. **Given** a plan within ±5% of target, **When** the user views the Diet tab, **Then** the deviation indicator shows green and a value ≤ 5%
2. **Given** a plan that was generated before this fix (old inaccurate data), **When** the user views it, **Then** the deviation still displays (possibly amber/red) — no crash

---

### Edge Cases

- Food database (`foods.json`) has fewer available foods for a restricted diet — algorithm must still reach ±5% by scaling existing items rather than failing
- Caloric target is very low (e.g. 1200 kcal) or very high (e.g. 4000 kcal) — scaling must not produce implausible single-item portions (no item should exceed 600g or go below 20g)
- A meal slot has zero available foods after restriction filtering — the remaining meal slots must absorb the caloric allocation so the day total still hits ±5%

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each day's total calories in a generated plan MUST be within ±5% of the user's calculated daily caloric target
- **FR-002**: The caloric accuracy requirement MUST apply to all supported goal types: lose_fat, build_muscle, general_health, maintain, improve_endurance, weight_loss, muscle_gain
- **FR-003**: The caloric accuracy requirement MUST be maintained when dietary restrictions are applied (vegetarian, vegan, gluten_free, dairy_free, halal, kosher)
- **FR-004**: Individual food portion sizes MUST remain within realistic bounds — no single item scaled below 20g or above 600g
- **FR-005**: If a meal slot has no available foods after filtering, the caloric shortfall MUST be redistributed to the remaining non-empty meal slots to preserve the daily total
- **FR-006**: Protein, carbohydrate, and fat totals MUST also be within ±10% of their respective macro targets (caloric accuracy takes priority)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of generated diet plan days land within ±5% of the daily caloric target — 0 days outside this range
- **SC-002**: All 7 goal types produce plans meeting the ±5% caloric accuracy requirement
- **SC-003**: All supported dietary restriction combinations produce plans meeting the ±5% caloric accuracy requirement
- **SC-004**: No individual food portion exceeds 600g or falls below 20g in any generated plan

## Assumptions

- The daily caloric target is already correctly calculated by the macro calculator (Mifflin-St Jeor BMR formula) — this fix is only in the food selection and portion-scaling layer
- The existing `foods.json` database (229 foods seeded from USDA) contains sufficient variety to meet caloric targets across all restriction combinations
- The fix is applied in the backend plan generation engine — no changes to the user-facing calorie display logic are needed beyond what already exists
- Proportional meal slot ratios (breakfast 25%, lunch 35%, dinner 30%, snack 10%) are correct and remain unchanged; only the portion-scaling within each slot needs correction
