# Data Model: Fix Dietary Restriction Enforcement & Redesign Diet Plan Saved Meals UX

**Branch**: `018-diet-restrictions-plan-ux`  
**Date**: 2026-04-06

## No Schema Changes

This feature requires **no database migrations**. All required columns exist.

---

## Existing Tables Used

### `user_dietary_restrictions` (user-service)

| Column | Type | Notes |
|--------|------|-------|
| id | String PK | |
| user_id | String | Indexed; scoped to auth user |
| restriction_type | String(50) | e.g. `vegetarian`, `vegan`, `gluten_free`, `halal`, `kosher`, `no_dairy` |
| created_at | DateTime | |

**Usage**: Frontend reads this via `GET /api/users/me/dietary-restrictions`, maps `restriction_type` values, and passes them to the diet generate endpoint.

---

### `diet_recommendations` (recommendation-service)

| Column | Type | Notes |
|--------|------|-------|
| id | String PK | UUID; used as grouping key in `day_plans.notes` |
| user_id | String | Indexed |
| scan_id | String | |
| goal_type | String | |
| structured_plan | Text (JSON) | Full 7-day plan; `days[].meals[].items[]` with macros |
| edited_plan | Text (JSON) | Nullable; user-edited version |
| created_at | DateTime | Used as plan generation date for display label |

---

### `day_plans` (recommendation-service)

| Column | Type | Notes |
|--------|------|-------|
| id | String PK | |
| user_id | String | Indexed |
| name | String | Convention: `AI Plan YYYY-MM-DD (Day N)` for auto-saved plans |
| plan_date | Date | Nullable; set to generation date for auto-saved plans |
| notes | String | **Stores `recommendation_id`** — used to group 7 days into one plan block |
| created_at | DateTime | |
| updated_at | DateTime | |

---

### `day_plan_entries` (recommendation-service)

| Column | Type | Notes |
|--------|------|-------|
| id | String PK | |
| day_plan_id | String FK | → `day_plans.id` |
| meal_slot | String | `breakfast` \| `lunch` \| `dinner` \| `snack` |
| custom_meal_id | String | Nullable |
| custom_meal_name | String | Nullable; denormalized meal name |
| calories_kcal | Float | Meal total |
| protein_g | Float | |
| carbs_g | Float | |
| fat_g | Float | |
| fiber_g | Float | |
| items_snapshot | Text (JSON) | Snapshot of food items at save time |

---

## foods.json Data Fix

**File**: `services/recommendation-service/src/data/foods.json`

Six entries have incorrect restriction flags and must be corrected:

| Food Name | Current `vegetarian` | Correct `vegetarian` | Current `vegan` | Correct `vegan` |
|-----------|---------------------|---------------------|----------------|----------------|
| Chicken, thighs, frozen, breaded, reheated | `true` | `false` | `true` | `false` |
| ON THE BORDER, soft taco with ground beef, cheese and lettuce | `true` | `false` | `true` | `false` |
| Fish oil, salmon | `true` | `false` | `true` | `false` |
| Snacks, shrimp cracker | `true` | `false` | `true` | `false` |
| APPLEBEE'S, Double Crunch Shrimp | `true` | `false` | `true` | `false` |
| DENNY'S, golden fried shrimp | `true` | `false` | `true` | `false` |

---

## UI Data Flow for Redesigned Saved Plans

```
GET /api/recommendations/day-plans
  → list of DayPlan records ordered by created_at DESC
  → group by notes (= recommendation_id)
  → for each group: show one collapsible card
      label: created_at date of first plan in group
      expanded: Day 1..7 rows
        each day row: expandable → meal_slot entries with items_snapshot macros
```
