# Feature Specification: Plans UX Fixes and Workout Insights

**Feature Branch**: `011-plans-fixes-workout-insight`  
**Created**: 2026-04-05  
**Status**: Draft  
**Input**: User description: "the personal information section now works as well as the other segments in profile, in plans, there should not be an option to select the active level as that was decided in the profile, the value should be set to what the profile value is. with the diet plan, the values again dont make any sense. day 1 mentions that it is 2950 kcal in total, but looking at the total cal per meal adding it up doesnt even reach 2000, this is straight up misinformation. the log button in the diet plan works, but the my saved meals segment in food and meals does not show the day plans that are saved, nor does it appear in the day planner, as for workout ai generated plans, there should be a way to delete older plans. there should be a brief explanation for the plan showing why certain exercises were chosen based off the users muscle composition and what needs work and whats already good."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Diet Plan Calorie Accuracy (Priority: P1)

A user views their AI-generated diet plan and expects the total daily calories shown to match the actual sum of calories across all meals in that day. Currently the displayed day total (e.g. 2950 kcal) does not match the sum of individual meal totals (which add up to under 2000 kcal), displaying incorrect nutritional information.

**Why this priority**: This is the most critical fix — showing inaccurate calorie totals is misleading and undermines user trust in the entire diet plan. Users making health decisions based on this data are being actively misinformed.

**Independent Test**: Open a generated diet plan, sum all meal calories manually for any day, and verify the displayed day total matches within ±5 kcal.

**Acceptance Scenarios**:

1. **Given** a generated diet plan exists, **When** the user views Day 1, **Then** the displayed daily total calories equals the arithmetic sum of all meal calories for that day.
2. **Given** a diet plan with 3 meals per day, **When** the user views any day's summary, **Then** the protein, carbs, fat, and calorie totals all match the sum of their respective meal values.
3. **Given** the diet plan macro targets are set (e.g. 2500 kcal), **When** the plan is generated, **Then** the per-meal calorie values must actually sum to the stated daily target (within ±10%).

---

### User Story 2 - Activity Level Auto-Populated from Profile (Priority: P2)

When a user navigates to the Plans page to generate a diet or workout recommendation, the activity level field should not be shown as an editable selector. Instead, it should be automatically read from the user's profile and used silently in plan generation. The user already set their activity level on the Profile page and should not be asked to set it again.

**Why this priority**: Duplicate data entry creates inconsistency — a user who sets "Very Active" in their profile and accidentally picks "Sedentary" in the plans form will get a miscalculated plan. Removing the redundant field eliminates this risk.

**Independent Test**: Navigate to Plans page, verify no activity level selector is visible, generate a plan, and confirm the backend used the profile's stored activity level.

**Acceptance Scenarios**:

1. **Given** a user with activity level "moderately_active" set in their profile, **When** they open the Plans page, **Then** no activity level selector is displayed.
2. **Given** a user with activity level set in their profile, **When** they generate a diet plan, **Then** the system uses the profile activity level value for macro calculations.
3. **Given** a user with no activity level set in their profile, **When** they visit the Plans page, **Then** the system defaults to "moderately_active" for plan generation without prompting the user.

---

### User Story 3 - Saved Day Plans Visible in My Saved Meals and Day Planner (Priority: P2)

When a user logs a diet plan day (via the "Log" button), the saved day plan should appear in both the "My Saved Meals" sub-tab and in the Day Planner view. Currently these sections remain empty even after logging a day plan.

**Why this priority**: The Log button works but saved data is not surfaced anywhere, making the feature feel broken. Users lose access to plans they have already saved.

**Independent Test**: Log a diet plan day, navigate to "My Saved Meals" tab, verify the saved plan appears. Then open the Day Planner and verify it also appears there.

**Acceptance Scenarios**:

1. **Given** a user has logged a diet plan day, **When** they open the "My Saved Meals" sub-tab, **Then** the saved day plan is listed with its name and date.
2. **Given** a user has multiple saved day plans, **When** they open the Day Planner, **Then** all their saved day plans are available for selection or review.
3. **Given** no day plans have been saved, **When** the user views "My Saved Meals", **Then** an appropriate empty state message is shown.

---

### User Story 4 - Delete Older Workout Plans (Priority: P3)

Users with multiple AI-generated workout plans should be able to delete plans they no longer want. Currently old plans accumulate with no way to remove them.

**Why this priority**: Usability — users who have generated many plans need to keep their list manageable. Lower priority than data accuracy issues.

**Independent Test**: Generate two workout plans, delete the older one, verify it no longer appears in the plan list.

**Acceptance Scenarios**:

1. **Given** a user has multiple workout plans, **When** they click the delete action on a plan, **Then** a confirmation prompt appears before deletion.
2. **Given** the user confirms deletion, **When** the plan is deleted, **Then** it is removed from the plan list immediately.
3. **Given** a user has only one workout plan, **When** they delete it, **Then** the plans section shows an appropriate empty state prompting them to generate a new plan.

