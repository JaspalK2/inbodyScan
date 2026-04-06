# Quickstart & Validation Scenarios: Editable AI-Generated Plans

**Feature**: 004-editable-ai-plans  
**Date**: 2026-04-02  
**Pre-condition**: Local stack running (`bash scripts/start-local.sh`), user logged in with at least one scan uploaded.

---

## Scenario 1: Generate Workout Plan (happy path)

1. Navigate to Recommendations page
2. Click **Generate Workout Plan**
3. Observe loading state (spinner or progress indicator)
4. Within 30 seconds, a workout plan appears with:
   - Section headers per week/day
   - Exercises with name, sets, reps listed
   - A workout quality score (0–100) displayed prominently

**Pass criteria**: Plan rendered, score visible, no error message.

---

## Scenario 2: Generate Diet Plan (happy path)

1. Navigate to Recommendations page
2. Click **Generate Diet Plan**
3. Within 30 seconds, a 7-day meal plan appears with:
   - Meals per day (breakfast, lunch, dinner, snack)
   - Per-meal macro values
   - A macro pie chart (protein / carbs / fat)

**Pass criteria**: Plan rendered, pie chart visible with three coloured slices, no error message.

---

## Scenario 3: Gemini Quota Error (503 error handling)

To test without exhausting real quota, mock the error:

```python
# In gemini_client.py temporarily:
from google.api_core.exceptions import ResourceExhausted
raise ResourceExhausted("quota exceeded")
```

1. Attempt to generate either plan
2. Observe the UI response

**Pass criteria**: A user-friendly message appears (e.g. "Plan generation is temporarily unavailable — please try again shortly.") with a **Retry** button. No "500 Internal Server Error" shown. Remove the mock after testing.

---

## Scenario 4: No Scan Uploaded

1. Log in as a user with no scans
2. Navigate to Recommendations page
3. Attempt to generate a plan

**Pass criteria**: User sees a prompt to upload a scan first; generate button is disabled or redirects to scan upload.

---

## Scenario 5: Edit Workout Plan — Live Score Update

1. Generate (or view an existing) workout plan
2. Click **Edit** to enter edit mode
3. Change the **reps** value on any exercise (e.g. from "8-10" to "4-6")
4. Within 1 second: the workout quality score updates to reflect the change (score may increase or decrease)
5. Change **sets** on another exercise
6. Verify score updates again within 1 second

**Pass criteria**: Score changes within 1 second of each edit, without a page reload.

---

## Scenario 6: Save Edited Workout Plan

1. While in edit mode (Scenario 5), make at least one change
2. Click **Save**
3. Reload the page (hard refresh)

**Pass criteria**: The edited exercise values are displayed (not the original AI-generated values), and the score matches the edited plan.

---

## Scenario 7: Discard Workout Edits

1. While in edit mode, change an exercise's sets from the original value
2. Click **Discard**

**Pass criteria**: All exercise values revert to the last saved state; the score reverts to match the last saved plan; edit mode is exited.

---

## Scenario 8: Edit Diet Plan — Live Macro Chart Update

1. Generate (or view) a diet plan
2. Click **Edit** to enter edit mode
3. Increase the `protein_g` value on a meal
4. Within 1 second: the protein slice of the macro pie chart grows visibly

**Pass criteria**: Pie chart updates within 1 second of the edit, without a page reload.

---

## Scenario 9: Save Edited Diet Plan

1. While in diet edit mode, change at least one macro value or meal name
2. Click **Save**
3. Reload the page

**Pass criteria**: Edited values persist; pie chart reflects saved macros.

---

## Scenario 10: Re-generate When Edited Plan Exists

1. Generate and save edits to a workout plan
2. Click **Generate Workout Plan** again

**Pass criteria**: A confirmation dialog appears asking whether to overwrite the existing plan. Confirming generates a new plan and clears edits. Cancelling leaves the existing plan unchanged.

---

## Scenario 11: Invalid Exercise Values (validation)

1. Enter workout edit mode
2. Change sets to `0` for an exercise
3. Attempt to save

**Pass criteria**: Inline validation error shown ("Sets must be at least 1"). Save is blocked until corrected.

---

## Scenario 12: Zero-gram Food Portion

1. Enter diet edit mode
2. Set a meal's portion size (or `protein_g` / `carbs_g`) to `0`
3. Observe macro chart

**Pass criteria**: That meal's contribution is excluded from macro totals. If total daily calories fall below a safe minimum (e.g. 1200 kcal), a warning is displayed. Save is not blocked (user may be intentionally removing an item).
