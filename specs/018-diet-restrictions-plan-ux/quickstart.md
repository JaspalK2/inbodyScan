# Quickstart / Integration Scenarios

**Branch**: `018-diet-restrictions-plan-ux`  
**Date**: 2026-04-06

## Scenario 1: Vegetarian Restriction Enforced (US1 — P0 Safety)

```
1. In user profile, set dietary restriction: "vegetarian"
2. Navigate to Recommendations tab
3. Click "Generate Diet Plan"
4. Wait for generation to complete
5. Inspect all 7 days × 4 meal slots × N items
Expected: Zero items with vegetarian:false in foods.json appear
Expected: Specifically, "Chicken, thighs", "APPLEBEE'S Double Crunch Shrimp", 
          "DENNY'S golden fried shrimp", salmon, tuna, shrimp are all absent
```

### Backend validation script (pytest):
```bash
cd services/recommendation-service
python3 -m pytest tests/test_diet_restrictions.py -v
```

Expected: All tests pass including `test_vegetarian_no_meat_in_plan` and `test_vegan_no_animal_products`.

---

## Scenario 2: Vegan Restriction Enforced (US1)

```
1. Set profile restriction: "vegan"
2. Generate diet plan
3. Inspect all items
Expected: No meat, fish, dairy, eggs, or honey items
```

---

## Scenario 3: Multiple Restrictions Simultaneously (US1 Edge Case)

```
1. Set profile restrictions: ["vegetarian", "gluten_free"]
2. Generate diet plan
3. Inspect items
Expected: No meat/fish AND no gluten-containing items
```

---

## Scenario 4: Auto-Save on Generation (US2)

```
1. Navigate to Food & Meals tab → My Saved Meals
2. Note current number of saved plan blocks (N)
3. Generate a new diet plan
4. Navigate back to Food & Meals → My Saved Meals
5. Expected: N+1 plan blocks visible, newest at top
6. Expected: New block is labelled with today's date (e.g. "April 6, 2026")
7. Expected: No "Save day" button visible anywhere in the diet plan view
```

---

## Scenario 5: Expand Plan Block (US2)

```
1. In My Saved Meals, click the newest plan block
2. Expected: Block expands to show 7 day rows (Day 1 through Day 7)
3. Click "Day 1" row
4. Expected: Row expands to show breakfast, lunch, dinner, snack entries
5. Each meal entry shows: meal name, food items, and macro totals
```

---

## Scenario 6: Delete a Plan Block (US2)

```
1. In My Saved Meals, hover/tap a plan block
2. Click delete (trash icon)
3. Expected: Confirmation prompt or immediate removal
4. Expected: Block no longer appears in list
5. Refresh page — Expected: Block still gone (server-side deletion confirmed)
```

---

## Scenario 7: No Restrictions User (US1 Regression)

```
1. Remove all dietary restrictions from profile
2. Generate a diet plan
3. Expected: Plan generates normally with no filtering applied
4. Expected: Caloric accuracy within ±5% (existing requirement)
```

---

## Backend Test Commands

```bash
# US1 — restriction data fix tests
cd services/recommendation-service
python3 -m pytest tests/test_diet_restrictions.py -v

# US1 — regression: all existing tests still pass
python3 -m pytest tests/test_diet_engine.py -v

# US2 — frontend component tests
cd ../../frontend
npx vitest run __tests__/recommendations/
```
