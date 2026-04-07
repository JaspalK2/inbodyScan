# Quickstart: Workout Score Accuracy, Analytics Depth & Quality Polish

## Scenario 1 — Workout score always ≥95%

1. Go to Plans → generate a new workout plan
2. **Expect**: Score shown is between 95% and 100%
3. Generate 5 different plans (vary goal/muscle focus)
4. **Expect**: All 5 plans show score ≥95%

## Scenario 2 — Score updates on rep/set edits

1. Generate a workout plan
2. Note the current score (e.g., 97%)
3. Edit the sets on any exercise (increase or decrease)
4. **Expect**: Score updates immediately without page reload
5. Edit the reps on any exercise
6. **Expect**: Score updates immediately
7. Edit a duration or rest field (timed exercises)
8. **Expect**: Score updates immediately

## Scenario 3 — Analytics with 2+ scans

1. Ensure at least two InBody scans are uploaded
2. Go to Analytics
3. **Expect**: Delta cards visible at top (weight, fat %, SMM, BMI with ▲/▼)
4. **Expect**: Plain-language summary card visible
5. **Expect**: Trend charts for primary metrics
6. **Expect**: Muscle balance section (if segmental data present)

## Scenario 4 — Analytics with 1 scan

1. Log in with an account that has exactly one scan
2. Go to Analytics
3. **Expect**: Body composition snapshot shown (no trend charts)
4. **Expect**: Prompt to upload a second scan is visible
5. **Expect**: No blank/broken layout

## Scenario 5 — Analytics with 0 scans

1. Log in with an account that has no scans
2. Go to Analytics
3. **Expect**: Empty state message "Upload your first InBody scan to see analytics"
4. **Expect**: Call-to-action button linking to /scans

## Scenario 6 — Optimistic dietary restriction update

1. Go to Profile
2. Click to add a dietary restriction (e.g., "vegan")
3. **Expect**: The button highlights immediately (before server responds)
4. Click to remove it
5. **Expect**: The highlight clears immediately

## Scenario 7 — Optimistic goal change

1. Go to Profile
2. Click a different health goal
3. **Expect**: New goal highlights immediately
4. No loading spinner or lag visible

## Scenario 8 — Backend sync failure reverts UI

1. Simulate network failure (disable network or use dev tools)
2. Click a dietary restriction button
3. **Expect**: UI optimistically updates
4. **Expect**: After timeout, UI reverts to previous state and shows inline error

## Scenario 9 — Quality pass: empty states on all pages

1. Log in with a brand-new account (no scans, no plans, no profile data)
2. Visit: Dashboard, Scans, Analytics, Plans, Profile
3. **Expect**: Every page shows a helpful message with a call-to-action (no blank/broken layouts)

## Scenario 10 — Quality pass: loading indicators

1. On a slow connection (throttle to Slow 3G in browser dev tools)
2. Navigate between pages
3. **Expect**: Every page shows a spinner or skeleton while loading
