# Feature Specification: Fix 500 Error on GET Day Plans

**Feature Branch**: `017-fix-items-snapshot-orm-mutation`
**Created**: 2026-04-06
**Status**: Draft
**Input**: GET /api/recommendations/day-plans returns 500 Internal Server Error — saved day plan does not appear in the Food & Meals or Day Planner tabs.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Viewing saved day plans succeeds without error (Priority: P1)

A user saves a diet day, then navigates to the Food & Meals "Saved" tab or the Day Planner tab. The list of saved plans loads successfully and the newly saved plan is visible.

**Why this priority**: The GET endpoint crashes every time a plan with food items has been saved, making the entire saved-plans feature completely broken for all users.

**Independent Test**: Save any diet day with food items → navigate to the Saved tab or Day Planner → the plan list loads (no error) and the saved plan appears.

**Acceptance Scenarios**:

1. **Given** at least one day plan with food items has been saved, **When** the user opens the Food & Meals "Saved" tab, **Then** the saved plans list loads within 2 seconds with no error
2. **Given** at least one day plan has been saved, **When** the user opens the Day Planner tab, **Then** the saved plans list loads within 2 seconds with no error
3. **Given** a plan saved with 4 meal slots containing food items, **When** the plan list is displayed, **Then** each plan entry shows the correct meal slot names and calorie/macro values

---

### User Story 2 — Food items within each saved plan display correctly (Priority: P1)

When a saved day plan is expanded, the individual food items within each meal slot are displayed correctly, matching what was saved.

**Why this priority**: The food item list is the primary content users save. Blank or missing items makes the feature worthless.

**Independent Test**: Save Day 1 with breakfast containing food items → open the saved plan → breakfast shows the correct food items.

**Acceptance Scenarios**:

1. **Given** a plan saved with specific food items in a meal slot, **When** the user expands that saved plan, **Then** all food items are displayed with their correct names and quantities
2. **Given** a plan saved by the algorithmic engine, **When** displayed, **Then** food items render correctly — no blank or empty lists

---

### Edge Cases

- A plan saved with zero food items (empty snapshot) — the plan must still appear in the list with empty meal slots
- Plans saved before this fix — data already stored correctly in the database must continue to display correctly after the fix
- A user with multiple saved plans — all plans must load correctly in a single request without any one plan contaminating another

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The saved day plans endpoint MUST return a successful response for any user who has saved at least one plan containing food items
- **FR-002**: Food item snapshots MUST be deserialized and displayed correctly without modifying the underlying stored data record
- **FR-003**: The fix MUST NOT change the database schema, API response shape, or the storage format of food item snapshots
- **FR-004**: The fix MUST be backwards-compatible — plans saved before the fix MUST continue to display correctly

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The saved day plans endpoint returns a successful response for 100% of requests — zero 500 errors caused by this bug
- **SC-002**: Food items in each saved plan are displayed correctly in 100% of cases — zero plans showing blank or corrupted item lists
- **SC-003**: The fix requires no database migration and no change to the API response shape

## Assumptions

- The underlying database rows are stored correctly — food item snapshots are persisted as valid JSON strings; the bug is purely in the read/deserialization path
- No other code paths in this service mutate ORM objects after loading in a way that would interact with this fix
- The caloric accuracy requirement (±5%) is tracked separately under feature 015 and is out of scope for this fix
