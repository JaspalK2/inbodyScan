# Feature Specification: Workout & Diet UX Fixes

**Feature Branch**: `009-workout-diet-ux-fixes`  
**Created**: 2026-04-05  
**Status**: Draft  
**Input**: User description: "the workout recommended plan should just be one week worth of workouts, not multiple weeks with different days, the user should just commit to one week. The score for a generated workout should not be anything under 90/100. Active edits that the user makes to the workout recommended should show the effect on the score, with a point system for feedback. For the diet system it should be far more condensed, the days should be in their own condensed boxes. Find a better naming convention than 'Day - Planner Breakfast' as that is repetitive. Remove the saving of individual meals from the day planner. For the day planner meal selector, use a small expandable box showing saved days and saved meals. Adding meals in the manual planner should actually update the macro bars visually. Fix the token expired error on the recommendations page."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fix Token Expiry on Recommendations Page (Priority: P1)

When a user's authentication token expires, the recommendations page shows a token expired error instead of transparently refreshing and retrying. This blocks users from accessing their core recommendations.

**Why this priority**: Functional blocker — users cannot access the app's main feature.

**Independent Test**: Expire a user token (or simulate expiry), navigate to recommendations page, and verify the page loads without error.

**Acceptance Scenarios**:

1. **Given** a user's access token has expired, **When** they visit the recommendations page, **Then** the token is silently refreshed and the page loads normally with no error shown.
2. **Given** a token refresh fails because the session is fully expired, **When** they visit the recommendations page, **Then** they are redirected to login with a clear message.

---

### User Story 2 - Single-Week Workout Plan with 90+ Score Floor (Priority: P1)

A user generates a workout plan and expects one week of workouts. Currently the plan shows multiple weeks. Additionally, plans receive scores below 90, which signals poor quality.

**Why this priority**: The plan structure is fundamentally wrong and low scores undermine user trust in the app.

**Independent Test**: Generate a new workout plan and verify it shows exactly one week of workouts with a score at or above 90.

**Acceptance Scenarios**:

1. **Given** a user generates a workout plan, **When** the plan is displayed, **Then** it shows only one week of workouts with no additional weeks visible.
2. **Given** a workout plan is generated, **When** the quality score is computed, **Then** the score is always 90 or higher out of 100.
3. **Given** a user views and commits to the one-week plan, **When** they save it, **Then** the single week is saved as their active workout commitment.

---

### User Story 3 - Real-Time Score Feedback on Workout Edits (Priority: P2)

When a user edits their workout plan (swaps exercises, changes sets/reps), the score should update immediately with a visible point delta so the user always receives feedback on their changes.

**Why this priority**: Without feedback, users don't understand the impact of edits and engagement drops.

**Independent Test**: Edit one exercise in a generated workout plan and verify the score updates with a visible delta indicator.

**Acceptance Scenarios**:

1. **Given** a user is viewing a workout plan with a score, **When** they edit any exercise or parameter, **Then** the score updates immediately.
2. **Given** an edit produces a score change smaller than 1 point, **When** the update is displayed, **Then** a decimal delta indicator relative to the original generated score (e.g., "−0.2 pts from original") is shown so the user knows the change had an effect.
3. **Given** an edit reduces the score, **When** the update is displayed, **Then** a negative delta is shown in a distinct color (e.g., red).

---

### User Story 4 - Condensed Diet Day Planner with Simplified Labels (Priority: P2)

The diet day planner is visually verbose. Days should each be in a compact, bordered card. The meal label "Day - Planner Breakfast" is redundant and must be simplified.

**Why this priority**: Overly verbose layout reduces usability and makes the planner hard to scan.

**Independent Test**: Open the day planner and verify each day is in a compact card with labels like "Breakfast" (not "Day 1 - Planner Breakfast").

**Acceptance Scenarios**:

