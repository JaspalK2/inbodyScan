# Data Model: Food Log Quantity Unit Selector

## Entities Changed

### DailyFoodLogEntry (extended)

Table: `daily_food_log_entries`

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| id | VARCHAR(36) | NOT NULL | PK, unchanged |
| user_id | VARCHAR(36) | NOT NULL | unchanged |
| log_date | DATE | NOT NULL | unchanged |
| fdc_id | INTEGER | NULL | unchanged |
| food_name | VARCHAR(255) | NOT NULL | unchanged |
| brand | VARCHAR(255) | NULL | unchanged |
| source | VARCHAR(50) | NOT NULL | unchanged |
| source_ref_id | VARCHAR(36) | NULL | unchanged |
| quantity_g | FLOAT | NOT NULL | gram-equivalent (always populated) |
| calories_kcal | FLOAT | NULL | scaled to quantity_g — unchanged |
| protein_g | FLOAT | NULL | scaled to quantity_g — unchanged |
| carbs_g | FLOAT | NULL | scaled to quantity_g — unchanged |
| fat_g | FLOAT | NULL | scaled to quantity_g — unchanged |
| fiber_g | FLOAT | NULL | scaled to quantity_g — unchanged |
| **entered_quantity** | **FLOAT** | **NULL** | **NEW — raw value user typed** |
| **entered_unit** | **VARCHAR(10)** | **NULL** | **NEW — unit symbol (g/oz/lb/ml/piece/cup)** |
| created_at | DATETIME | NOT NULL | unchanged |

**Validation rules**:
- `entered_quantity` MUST be > 0 when provided
- `entered_unit` MUST be one of: g, oz, lb, ml, piece, cup when provided
- Both fields are nullable for backward compatibility with existing entries

---

### CustomMealItem (extended)

Table: `custom_meal_items`

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| id | VARCHAR(36) | NOT NULL | PK, unchanged |
| meal_id | VARCHAR(36) | NOT NULL | FK → custom_meals.id, unchanged |
| fdc_id | INTEGER | NULL | unchanged |
| food_name | VARCHAR(255) | NOT NULL | unchanged |
| quantity_g | FLOAT | NOT NULL | gram-equivalent — unchanged |
| calories_kcal | FLOAT | NULL | unchanged |
| protein_g | FLOAT | NULL | unchanged |
| carbs_g | FLOAT | NULL | unchanged |
| fat_g | FLOAT | NULL | unchanged |
| fiber_g | FLOAT | NULL | unchanged |
| sodium_mg | FLOAT | NULL | unchanged |
| **entered_quantity** | **FLOAT** | **NULL** | **NEW** |
| **entered_unit** | **VARCHAR(10)** | **NULL** | **NEW** |

---

## Unit Conversion Reference

| Symbol | Name | Grams per unit |
|--------|------|----------------|
| g | gram | 1.0 |
| oz | ounce | 28.3495 |
| lb | pound | 453.592 |
| ml | millilitre | 1.0 (water-density approx) |
| cup | US cup | 240.0 |
| piece | piece/item | USDA serving_size_g ?? 100.0 |