---

### User Story 5 - Workout Plan Explanation Based on Body Composition (Priority: P3)

Each AI-generated workout plan should include a brief explanation (2–4 sentences) of why the specific exercises were chosen, referencing the user's muscle composition data from their InBody scan. The explanation should highlight which muscle groups need improvement and which are already performing well.

**Why this priority**: Adds meaningful context — users understand the reasoning behind their plan, which increases trust and adherence.

**Independent Test**: Generate a workout plan, view it, verify an explanation section appears that references at least one body composition metric from the scan.

**Acceptance Scenarios**:

1. **Given** a user generates a workout plan from a scan with body composition data, **When** they view the plan, **Then** a "Why this plan?" section appears with 2–4 sentences referencing their muscle composition.
2. **Given** the explanation is shown, **When** the user reads it, **Then** it identifies at least one muscle group that needs improvement and at least one that is already strong.
3. **Given** scan data has limited composition detail, **When** the plan is generated, **Then** the explanation still appears with general reasoning based on available data and goal type.

---

### Edge Cases

- What happens if the user's profile has no activity level set when they try to generate a plan? (Default to "moderately_active" silently)
- What if a diet plan's meal data is missing calorie values for some meals? (Treat missing values as 0; day total must still be the accurate sum)
- What if the user deletes a workout plan while viewing it? (Return to the plans list immediately)
- What if the AI fails to include a body composition explanation in the workout plan response? (Show a generic explanation based on goal type alone)
- What if a user has no saved day plans? ("My Saved Meals" and Day Planner show an empty state with a prompt to log a plan)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Plans page MUST NOT display an activity level selector; the value MUST be automatically sourced from the user's saved profile.
- **FR-002**: If no activity level is stored in the user's profile, the system MUST default to "moderately_active" for plan generation without prompting the user.
- **FR-003**: The displayed daily calorie total MUST be computed by summing the individual meal calorie values; AI-returned day total values MUST be ignored.
- **FR-004**: The displayed daily protein, carbs, and fat totals MUST be computed by summing the respective per-meal values; AI-returned day total values MUST be ignored.
- **FR-005**: Logged day plans MUST appear in the "My Saved Meals" sub-tab with name and date.
- **FR-006**: Logged day plans MUST appear in the Day Planner view for review or reuse.
- **FR-007**: Users MUST be able to delete any AI-generated workout plan from the plans list.
- **FR-008**: Deleting a workout plan MUST require a confirmation step before permanent removal.
- **FR-009**: Each AI-generated workout plan MUST include a "Why this plan?" explanation of 2–4 sentences, displayed at the top of the plan before the exercise list.
- **FR-010**: The workout explanation MUST identify muscle groups that need improvement and those that are already strong, based on the scan data used for generation.

### Key Entities

- **Diet Plan Day**: A single day within a diet plan, containing multiple meals; the `day_totals` field must equal the arithmetic sum of all meals' nutritional values.
- **Saved Day Plan**: A logged diet plan day stored for future reference; must appear in both "My Saved Meals" and Day Planner views.
- **Workout Plan**: An AI-generated weekly workout split; gains a `plan_explanation` field with body-composition-based reasoning (2–4 sentences).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of diet plan day totals match the arithmetic sum of their meal-level values (zero tolerance for mismatch).
- **SC-002**: The activity level selector is absent from the Plans page for all users.
- **SC-003**: Saved day plans appear in "My Saved Meals" and Day Planner within 1 page refresh of being logged.
- **SC-004**: Users can delete any workout plan in 2 or fewer interactions (click delete, confirm).
- **SC-005**: 100% of newly generated workout plans include a non-empty "Why this plan?" explanation section.

## Clarifications

### Session 2026-04-05

- Q: Should day totals be computed client-side from meal values (ignoring AI-returned totals), or fixed in the AI prompt? → A: Compute day totals by summing meal values on the display side; ignore AI-provided totals.
- Q: Where should the "Why this plan?" explanation be displayed in the workout plan view? → A: Always visible at the top of the plan, before the exercise list.

## Assumptions

- The user's profile activity level is stored and accessible at plan-generation time (established in feature 010).
- The diet calorie fix must be applied at the display layer: day totals are always computed by summing the individual meal values; AI-returned `day_totals` values are ignored entirely.
- "My Saved Meals" and "Day Planner" already have UI scaffolding from prior features; only the data-fetching or rendering logic needs correction.
- Workout plan deletion is a hard delete with no recovery requirement.
- The workout explanation is generated by the AI at plan-creation time; it is not regenerated on demand.
- Diet plan deletion is out of scope for this feature — only workout plan deletion is requested.
- The Plans page already fetches the user's profile; the activity level value from that fetch will be passed directly to plan generation.