1. **Given** a user opens the diet day planner, **When** the page loads, **Then** each day is displayed in its own compact, visually distinct card or collapsible box.
2. **Given** a meal slot is shown, **When** its label is rendered, **Then** it shows only the meal type (e.g., "Breakfast", "Lunch", "Dinner") without any day-name or "Planner" prefix.
3. **Given** a day card is collapsed, **When** the user clicks to expand, **Then** all meal slots for that day are revealed.

---

### User Story 5 - Remove Individual Meal Save from Day Planner (Priority: P2)

The ability to save individual meals directly from the day planner should be removed. Users who want a specific meal can save the whole day and retrieve it from "My Saved Meals".

**Why this priority**: Simplifies the UI by removing a redundant path that adds visual clutter.

**Independent Test**: Open a day in the day planner and verify there is no "Save Meal" button on any individual meal slot.

**Acceptance Scenarios**:

1. **Given** a user views any day in the day planner, **When** they look at individual meal slots, **Then** there is no option to save individual meals from that slot.
2. **Given** a user wants to reuse a specific meal from a planned day, **When** they save the whole day and navigate to "My Saved Meals", **Then** they can access that meal within the saved day.

---

### User Story 6 - Compact Expandable Meal Selector in Day Planner (Priority: P2)

When a user selects a meal for a slot in the day planner, the current large dropdown should be replaced with a compact, expandable box showing saved days and individually saved meals in separate sections.

**Why this priority**: The current large dropdown is visually disruptive and doesn't leverage saved data well.

**Independent Test**: Click the meal selector for a planner slot and verify a compact box appears that expands to show saved days and saved meals.

**Acceptance Scenarios**:

1. **Given** a user clicks the meal selector for a day planner slot, **When** the selector opens, **Then** a small compact box appears (not a full-width dropdown).
2. **Given** the compact selector is open, **When** the user expands it, **Then** it shows a "Saved Days" section (if any exist) and a "Saved Meals" section for individually created meals.
3. **Given** no saved days or meals exist, **When** the selector opens, **Then** an appropriate empty state is shown within the compact box.

---

### User Story 7 - Macro Bars Visually Update in Manual Planner (Priority: P1)

When a user adds meals in the manual planner, the macro numbers update but the visual progress bars do not move. The bars must visually update in sync with the numeric totals.

**Why this priority**: The macro bars are the primary visual feedback mechanism for nutrition — a static bar while numbers change is a broken core interaction.

**Independent Test**: Add a meal in the manual planner and verify the macro progress bars visually expand/contract proportionally.

**Acceptance Scenarios**:

1. **Given** a user is on the manual planner with a set daily target, **When** they add a meal, **Then** the macro progress bars (calories, protein, carbs, fat) visually update their widths to reflect the new totals.
2. **Given** a meal is removed from the manual planner, **When** the update occurs, **Then** the macro bars visually shrink proportionally.
3. **Given** the total exceeds the daily target for a macro, **When** displayed, **Then** the bar is filled and shows an over-target indicator.

---

### Edge Cases

- What if a workout edit drops the score below 90 — is it allowed to go below 90 post-generation? (Assumption: yes, edits can drop below; the floor only applies to the initial generation.)
- What if a token refresh returns an error mid-session during a recommendations data load — retry once, then redirect to login.
- What if the day planner meal selector is opened and there are no saved days or meals — show an empty state with a prompt to create/save meals.
- What if macro targets are zero or not set — bars should show a neutral state rather than dividing by zero.

## Requirements *(mandatory)*

### Functional Requirements

**Authentication**

- **FR-001**: When an access token is expired on the recommendations page, the system MUST silently refresh the token and reload the recommendation data without displaying any error.
- **FR-002**: If a token refresh fails (session fully expired), the system MUST redirect the user to the login page with a clear informational message.

**Workout Plan**

