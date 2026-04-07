# Feature Specification: Workout Score Accuracy, Analytics Depth & Quality Polish

**Feature Branch**: `023-workout-analytics-quality`
**Created**: 2026-04-07
**Status**: Draft
**Input**: User description: "workout score within 5% tolerance; score reflects reps/sets/duration/rest; analytics page enhanced with muscle composition analysis and imbalance detection; iterative quality debug mode with optimistic UI updates"

## Clarifications

### Session 2026-04-07

- Q: Should the iterative quality pass (US4) cover only frontend/UX fixes or also backend issues found during review? → A: Full-stack — frontend polish AND backend issues found during review (slow queries, missing validation, data correctness bugs). The pass is unbounded and continues until the app is genuinely production-quality.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Workout Volume Score Within 5% Tolerance (Priority: P1)

When a workout plan is generated, the total volume score must be within 5% of the 100% target (between 95% and 105%). Currently it can drift further, making plans feel unbalanced. Additionally, the score must update dynamically when the user edits rep counts, set counts, or time/rest values — not just when exercises are added or removed.

**Why this priority**: A workout score that is inaccurate or unresponsive to edits undermines user trust in the plan. This is the direct equivalent of the diet caloric accuracy fix (feature 015).

**Independent Test**: Generate a workout plan — confirm score is between 95–105%. Edit a rep/set count — confirm the score updates immediately without page reload.

**Acceptance Scenarios**:

1. **Given** a generated workout plan is displayed, **When** the score is rendered, **Then** the percentage shown is always between 95% and 105%.
2. **Given** a workout plan is displayed, **When** the user changes the rep count on any exercise, **Then** the volume score updates immediately.
3. **Given** a workout plan is displayed, **When** the user changes the set count on any exercise, **Then** the volume score updates immediately.
4. **Given** a workout plan is displayed, **When** the user changes time duration or rest period, **Then** the volume score updates immediately.
5. **Given** the generation algorithm cannot reach the target range with selected exercises, **When** a plan is generated, **Then** volume is redistributed across exercises until the score falls within 95–105%.

---

### User Story 2 — Enhanced Analytics Page with Body Composition Insights (Priority: P1)

The analytics page currently shows only a sparse list of metrics. Users need trend lines, muscle balance analysis (detecting left/right or upper/lower imbalances), plain-language summary cards, and delta indicators showing change since their previous scan.

**Why this priority**: The analytics page is the core value proposition for InBody scan users. Without meaningful insights it is just a table of numbers.

**Independent Test**: With two or more scans uploaded, open Analytics — confirm trend charts, a muscle balance section, summary cards, and per-metric delta indicators are all visible.

**Acceptance Scenarios**:

1. **Given** a user has at least two scans, **When** they open Analytics, **Then** trend lines are shown for skeletal muscle mass, body fat %, BMI, and segmental lean mass.
2. **Given** a user has segmental lean mass data, **When** they view Analytics, **Then** a muscle balance section highlights any imbalance greater than 10% between paired segments (e.g., left arm vs right arm).
3. **Given** a user has at least one scan, **When** they view Analytics, **Then** plain-language summary cards describe their current composition.
4. **Given** a user has multiple scans, **When** they view Analytics, **Then** each key metric shows a delta (change since previous scan) with an up/down indicator.
5. **Given** a user has only one scan, **When** they view Analytics, **Then** current data is shown without trend lines, with a prompt to upload a second scan.

---

### User Story 3 — Optimistic UI Updates for Profile Interactions (Priority: P2)

When users add/remove dietary restrictions or change their health goal, the change must appear on screen instantly — before the server responds. If the backend sync fails, the UI reverts and shows an error.

**Why this priority**: The current lag between clicking a button and seeing the result makes the app feel slow. Optimistic updates are a standard UX pattern that dramatically improves perceived performance.

**Independent Test**: On the Profile page, add a dietary restriction. Confirm it appears in the list immediately on click (before network completes). Throttle the connection — the UI should still respond instantly.

**Acceptance Scenarios**:

1. **Given** a user clicks to add a dietary restriction, **When** the button is pressed, **Then** the restriction appears in the list immediately.
2. **Given** a user clicks to remove a dietary restriction, **When** the button is pressed, **Then** the restriction disappears immediately.
3. **Given** a backend error occurs during an optimistic change, **When** the error is received, **Then** the UI reverts and shows an inline error.
4. **Given** a user changes their health goal, **When** the selection is made, **Then** the new goal is highlighted immediately.

---

### User Story 4 — Full-Stack Iterative Quality Pass (Priority: P2)

A comprehensive, ongoing review of the entire webapp — frontend and backend — to identify and fix all rough edges until the product is genuinely production-quality. This is not a single bounded task: the iteration continues until no meaningful improvements remain. Issues may include missing empty states, loading indicators, layout inconsistencies, unclear labels, slow backend endpoints, missing error handling, incorrect data, and any other quality gap discovered during review.

