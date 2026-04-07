# Feature Specification: Food Log Quantity Unit Selector

**Feature Branch**: `021-quantity-unit-selector`
**Created**: 2026-04-06
**Status**: Draft
**Input**: User description: "now another thing i noticed is that there should be more measurement options, aka if im getting a drink added the quantity would be ounces. or if im getting a food item, maybe the quantity would make more sense to be in pieces or lbs etc, there should not just be the gram option there should be a dropdown asking the user what quantity they would like to measure in when they add it."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Select Measurement Unit When Adding Food to Log (Priority: P1)

A user searching for and adding a food or drink item to their daily food log currently must enter the quantity in grams only. This user wants to type a quantity in a familiar unit — such as ounces for a drink, pieces for a snack item, or pounds for a protein source — and have the system automatically convert it to grams for nutritional calculation.

**Why this priority**: This is the core request. Without unit selection the food logging UX is friction-heavy for users who do not think in metric units, causing them to skip logging or enter incorrect values. It directly affects the accuracy of calorie and macro tracking.

**Independent Test**: Open the Food & Meals → Search & Add tab, search for any food item, and confirm that a unit selector dropdown appears alongside the quantity input. Select a non-gram unit (e.g., oz), enter a value, and verify the item is logged with correctly converted gram-equivalent macros.

**Acceptance Scenarios**:

1. **Given** a user has searched for a food item and it appears in results, **When** they view the add-to-log controls for that item, **Then** a unit dropdown is visible next to the quantity input field, defaulting to "g" (grams).
2. **Given** the unit dropdown is visible, **When** the user selects "oz" and enters "8", **Then** the system logs the item using the gram-equivalent of 8 oz (≈ 227 g) and scales all macros proportionally.
3. **Given** the unit dropdown is visible, **When** the user selects "piece" and enters "2", **Then** the system logs the item using 2× the per-100 g serving estimate and scales macros proportionally.
4. **Given** the unit dropdown is visible, **When** the user selects "lb" and enters "0.5", **Then** the system logs 0.5 lb (≈ 227 g) with correctly scaled macros.
5. **Given** the user selects "ml" for a drink, **When** they enter "355" (a standard can), **Then** the system logs the item at 355 ml treated as 355 g (water-density approximation) with scaled macros.

---

### User Story 2 - Unit Selector on Custom Meal Item Entry (Priority: P2)

A user building a custom meal (via the Search & Add / Build a Meal workflow) wants to specify ingredient quantities in the same flexible units as the food log entry flow — e.g., "2 cups of oats" or "6 oz of chicken breast" — rather than being forced to convert to grams before entry.

**Why this priority**: Custom meal building shares the same quantity input pattern as direct log entry. Applying the same unit selector here eliminates a parallel inconsistency in the same screen.

**Independent Test**: In the Build a Meal section, add a food item and confirm the unit dropdown appears alongside quantity. Select "oz", enter a value, save the meal, and verify the saved item reflects the gram-equivalent value.

**Acceptance Scenarios**:

1. **Given** a user is building a custom meal and adds a food search result, **When** the item appears in the pending meal list, **Then** a unit dropdown is available on each item's quantity field.
2. **Given** a unit is selected and a quantity is entered, **When** the user saves the meal, **Then** the stored item quantity reflects the gram-equivalent of the entered value and unit.

---

### Edge Cases

- User enters 0 or a negative number — input should be rejected with an inline validation message.
- User selects "piece" for a liquid item — allowed; the piece-to-gram conversion uses the USDA serving size if available, otherwise 100 g/piece, and the logged entry notes the unit for transparency.
- Very large quantities (e.g., 10 000 g) — system accepts them; no upper cap enforced at the UI level.
- User switches unit after entering a quantity — the quantity field value persists; only the unit label changes. The conversion is applied at log time, not live.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The quantity input for food log entries MUST be accompanied by a unit selector dropdown.
- **FR-002**: The unit selector MUST offer at minimum the following options: g (grams), oz (ounces), lb (pounds), ml (millilitres), piece/item, cup.
- **FR-003**: When a non-gram unit is selected and the user submits, the system MUST convert the entered quantity to grams before storing or calculating macros, using standard conversion factors (1 oz = 28.3495 g, 1 lb = 453.592 g, 1 ml ≈ 1 g, 1 cup = 240 ml ≈ 240 g). For "piece", the system MUST use the USDA serving size (grams per serving) when that data is present in the search result; if absent, fall back to 100 g per piece.
- **FR-004**: All macro values (calories, protein, carbs, fat, fiber) MUST be scaled proportionally to the converted gram quantity before being stored in the food log.
- **FR-005**: The unit selector MUST default to "g" on every new entry so existing users are not disrupted.
- **FR-006**: The same unit selector MUST appear on the custom meal item entry (Build a Meal flow) with identical unit options and conversion behaviour.
- **FR-007**: The selected unit and original entered value MUST be displayed in the food log entry line item so users can verify what they logged (e.g., "Chicken Breast — 6 oz (170 g)").

### Key Entities

- **FoodLogEntry**: Extended with two new nullable backend columns — `entered_quantity` (numeric, the value the user typed) and `entered_unit` (string enum, the unit they selected) — stored alongside the existing `quantity_g` field. These persist across devices and sessions and are displayed in log entry line items.
- **Unit**: An enumerated value set — g, oz, lb, ml, piece, cup — with associated conversion factors to grams.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can add a food item to their log using any of the 6 supported units in under 30 seconds from search to confirmation.
- **SC-002**: 100% of logged entries using non-gram units store a correctly converted gram quantity (verified by checking stored value vs. expected conversion).
- **SC-003**: The unit dropdown is visible and operable on both the food log entry and the custom meal builder on the same release.
- **SC-004**: No existing food log entries or custom meals are affected or re-converted when the feature is deployed (backward-compatible change).

## Clarifications

### Session 2026-04-06

- Q: Should the original entered unit and value be persisted to the backend database, or is the conversion to grams the only thing stored? → A: Store `entered_quantity` + `entered_unit` as new nullable columns in the food log entry table; display both on all devices.
- Q: When a user switches unit after typing a quantity, should the quantity field auto-recalculate to the equivalent in the new unit? → A: No — raw number stays as typed; unit label changes only; conversion happens at submit.
- Q: For the "piece" unit, should the USDA serving size be used when available, or always fall back to 100 g? → A: Use USDA serving size when present in the search result; fall back to 100 g when absent.

## Assumptions

- The existing food search returns nutritional data per 100 g; all unit conversions are relative to this 100 g baseline.
- "piece" as a unit uses the USDA serving size (grams per serving) when available in the search result payload, falling back to a flat 100 g default when the serving size is absent.
- "cup" is standardised at 240 g (water-equivalent); this is a known approximation that varies by ingredient density but is acceptable for v1.
- ml is treated as gram-equivalent (water density = 1 g/ml) for all items; this is a v1 approximation.
- The `entered_quantity` and `entered_unit` fields are persisted to the backend and used for display across devices. They do not affect any downstream calorie/macro calculations, which always operate on `quantity_g`.
- Backend schema change is minimal — two nullable columns added to the food log entry table; no breaking migration required.
- This feature applies to the food log direct-entry flow and the custom meal builder. It does not apply to the AI-generated diet plan viewer (those entries are already in grams).
