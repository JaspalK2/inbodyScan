# Research: Food Log Quantity Unit Selector

## Unit Conversion Factors

**Decision**: Use the following standard conversion factors, all relative to grams.

| Unit | Symbol | Grams per unit | Source |
|------|--------|---------------|--------|
| gram | g | 1.0 | baseline |
| ounce (avoirdupois) | oz | 28.3495 | NIST |
| pound | lb | 453.592 | NIST |
| millilitre | ml | 1.0 | water-density approximation (v1) |
| cup (US) | cup | 240.0 | US customary |
| piece / item | piece | USDA serving_size_g if available, else 100.0 | USDA FoodData Central |

**Rationale**: These are universally recognised values. ml≈g water-density approximation
is standard in nutrition apps for v1 (e.g. MyFitnessPal, Cronometer).

**Alternatives considered**: Using ingredient-specific densities for ml — rejected for v1
complexity; will revisit if user feedback surfaces inaccuracy issues.

---

## USDA Serving Size Availability

**Decision**: Use `serving_size` + `serving_unit` from the existing `FoodResult`
interface (`food_search.py` already maps `servingSize` and `servingSizeUnit` from USDA).
When `serving_unit` indicates a weight unit (g, oz, lb) convert to grams; otherwise
treat `serving_size` as grams directly (USDA returns grams for most items).

**Rationale**: The data is already fetched and available in the search result payload.
Zero additional API cost. Covers common cases: "1 medium apple = 182 g",
"1 large egg = 50 g", "1 slice bread = 28 g".

**Alternatives considered**: Always 100 g/piece — rejected because it's meaningfully
wrong for common items and the correct data is already in the payload.

---

## Schema Migration Strategy

**Decision**: Add two nullable columns to `daily_food_log_entries` and `custom_meal_items`
via SQLAlchemy `create_all` with `checkfirst=True` pattern (existing pattern in this repo).
On Vercel, `create_all` runs on first HTTP request via `_LazyASGI`.

**Columns added**:
- `entered_quantity FLOAT NULL` — the raw number the user typed
- `entered_unit VARCHAR(10) NULL` — the unit symbol (g, oz, lb, ml, piece, cup)

**Rationale**: Additive, nullable columns require no data migration and are
backward-compatible. Existing rows simply have NULL for both fields (displayed as grams).

**Alternatives considered**: Separate `unit_conversions` table — rejected as unnecessary
indirection for two simple scalar fields.

---

## Frontend Architecture

**Decision**: Introduce a single `frontend/lib/unit-conversions.ts` module exporting:
- `UNITS` — ordered array of `{ label, symbol, toGrams: (qty, servingSizeG?) => number }`
- `convertToGrams(qty: number, unit: string, servingSizeG?: number) => number`

UI: inline `<select>` element (Tailwind-styled to match existing inputs) rendered
immediately after the quantity `<input>` on the same row. No new component file needed
given its simplicity; if reused in 3+ places a `UnitSelect` component is appropriate.

**Rationale**: Keeps conversion logic testable and separate from UI. The select element
is the simplest accessible pattern for a small fixed option set (6 items).