**Why this priority**: The webapp as a whole is not yet at end-product quality. Individual feature fixes have limited value if the overall experience feels unfinished. The iteration stops only when the app is as close to perfect as it can be.

**Independent Test**: Walk through every user-facing flow end-to-end (authenticated and unauthenticated). Confirm: every page has a helpful empty state, all async operations show loading indicators, no raw IDs or debug text visible, no slow interactions, no broken layouts at 375px, no backend errors silently swallowed.

**Acceptance Scenarios**:

1. **Given** any page has no data, **When** it loads, **Then** a clear empty-state message with a call-to-action is shown.
2. **Given** any async operation is in progress, **When** the user waits, **Then** a visible loading indicator is shown.
3. **Given** any main page, **When** viewed at 375px width, **Then** no content overflows and navigation remains accessible.
4. **Given** any backend endpoint is called, **When** it returns an error, **Then** the frontend displays a user-friendly error message (never a raw stack trace or silent failure).
5. **Given** the iterative pass is underway, **When** a backend performance issue is found (e.g., slow query, redundant calls), **Then** it is fixed as part of this iteration rather than deferred.

---

### Edge Cases

- Workout score algorithm must clamp to [95%, 105%]; if selected exercises cannot reach this, volume must be redistributed rather than displaying an out-of-range value.
- Analytics must gracefully handle scans missing segmental data (older InBody models); degrade to showing only aggregate metrics without the balance section.
- Optimistic updates must reconcile properly when two rapid changes conflict — final server state wins.
- Users with zero scans must see a meaningful landing state on the Analytics page (not a blank or broken layout).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The workout volume score MUST always display between 95% and 105%; the generation algorithm MUST enforce this constraint.
- **FR-002**: The workout volume score MUST recalculate on screen whenever reps, sets, duration, or rest values change.
- **FR-003**: The Analytics page MUST display trend lines for skeletal muscle mass, body fat %, BMI, and segmental lean mass when two or more scans exist.
- **FR-004**: The Analytics page MUST display a muscle balance section identifying imbalances >10% between paired segments when segmental data is available.
- **FR-005**: The Analytics page MUST show plain-language summary cards interpreting the user's composition.
- **FR-006**: The Analytics page MUST show delta indicators (change since last scan) for all key metrics when multiple scans exist.
- **FR-007**: Adding or removing dietary restrictions MUST update the displayed list immediately (optimistic); server sync is asynchronous.
- **FR-008**: Changing health goal MUST update the selected state immediately (optimistic).
- **FR-009**: If a backend sync fails after an optimistic update, the UI MUST revert and display an inline error.
- **FR-010**: Every main page MUST have a defined empty state with a user-facing message and call-to-action when no data is available.
- **FR-011**: All async operations MUST display a loading indicator while in progress.
- **FR-012**: The iterative quality pass MUST cover both frontend (visual, UX, layout) and backend (slow endpoints, missing validation, error handling, data correctness) issues found during review.
- **FR-013**: The iterative pass MUST continue until no meaningful improvements remain — it is not time-boxed to a single review cycle.

### Key Entities

- **WorkoutPlan**: collection of exercises each with sets, reps, duration, rest — volume score derived from these fields.
- **BodyCompositionSnapshot**: per-scan values for SMM, body fat %, BMI, and segmental lean mass (left/right arm, left/right leg, trunk).
- **MuscleBalanceReport**: computed from segmental data — imbalance flags, affected segments, percentage difference.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of generated workout plans display a score between 95% and 105%.
- **SC-002**: Score updates appear within 100ms of a rep/set/duration/rest value change.
- **SC-003**: Analytics page shows at least 4 distinct insight sections (trends, balance, summary cards, deltas) for users with 2+ scans.
- **SC-004**: Profile page interactions (restriction add/remove, goal change) reflect changes on screen in under 50ms from button press.
- **SC-005**: Zero main pages show a blank or broken layout when loaded with no data.

## Assumptions

- Segmental lean mass data (per-limb values) is available in existing scan metrics for users who have uploaded recent InBody scans; older scans without this data degrade gracefully.
- The workout plan score algorithm already exists in the backend; this feature tightens its tolerance and expands the inputs it considers.
- Optimistic update means the UI reflects the change using local state immediately; no offline persistence required — a page refresh re-fetches from server.
- The iterative quality pass (US4) covers the entire webapp — all frontend pages and all backend services — not just the six main pages.
- General body composition reference ranges will use publicly available data; no personalised medical claims are made.
- US4 is explicitly unbounded: it continues until the app is production-quality, stopping only when no meaningful improvements remain.
