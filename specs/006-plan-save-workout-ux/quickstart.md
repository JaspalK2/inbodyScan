# Quickstart / Integration Scenarios: Plan Save Flow and Workout UX Fixes (006)

These scenarios validate the full feature end-to-end against a running local stack.

---

## Scenario 1: Save Generated Diet Day → Verify Day Plan + Individual Meals Created

**Prerequisites**: Logged-in user with a generated diet plan visible.

1. Open Recommendations → Diet tab.
2. Expand any generated diet day (e.g., Day 1).
3. Click **"Save Day"** on that day.
4. **Expected**: Loading spinner on button → success toast "Day saved — 4 meals added to Saved Meals."
5. Navigate to **Food & Meals → Saved Meals** sub-tab.
6. **Expected**: Four new meal entries appear at the top: "Day Planner — Breakfast", "Day Planner — Lunch", "Day Planner — Dinner", "Day Planner — Snack" (only slots that had foods).
7. Navigate to **Day Planner** tab.
8. **Expected**: A new day plan record appears in the saved plans list with name "Day 1 — [goal_type]".

**Pass criteria**: Both the day plan and all non-empty meal slots appear in their correct tabs within 2 navigation actions.

---

## Scenario 2: Saved Meals Tab Shows Only Individual Meals (Not Day Plans)

**Prerequisites**: At least one saved day plan and at least one user-created custom meal exist.

1. Navigate to **Food & Meals → Saved Meals** sub-tab.
2. **Expected**: List shows individual custom meals ONLY (user-created + "Day Planner — [Slot]" meals). No "Day Plans" section is present.
3. Navigate to **Day Planner** tab.
4. **Expected**: Saved day plan records appear. Individual meal cards do NOT appear here.

**Pass criteria**: Each tab shows exactly its intended content type; no cross-contamination.

---

## Scenario 3: Exercise Labels Visible in Workout Plan View Mode

**Prerequisites**: At least one saved workout plan (AI-generated or custom split).

1. Navigate to **Recommendations → Workout** tab.
2. Open a saved workout plan or split.
3. Expand any non-rest training day.
4. **Expected**: Each exercise shows labelled data, e.g.:
   - "Bench Press · Sets: 3 · Reps: 8–12 · Weight: 60 kg · Rest: 90 s"
   - Fields with no value (e.g., no weight) are omitted rather than shown blank.

**Pass criteria**: No unlabelled numeric values visible.

---

## Scenario 4: Add Exercise to Generated Workout Plan in Edit Mode

**Prerequisites**: At least one AI-generated workout plan exists.

1. Open the generated workout plan → click **Edit**.
2. Expand Week 1, Day 1 (non-rest).
3. Click **"+ Add exercise"**.
4. **Expected**: A new exercise row appears with typeahead input (placeholder "Search exercise…"), Sets=3, Reps="8-12", Rest=60.
5. Type "squat" in the typeahead → select "Barbell Squat" from dropdown.
6. **Expected**: Score updates within 1 second.
7. Click the **remove** icon on the original first exercise.
8. **Expected**: Exercise disappears; score updates within 1 second.
9. Click **Save** → reload page.
10. **Expected**: Changes persist.

**Pass criteria**: Add/remove work; score updates after each; changes survive save and reload.

---

## Scenario 5: Remove Exercise in Edit Mode

**Prerequisites**: Generated workout plan with at least 2 exercises on Day 1.

1. Open plan → Edit → expand Day 1.
2. Click the remove icon on exercise row 1.
3. **Expected**: Row disappears immediately; score recalculates within 1 second; score value decreases (lower volume).

**Pass criteria**: Exercise removed in 1 click; score reflects change.

---

## Scenario 6: Live Score in Custom Split Builder

**Prerequisites**: User is on Workout → Split Builder tab.

1. Navigate to **Workout → Split** sub-tab.
2. Assign focus "Push" to Monday, add exercise "Bench Press" with sets=3, reps="8-12".
3. **Expected**: Live score panel appears below (or alongside) the split builder showing overall score and sub-scores.
4. Add another exercise to Wednesday.
5. **Expected**: Score updates within 1 second of adding the exercise.
6. Remove all exercises from Monday.
7. **Expected**: Score updates (decreases) within 1 second.

**Pass criteria**: Score visible and updating throughout split-building; no extra save action required to see score.

---

## Scenario 7: Error State — Save Day with Empty Meals

**Prerequisites**: Generated diet plan with all food lists cleared (or a day with no foods added yet).

1. Expand a day that has no food items in any meal slot.
2. Click **"Save Day"**.
3. **Expected**: Error toast or inline message "No meals to save — add foods first." No API calls made.

**Pass criteria**: Empty-day save is blocked with user-friendly feedback.
