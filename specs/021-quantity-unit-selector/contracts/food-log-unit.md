# API Contract: Food Log Unit Fields

## POST /api/recommendations/food-log

### Request body change (additive)

```json
{
  "log_date": "2026-04-06",
  "entries": [
    {
      "food_name": "Chicken Breast",
      "fdc_id": 171477,
      "quantity_g": 170.1,
      "entered_quantity": 6,
      "entered_unit": "oz",
      "calories_kcal": 187.0,
      "protein_g": 35.0,
      "carbs_g": 0.0,
      "fat_g": 4.0,
      "fiber_g": 0.0
    }
  ]
}
```

**`entered_quantity`** (number | null): the raw value the user typed. Optional.
**`entered_unit`** (string | null): one of `g | oz | lb | ml | piece | cup`. Optional.

Both fields are optional — existing callers that omit them are unaffected.
`quantity_g` MUST already be the gram-equivalent; the backend does not re-convert.

### Response change (additive)

`FoodLogEntryOut` now includes `entered_quantity` and `entered_unit` in the same
shape as the request. Null for pre-existing entries.

---

## PATCH /api/recommendations/custom-meals/{meal_id}/items (existing meal builder)

`MealItemIn` extended with the same two optional fields — `entered_quantity` and
`entered_unit`. The existing `quantity_g` field continues to carry the gram-equivalent.

---

## Frontend unit-conversions contract

```typescript
// frontend/lib/unit-conversions.ts

export type UnitSymbol = "g" | "oz" | "lb" | "ml" | "piece" | "cup";

export interface UnitOption {
  symbol: UnitSymbol;
  label: string;
  toGrams: (qty: number, servingSizeG?: number) => number;
}

export const UNITS: UnitOption[];

// Returns quantity converted to grams.
// servingSizeG is only used when symbol === "piece".
export function convertToGrams(
  qty: number,
  symbol: UnitSymbol,
  servingSizeG?: number
): number;
```
