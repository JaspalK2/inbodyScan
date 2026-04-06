# Quickstart & Integration Scenarios: Profile & Diet Fixes (010)

## Prerequisites

- App running locally (`./start-local.sh`)
- Logged-in user with at least one InBody scan uploaded

---

## Scenario 1 — Profile Nav Near Sign Out

1. Open the app. Look at the left sidebar.
2. **Verify**: "Profile" link is **not** listed alongside Dashboard, Scans, Analytics, Plans.
3. **Verify**: A "Profile" link appears **above** the Sign Out button at the bottom of the sidebar.
4. Click the Profile link. Verify it navigates to `/profile`.

---

## Scenario 2 — Profile Data Saves and Loads

1. Navigate to `/profile`.
2. Enter: First Name = "Test", Age = 30, Weight = 75 kg, Activity Level = "Very Active".
3. Click "Save Profile".
4. **Verify**: A green "Saved!" confirmation appears briefly.
5. Reload the page.
6. **Verify**: All entered values are still shown in the form fields.
7. Change Weight to 80 kg, click Save, reload.
8. **Verify**: Weight shows 80 kg, not 75 kg.

---

## Scenario 3 — Goal Button Selected State Persists

1. Navigate to `/profile`.
2. Click "Build Muscle".
3. **Verify**: "Build Muscle" button shows a purple highlighted state; other buttons do not.
4. Reload the page.
5. **Verify**: "Build Muscle" is still highlighted.

---

## Scenario 4 — Dietary Restrictions Persist and Applied to Recommendations

1. Navigate to `/profile`.
2. Toggle "Vegetarian" on.
3. **Verify**: "Vegetarian" badge shows cyan active state with an × icon.
4. Reload. **Verify**: "Vegetarian" is still active.
5. Navigate to `/recommendations`, select a scan, click "Generate Diet Plan".
6. **Verify**: Generated meal plan contains no meat (chicken, beef, pork, fish).

---

## Scenario 5 — Diet Macro Totals Hit Targets

1. Navigate to `/recommendations`, select a scan, generate a diet plan.
2. Expand Day 1. Note the daily targets shown (e.g. 2400 kcal, 180g protein).
3. Sum the calories/protein/carbs/fat across all 4 meals of Day 1.
4. **Verify**: Each macro is within ±10% of the stated target.
5. Repeat for Day 2 and Day 7.

---

## Scenario 6 — Saved Days in My Saved Meals

1. Navigate to `/recommendations` → "Day Planner" tab.
2. Build a day plan (assign meals to Breakfast/Lunch/Dinner/Snack), name it "Test Day", click "Save Day".
3. Navigate to the "Food & Meals" tab.
4. Click "Saved" sub-tab.
5. **Verify**: A "Saved Day Plans" section appears showing "Test Day" with its meal slots.
6. **Verify**: Individual saved meals also appear in a separate "Saved Meals" section.

---

## Error State Validation

- With the user-service stopped, open `/profile` and click "Save Profile".
- **Verify**: An error message is shown ("Failed to save profile. Please try again.").
- **Verify**: The form retains all entered values after the error.