- **FR-003**: The generated workout plan MUST display exactly one week of workouts; no multi-week structure may be shown.
- **FR-004**: The workout plan generation logic MUST produce a quality score of 90 or higher for every plan generated.
- **FR-005**: When a user edits any element of the workout plan, the score MUST recalculate and update in real time using a client-side deterministic rule set (no backend call required per edit).
- **FR-006**: Every score change MUST be displayed with a signed decimal delta indicator relative to the original AI-generated score (e.g., "−3.5 pts from original", "+1.2 pts from original"), including changes smaller than 1 point.
- **FR-007**: Negative score deltas MUST be visually differentiated from positive deltas (e.g., via color).

**Diet / Day Planner**

- **FR-008**: Each day in the diet day planner MUST be displayed in its own compact, visually distinct card or collapsible box.
- **FR-009**: Meal slot labels MUST use only the meal type name (e.g., "Breakfast") and MUST NOT include a day-name prefix or the word "Planner".
- **FR-010**: The ability to save individual meals directly from within day planner slots MUST be removed from the UI.
- **FR-011**: The meal selector within each day planner slot MUST be a compact, expandable widget that fits within a single-line height when collapsed.
- **FR-012**: When expanded, the meal selector MUST show a "Saved Days" section and a "Saved Meals" section as distinct groups.
- **FR-013**: Adding or removing any meal in the manual planner MUST cause all macro progress bars to visually update their widths proportionally to the updated totals vs. daily targets.

### Key Entities

- **Workout Plan**: A single-week collection of training days with a quality score (90–100 at generation).
- **Workout Score**: A numeric 0–100 rating recomputed on every user edit, with a signed delta shown.
- **Day Plan**: One day entry in the diet day planner, displayed as a compact card with named meal slots.
- **Meal Slot**: A named position within a day (Breakfast, Lunch, Dinner, Snack) assignable via the compact meal selector.
- **Saved Day**: A previously saved full-day meal plan available in the meal selector.
- **Saved Meal**: An individually created meal available in the meal selector.
- **Macro Bar**: A visual progress indicator showing current intake vs. daily target for each macro nutrient.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The token expired error on the recommendations page is eliminated; transparent refresh succeeds 100% of the time when a valid refresh token exists.
- **SC-002**: 100% of newly generated workout plans have a quality score of 90 or above.
- **SC-003**: Score delta feedback appears within 500 ms of any workout plan edit, for changes as small as 0.1 points.
- **SC-004**: The diet day planner displays all days in compact individual cards; zero meal labels contain a day-name or "Planner" prefix.
- **SC-005**: Macro progress bars visually update within 200 ms of any meal addition or removal in the manual planner.
- **SC-006**: The meal selector in the day planner collapses to single-line height and expands on interaction to reveal categorised saved days and meals.
- **SC-007**: No individual meal-save controls are present on any meal slot within the day planner.

## Clarifications

### Session 2026-04-05

- Q: Is workout score recalculation on edit computed client-side or via a backend call? → A: Client-side using a local deterministic rule set (no backend call per edit).
- Q: Is the score delta shown relative to the previous edit or the original AI-generated score? → A: Relative to the original AI-generated score (cumulative drift indicator).

## Assumptions

- The initial workout score is generated by the backend recommendation service (enforcing the 90-point floor there); post-generation edits are scored client-side using a derived deterministic rule set, making real-time feedback instant.
- "One week" means the user's configured training days within a 7-day period (e.g., a 4-day split shows 4 training days); rest days may be shown as rest entries.
- Edits to the workout plan that drop the score below 90 are permitted post-generation; the 90-point floor applies only at generation time.
- The macro bar bug is a frontend state/rendering issue where bar widths are not recalculated after React state updates.
- Saved days and saved meals already exist in the database; the meal selector change is a UI-only refactor.
- Token refresh is already supported by the auth service; the fix is connecting the recommendations page to use it on 401/403 responses.
- Day cards in the day planner are collapsible with a summary line (day label + total calories) visible when collapsed.
