# Quickstart: Manual Integration Test Scenarios

**Feature**: 011-plans-fixes-workout-insight  
**Date**: 2026-04-05

Prerequisites: All services running (`./scripts/start-local.sh`), logged in as a test user with a profile that has `activity_level` set.

---

## Scenario 1: Diet Plan Calorie Totals Are Accurate

1. Navigate to **Plans → Food & Meals → AI Generated Plans**
2. Select an existing diet plan (or generate one)
3. Open any day (e.g. Day 1)
4. Manually add up the calories shown for each individual meal
5. **Expected**: The "Day Total" calories displayed equals your manual sum (±0 kcal)
6. Repeat for protein, carbs, fat
7. **Expected**: All macros match the sum of meal values

---

## Scenario 2: Activity Level Not Shown on Plans Page

1. Navigate to **Plans**
2. Inspect the "Generate Diet Plan" form
3. **Expected**: No activity level dropdown/selector is visible
4. Generate a diet plan
5. **Expected**: Plan generates successfully; macros match the profile's activity level (verify via macro targets shown in plan)

---

## Scenario 3: Saved Day Plans Appear in My Saved Meals

1. Navigate to **Plans → Food & Meals → AI Generated Plans**
2. Open a diet plan day and click **Log** (log the day)
3. Navigate to **Plans → Food & Meals → My Saved Meals**
4. **Expected**: The logged day plan appears with its name and date
5. Navigate to **Plans → Food & Meals → Day Planner**
6. **Expected**: The saved day plan is available in the Day Planner view

---

## Scenario 4: Delete Workout Plan

1. Navigate to **Plans → Workout → AI Generated Plans**
2. Ensure at least 2 workout plans exist (generate a second if needed)
3. On the older plan card, click the **Delete** button
4. **Expected**: A confirmation prompt appears ("Are you sure?")
5. Click **Cancel** — **Expected**: Plan is NOT deleted, returns to normal view
6. Click **Delete** again → **Confirm**
7. **Expected**: Plan is removed from the list immediately
8. Delete the last remaining plan
9. **Expected**: Empty state shown with prompt to generate a new plan

---

## Scenario 5: Workout Plan Explanation Shows Body Composition Context

1. Navigate to **Plans → Workout → AI Generated Plans**
2. Generate a new workout plan (requires a scan to be on file)
3. Open the newly generated plan
4. **Expected**: A "Why this plan?" explanation section appears at the **top** of the plan, before the exercise list
5. **Expected**: The explanation (2–4 sentences) references at least one body composition metric (e.g. lean mass, body fat %, muscle imbalance)
6. **Expected**: The explanation mentions what needs improvement AND what is already strong

---

## Scenario 6: Fallback for Plans Without Explanation

1. Open an **older** workout plan generated before this feature
2. **Expected**: Either the `summary` field is displayed in its place, or no explanation section is shown (no crash, no blank section)
