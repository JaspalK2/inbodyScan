# Quickstart: Fix Save Diet Day Plan Visibility (016)

## Scenarios

### Scenario 1 — Happy path: save succeeds, plan appears in both tabs
1. Generate a diet plan and navigate to the Recommendations → Diet tab
2. Expand Day 1, click "Save day"
3. **Expected**: Button shows spinner → "Day saved ✓" (green) appears briefly below the button → spinner disappears
4. Switch to Food & Meals tab → click "Saved" sub-tab
5. **Expected**: "Saved Day Plans" section shows "Day 1 meal plan" with 4 meal slot labels
6. Switch to Day Planner tab
7. **Expected**: "Day 1 meal plan" appears in the saved plans list at the bottom

### Scenario 2 — Error path: network failure shows inline error
1. Open browser DevTools → Network → set to Offline
2. Expand Day 1, click "Save day"
3. **Expected**: Spinner appears → spinner stops → "Failed to save — please try again." appears in red below the button
4. The plan does NOT appear in Saved Day Plans or Day Planner
5. Re-enable network → click "Save day" again → Scenario 1 plays out

### Scenario 3 — Empty meals guard is inline, not a blocking alert
1. (Requires sparse food DB or manual state manipulation) — all 4 meal slots have zero food items
2. Click "Save day"
3. **Expected**: "No meals to save — add foods first." appears inline in amber/red below the button; no browser alert box; no spinner; no API call

### Scenario 4 — Success message auto-clears after 3 seconds
1. Complete Scenario 1
2. Wait 3 seconds after "Day saved ✓" appears
3. **Expected**: The green message disappears automatically; button returns to normal state

## Fast unit test check
```bash
cd frontend && node_modules/.bin/vitest run __tests__/recommendations/ --no-coverage
```
