# Data Model: Food & Meal Tracker Enhancements

**Feature**: 002-food-meal-tracker  
**Date**: 2026-04-02

---

## New Table: `daily_food_log_entries`

Stores all food items a user has explicitly logged as consumed on a specific date. This is the single source of truth for the macro pie chart.

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | UUID | PK, default uuid4 | |
| `user_id` | VARCHAR(36) | NOT NULL, indexed | Scoped per user |
| `log_date` | DATE | NOT NULL, indexed | Date the food was consumed |
| `fdc_id` | INTEGER | nullable | USDA FDC ID if from food search |
| `food_name` | VARCHAR(255) | NOT NULL | Stored at log time (denormalised) |
| `brand` | VARCHAR(255) | nullable | Restaurant/brand name if applicable |
| `source` | VARCHAR(50) | NOT NULL, default 'manual' | `manual`, `diet_plan`, `saved_meal` |
| `source_ref_id` | VARCHAR(36) | nullable | FK to `diet_recommendations.id` or `custom_meals.id` for traceability |
| `quantity_g` | FLOAT | NOT NULL | Quantity consumed in grams |
| `calories_kcal` | FLOAT | nullable | Computed at log time from quantity |
| `protein_g` | FLOAT | nullable | Computed at log time |
| `carbs_g` | FLOAT | nullable | Computed at log time |
| `fat_g` | FLOAT | nullable | Computed at log time |
| `fiber_g` | FLOAT | nullable | Computed at log time |
| `created_at` | TIMESTAMP | NOT NULL, default now() | |

**Indexes**:
- `(user_id, log_date)` composite index — primary query pattern for fetching a day's log
- `user_id` index — for history queries

**Constraints**:
- No unique constraint on `(user_id, log_date, fdc_id)` — duplicate entries of the same food on the same day are allowed (FR-012)
- No TTL or expiry — retained indefinitely (Clarification Q3)

---

## Existing Tables Modified

### `diet_recommendations`

No schema change. The existing `edited_plan` TEXT column (already present) stores user-modified plan JSON. The "Log this meal" button reads from `structured_plan` or `edited_plan` (whichever is current) to create a `daily_food_log_entry`.

### `workout_recommendations`

No schema change. The existing `edited_plan` TEXT column is used for the live quality score feedback. The workout scorer runs client-side from the plan JSON.

---

## Unchanged Tables (reused as-is)

| Table | Used for |
|-------|---------|
| `custom_meals` + `custom_meal_items` | Saved meal shortcuts — read to populate "Saved" section; "Add to Today" creates a `daily_food_log_entry` with `source=saved_meal` per item |
| `nutritional_foods` | Not directly used — food search uses live USDA API calls |

---

## Entity Relationships

```
users (auth_users)
  └── daily_food_log_entries (user_id → user.id)
        ├── source='manual'      → created from food search
        ├── source='diet_plan'   → source_ref_id → diet_recommendations.id
        └── source='saved_meal'  → source_ref_id → custom_meals.id

diet_recommendations
  └── structured_plan / edited_plan (JSON) → parsed client-side for "Log this meal"

custom_meals → custom_meal_items
  └── "Add to Today" shortcut → creates daily_food_log_entries per item
```

---

## Derived: Macro Pie Chart State (client-side)

Not stored. Computed on the frontend by summing `daily_food_log_entries` for the selected date:

```
total_protein_g  = Σ entry.protein_g  (where entry.log_date = selected_date)
total_carbs_g    = Σ entry.carbs_g
total_fat_g      = Σ entry.fat_g
total_calories   = Σ entry.calories_kcal

overflow_protein = total_protein_g  > target_protein_g
overflow_carbs   = total_carbs_g    > target_carbs_g
overflow_fat     = total_fat_g      > target_fat_g
```

Targets come from the existing macro calculator (`/api/recommendations/diet/macros`).
