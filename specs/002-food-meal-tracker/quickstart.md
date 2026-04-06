# Quickstart: Food & Meal Tracker Enhancements

**Feature**: 002-food-meal-tracker  
**Date**: 2026-04-02

---

## Prerequisites

- All services from feature 001 running (`./scripts/start-local.sh`)
- `.env` populated with `USDA_API_KEY`, all `*_DATABASE_URL` vars, and `JWT_SECRET_KEY`
- An existing user account with at least one InBody scan uploaded (for macro targets)

---

## Database Setup

Run the following SQL in your Supabase project to create the new table:

```sql
CREATE TABLE daily_food_log_entries (
  id            VARCHAR(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
  user_id       VARCHAR(36) NOT NULL,
  log_date      DATE NOT NULL,
  fdc_id        INTEGER,
  food_name     VARCHAR(255) NOT NULL,
  brand         VARCHAR(255),
  source        VARCHAR(50) NOT NULL DEFAULT 'manual',
  source_ref_id VARCHAR(36),
  quantity_g    FLOAT NOT NULL,
  calories_kcal FLOAT,
  protein_g     FLOAT,
  carbs_g       FLOAT,
  fat_g         FLOAT,
  fiber_g       FLOAT,
  created_at    TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE INDEX idx_food_log_user_date ON daily_food_log_entries (user_id, log_date);
CREATE INDEX idx_food_log_user      ON daily_food_log_entries (user_id);
```

---

## Validation Scenarios

### 1. Restaurant meal search
1. Open the app → Recommendations → Food & Meals tab
2. Search for "Big Mac" — confirm results include an item with `brand = "McDonald's"` or similar
3. Search for "Chipotle chicken" — confirm branded results appear

### 2. Log food and see pie chart update
1. Search for "chicken breast"
2. Set quantity to 200 g → tap "Add to Today"
3. Confirm the item appears in today's food log
4. Confirm the macro pie chart updates to reflect protein/carbs/fat values

### 3. Macro overflow state
1. Log multiple high-protein foods until protein total exceeds daily target
2. Confirm the protein slice of the pie chart shows the overflow state (different color or label)

### 4. Saved meal shortcut
1. Save a custom meal via the Food & Meals tab
2. Scroll to the "Saved" section — confirm the meal appears with an "Add to Today" button
3. Tap the button — confirm all meal items are logged and the pie chart updates

### 5. AI diet plan — Log this meal
1. Generate a diet plan (requires active scan + health goal)
2. On any plan meal, tap "Log this meal"
3. Confirm the meal's macros now appear in the food log and pie chart for today

### 6. Edit AI diet plan — live macro preview
1. On a generated diet plan meal, change the quantity
2. Confirm the inline macro preview updates immediately (no page reload)
3. Tap "Log this meal" after the edit — confirm the edited quantity's macros are logged

### 7. Edit AI workout plan — live quality score
1. Generate a workout plan
2. Remove all cardio exercises from the plan
3. Confirm the cardio sub-score decreases in the quality score display immediately

### 8. Date navigation
1. Log a food item for today
2. Use the date picker to navigate to yesterday
3. Confirm today's logged items are not shown; yesterday's log (if any) is shown instead

### 9. Persistence
1. Edit and save a diet plan
2. Log out and log back in
3. Confirm the edited plan is still shown with the saved edits intact
