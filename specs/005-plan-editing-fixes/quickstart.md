# Quickstart / Integration Scenarios: Plan Editing and Log Fixes (005)

Manual validation scenarios. Run against a local stack (`bash scripts/start-local.sh`) with a user account that has at least one InBody scan uploaded and a generated diet + workout plan.

---

## Scenario 1 — Save a meal from the diet plan (view mode)

1. Navigate to Recommendations → Diet tab.
2. Expand the generated plan → expand Day 1.
3. Click **"Save meal"** on the Breakfast row (view mode, not editing).
4. A success toast appears ("Breakfast saved to your meals").
5. Navigate to Food & Meals → Saved Meals tab.
6. **Assert**: A new entry labelled "breakfast — [goal] plan" (or similar) appears with the correct food items and macro summary.

---

## Scenario 2 — Save an edited meal from the diet plan

1. Open Diet tab → expand Day 1.
2. Click **Edit** on the plan card.
3. Expand Day 1 breakfast → use "Search & add food" to add "100g banana".
4. Click **"Save meal"** on the Breakfast row.
5. **Assert**: Saved meal in Food & Meals → Saved Meals includes "100g banana" in its food list and the updated macro total.

---

## Scenario 3 — Saved day plans appear in Saved Meals tab

1. From the Diet tab, expand Day 2 and click **"Save day"** in the day row header.
2. Navigate to Food & Meals → Saved Meals tab.
3. **Assert**: A "Day Plans" section is visible below the individual saved meals section.
4. **Assert**: The saved day plan entry is listed with its name (e.g. "Day 2 meal plan").
5. Expand the day plan entry → **Assert**: All meal slots (breakfast, lunch, dinner, snack) are listed with their food items.

---

## Scenario 4 — Apply saved day plan from Day Planner to food log

1. Ensure at least one day plan has been saved (from Scenario 3 or prior).
2. Navigate to Food & Meals → Day Planner tab.
3. Select today's date.
4. Click **"Use saved plan"** (or equivalent button).
5. A picker appears showing saved day plans → select the plan saved in Scenario 3.
6. Confirm the selection.
7. **Assert**: The Day Planner for today now shows all meal slots populated from the plan.
8. Navigate to the food log for today.
9. **Assert**: All food items from the day plan appear as food log entries for today's date.

---

## Scenario 5 — Exercise typeahead search in workout plan editor

1. Navigate to Recommendations → Workout tab.
2. Open the workout plan → click **Edit**.
3. Expand Week 1 → Day 1 → click on any exercise name (e.g. "Bench Press").
4. **Assert**: The name field becomes a text input.
5. Type "squat" (2+ characters).
6. **Assert**: A dropdown appears within 1 second showing exercises matching "squat" (e.g. "Barbell Squat", "Goblet Squat", etc.).
7. Select "Barbell Squat".
8. **Assert**: The exercise name updates and the workout quality score recalculates within 1 second.
9. Click **"Add exercise"** on any workout day.
10. Search for "deadlift" → select "Romanian Deadlift" → set sets=3, reps="8-10" → confirm.
11. **Assert**: The new exercise appears in the day's list and the score updates.
12. Click **Save** → reload the page.
13. **Assert**: Both the replaced exercise and the added exercise persist.

---

## Scenario 6 — Empty states and validation

1. In edit mode, remove all food items from a meal → click **"Save meal"**.
   - **Assert**: Save is blocked; validation message "Meal must have at least one food item" is shown.
2. In Day Planner with no saved day plans, click **"Use saved plan"**.
   - **Assert**: Empty state shown: "No saved day plans yet — save a day plan from the Diet tab."
3. In workout edit mode, type a query that matches nothing (e.g. "zzzzxxx").
   - **Assert**: Dropdown shows "No exercises found — try different keywords."
