# Quickstart: Fix Diet Plan Rendering Crash (014)

## Test Scenarios

### Scenario 1 — New algorithmic plan renders (P1 smoke test)
1. Log in and navigate to Recommendations page
2. Generate a diet plan (or use an existing one generated after feature 013 deploy)
3. Click the Diet tab
4. **Expected**: 7 day rows appear, no white screen, no console TypeError

### Scenario 2 — Day row expansion works
1. Click on "Day 1" row
2. **Expected**: Breakfast, Lunch, Dinner, Snack sections expand with:
   - Meal label displayed (e.g. "Breakfast")
   - Food items listed (e.g. "Chicken breast tenders, breaded, uncooked 45.2g")
   - Macro row: "X kcal · P Xg · C Xg · F Xg"

### Scenario 3 — Day header totals are correct
1. With Day 1 expanded, note the calories shown in the header
2. **Expected**: Header shows sum of all 4 meals' calories, NOT 0 kcal

### Scenario 4 — Old LLM plan backwards compatibility
1. If an old plan exists in DB (from before feature 013), render it
2. **Expected**: Visual output identical to before — no regression

### Scenario 5 — Editing mode (new format)
1. Click Edit on a new algorithmic diet plan
2. Expand Day 1 → Breakfast
3. **Expected**: Food items listed as strings with ✕ remove buttons
4. Click "Search & add food", search for "oats", add 50g
5. **Expected**: "50g Oats" appended to food list, macros updated

### Scenario 6 — Save day plan (new format)
1. In view mode, click "Save day" on Day 1
2. **Expected**: No crash; day plan saved; "Day 1 meal plan" appears in saved plans

## Fast unit test check
```bash
cd frontend && npx jest --testPathPattern="normaliseMeal" --no-coverage
```
All tests should pass before and after the fix.
