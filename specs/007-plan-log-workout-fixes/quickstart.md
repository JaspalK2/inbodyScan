# Quickstart / Integration Scenarios: Plan Log and Workout Fixes (007)

## Prerequisites

- Local dev stack running: `http://localhost:3000/`
- At least one InBody scan uploaded (to unlock recommendations tab)
- Recommendation service running on port 8004

---

## Scenario 1: Verify Nested Button Fix (WorkoutPlanCard)

1. Open http://localhost:3000/ → Recommendations → Workouts tab
2. Open browser DevTools console
3. Click any workout plan card to expand it
4. **Expected**: No console error about "button cannot appear as a descendant of button"
5. Click the "Edit" button inside the expanded card
6. **Expected**: Edit mode opens normally

---

## Scenario 2: Delete a Diet Plan

1. Open http://localhost:3000/ → Recommendations → Diet tab
2. Generate at least 2 diet plans if none exist
3. Click the trash icon on any diet plan card
4. **Expected**: Confirmation prompt appears: "Delete this diet plan? This cannot be undone."
5. Click Cancel → plan remains
6. Click trash again → confirm deletion
7. **Expected**: Plan disappears from list immediately
8. Refresh page → plan is still gone

---

## Scenario 3: Free-Edit Sets in Workout Plan

1. Open http://localhost:3000/ → Recommendations → Workouts tab
2. Expand a generated workout plan → click Edit
3. Find an exercise with sets = 3
4. Click the Sets input, select all, type "8"
5. **Expected**: Field shows "8" immediately (does not revert to 3)
6. Clear the field entirely (backspace to empty)
7. **Expected**: Field is empty (does not revert)
8. Type "5" → click Save
9. **Expected**: Plan saved; reload shows sets = 5

---

## Scenario 4: Saved Meals Tab — Two Sections

1. Open http://localhost:3000/ → Recommendations → Diet tab
2. Save Day 1 from a generated diet plan (click "Save Day" on Day 1)
3. Save Day 2 from the same plan
4. Open Food & Meals tab → Saved Meals sub-tab
5. **Expected**:
   - "Day Planner Meals" section visible with sub-headings "Day 1" and "Day 2"
   - Meals like "Day Planner — Breakfast", "Day Planner — Lunch" grouped under correct day
6. Create a custom meal manually
7. **Expected**: "My Meals" section shows the user-created meal
8. Sections without content are hidden; if both empty, single empty state message shown

---

## Scenario 5: Log This Day from Day Planner

1. Save Day 1 from a generated diet plan (ensures items_snapshot populated)
2. Navigate to Day Planner tab
3. **Expected**: The saved day plan appears in the list
4. Click "Log this day" (BookmarkPlus icon)
5. Navigate to Food Log for today
6. **Expected**: Individual food items from Day 1 meal slots appear as log entries (not just macro totals)

---

## Scenario 6: Workout Plan Scores 100/100

1. Delete all existing workout plans (or use a fresh account)
2. Open http://localhost:3000/ → Recommendations → Workouts tab
3. Click "Generate Workout Plan"
4. Wait for generation to complete
5. **Expected**: Quality score shows **100/100** without any edits
6. Remove one exercise from a day
7. **Expected**: Score drops below 100
