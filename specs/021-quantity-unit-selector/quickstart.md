# Quickstart: Food Log Quantity Unit Selector

## Smoke Test Scenarios

### Scenario 1 — Log food in ounces

1. Log in → Food & Meals → Search & Add tab
2. Search "chicken breast", click a result
3. In the add row: change unit dropdown from "g" to "oz", enter `6`
4. Click "Add to Today"
5. **Expect**: Food log shows "Chicken Breast — 6 oz (170 g)" with macros scaled to 170 g

### Scenario 2 — Log drink in ml

1. Search "orange juice", select a result
2. Change unit to "ml", enter `355`
3. Add to log
4. **Expect**: Entry shows "355 ml (355 g)" with macros for 355 g

### Scenario 3 — Log by piece with USDA serving size

1. Search "apple", select "Apple, raw" (USDA item with serving_size ≈ 182 g)
2. Change unit to "piece", enter `1`
3. Add to log
4. **Expect**: Entry shows "1 piece (182 g)" — NOT "1 piece (100 g)"

### Scenario 4 — Default is still grams

1. Search any food, check the unit dropdown on the add row
2. **Expect**: Default selection is "g"; entering `150` and adding logs 150 g exactly

### Scenario 5 — Custom meal builder

1. Food & Meals → Build a Meal tab
2. Search a food, add to pending meal
3. Change unit to "lb", enter `0.5`
4. Save meal
5. **Expect**: Saved meal item shows 226.8 g (0.5 lb × 453.592)

### Scenario 6 — Existing entries unaffected

1. Find a food log entry created before this feature
2. **Expect**: Entry displays in grams as before; no "(null)" or broken display

### Scenario 7 — Invalid quantity rejected

1. Change unit to "oz", type `0` or `-5`
2. **Expect**: Inline validation message; form does not submit
