# Research: Fix Diet Plan Rendering Crash (014)

## Decision 1: Normalisation layer location

- **Decision**: Frontend-only, in `DietDayRow` via a `normaliseMeal()` helper function
- **Rationale**: Backend stores new schema; no DB migration needed; the frontend is the only consumer that renders the meal data; minimal blast radius
- **Alternatives considered**: Backend normalisation (rejected — would require schema migration or permanent dual-path in engine); stored-plan migration (rejected — overkill, risks corrupting user-edited plans)

## Decision 2: Normalisation function design

- **Decision**: Pure function `normaliseMeal(meal: any): NormalisedMeal` — maps both old and new schemas to one internal shape used by all downstream rendering code
- **Rationale**: Single point of change; downstream code reads clean typed fields; easy to extend for any future schema version
- **Alternatives considered**: Inline `??` chains at each call site (rejected — 8+ call sites, error-prone, unreadable)

## Decision 3: `foods` list representation for new schema

- **Decision**: Map `meal.items[]` → `"${item.food_name} ${item.grams}g"` strings, matching the display format already used for old-format foods
- **Rationale**: Consistent string representation for both display and editing; no UI changes needed; aligns with the existing "150g Chicken Breast" convention visible in the food-search add flow
- **Alternatives considered**: Rendering `items` as structured objects (rejected — would require view-layer changes; existing editing logic expects a string array for `foods`)

## Decision 4: Totals computation

- **Decision**: Update the `totals` reducer to call `normaliseMeal()` first so it reads the normalised flat fields — fixing the "0 kcal" day header bug for new plans
- **Rationale**: One reducer fix covers both the day header summary and the deviation-from-target calculation
- **Alternatives considered**: Separate fix per call site (rejected — same root cause; single fix cleaner)
