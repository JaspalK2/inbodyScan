# Feature Specification: Plan Log and Workout Fixes

**Feature Branch**: `007-plan-log-workout-fixes`  
**Created**: 2026-04-03  
**Status**: Draft  
**Input**: User description: "saving the meals from the diet generation appears in my saved meals, but the saved day itself does not appear in the day planner on the bottom. Thus there is no way to add a whole day worth of food items into the food log. When i go into the saved meals planner, I should see a list of meals that were saved via saved days, day by day, or a section of custom made saved meals from the food planner by the user, also there are older versions of diet planners made by AI that cannot be deleted this should be changed as well. For the planned ai generated workout program i cannot delete values from preset workouts for example i cannot change the number of sets from 3 to 8. also for a generated workout to be an 85/100 is not a good look, the generated workout should be an ideal 100/100 which the user can min max with their own preferences."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Saved Day Plans Appear in Day Planner and Can Log Whole Day to Food Log (Priority: P1)

When the user saves a day from a generated diet plan, a day plan record is created. This record MUST appear in the Day Planner tab's list of saved day plans. The user must then be able to click a single "Log this day" action on a saved day plan to add all of its food items (across all meal slots) into the food log for today's date — enabling the core "apply a full day of eating to my log" workflow.

**Why this priority**: Without this, the "Save Day" action is effectively useless — users cannot retrieve the saved day plan from the Day Planner and cannot log a full day's meals in one action.

**Independent Test**: Save a day from a generated diet plan → navigate to Day Planner tab → confirm the saved day plan appears in the list → click "Log this day" → navigate to the food log for today → confirm all meal slot food items appear as log entries.

**Acceptance Scenarios**:

1. **Given** a day plan was saved from a generated diet plan, **When** the user opens the Day Planner tab, **Then** the saved day plan appears in the list of saved day plans with its name, date (if set), and total macro summary.
2. **Given** a saved day plan is listed in the Day Planner, **When** the user clicks "Log this day", **Then** all food items from every meal slot in that plan are added to the food log for today's date in a single action.
3. **Given** a saved day plan has been logged, **When** the user opens the food log for today, **Then** entries from all meal slots (breakfast, lunch, dinner, snack) appear, each with correct food name and macro values.
4. **Given** the Day Planner tab is open and no day plans have been saved, **When** the user views the saved plans section, **Then** an empty state message is shown (e.g., "No day plans saved yet — save a day from your diet plan").

---

### User Story 2 — Saved Meals Tab Shows Day-Plan Meals and Custom Meals in Organised Sections (Priority: P1)

The Saved Meals sub-tab in the Food & Meals section must show two clearly labelled sections: one for meals auto-saved from generated diet days ("Day Planner Meals"), organised by which day they came from, and one for meals the user manually created ("My Meals"). Both sections are visible in a single scrollable list.

**Why this priority**: The current flat list mixes all meals together without context. Users cannot tell which meal came from which day, making the list confusing and hard to use.

**Independent Test**: Save Day 1 and Day 2 from a generated diet plan → manually create one custom meal → open Food & Meals → Saved Meals → confirm two sections appear: "Day Planner Meals" (with Day 1 and Day 2 sub-groups) and "My Meals" (with the user-created meal).

**Acceptance Scenarios**:

1. **Given** meals from multiple saved diet plan days exist, **When** the user views the Saved Meals tab, **Then** a "Day Planner Meals" section is shown, with each diet plan day's meals grouped together under a day label (e.g., "Day 1", "Day 2").
2. **Given** user-created custom meals exist, **When** the user views the Saved Meals tab, **Then** a "My Meals" section is shown containing only user-created meals, each displaying its user-chosen name.
3. **Given** a "Day Planner Meals" group is shown, **When** the user interacts with an individual meal, **Then** they can add that single meal's items to the food log (same "add to today" action as custom meals).
4. **Given** neither section has any content, **When** the user views Saved Meals, **Then** a single empty state message is shown rather than two empty section headers.

---

### User Story 3 — Delete Old AI-Generated Diet Plans (Priority: P1)

Users must be able to delete AI-generated diet plan records that are no longer needed. A delete button must be visible on each diet plan card in the Diet tab's plan history. Deleting a plan removes it permanently.

**Why this priority**: Users are accumulating stale AI-generated plans with no way to remove them, causing clutter and confusion.

**Independent Test**: Generate 3 diet plans → confirm all 3 appear in the Diet tab → click delete on the oldest one → confirm it disappears from the list immediately → refresh page → confirm it is still gone.

**Acceptance Scenarios**:

1. **Given** AI-generated diet plans are listed in the Diet tab, **When** the user clicks the delete button on a plan, **Then** a confirmation prompt is shown (e.g., "Delete this diet plan? This cannot be undone.").
2. **Given** the user confirms deletion, **When** the deletion completes, **Then** the plan is removed from the list immediately without a page reload.
3. **Given** the user cancels the confirmation, **When** cancelled, **Then** the plan remains in the list unchanged.
4. **Given** only one diet plan exists, **When** it is deleted, **Then** the empty state for diet plans is shown.

---

### User Story 4 — Edit Preset Exercise Values in Generated Workout Plans (Priority: P1)

In edit mode for an AI-generated workout plan, users must be able to freely change any numeric field on any exercise — including sets, reps, weight, and rest — replacing the preset values with their own. The current behaviour blocks editing preset values (e.g., a user cannot change sets from 3 to 8).

**Why this priority**: Blocking value edits makes the "Edit" button misleading and frustrating. Users cannot personalise the generated plan at all.

**Independent Test**: Open a generated workout plan → click Edit → find an exercise with sets=3 → clear the field and type "8" → confirm the value updates to 8 → click Save → reload → confirm the value persists as 8.

**Acceptance Scenarios**:

1. **Given** a generated workout plan is in edit mode, **When** the user clicks on any exercise's Sets field and types a new value, **Then** the field accepts the new value and the displayed value updates immediately.
2. **Given** any numeric field (Sets, Reps, Weight, Rest) in a generated workout plan edit mode, **When** the user clears the field entirely and enters a new value, **Then** the new value is saved when the user clicks Save.
3. **Given** the user changes sets from 3 to 8 and saves, **When** the plan is reloaded, **Then** all edited values persist correctly.

---

### User Story 5 — AI-Generated Workout Plans Score 100/100 by Default (Priority: P2)

The AI prompt for generating workout plans must be updated so that the plans it produces score 100/100 on the quality scoring system. A 100/100 plan is the ideal baseline that users can then customise (reducing or changing exercises) while watching the score adjust. An 85/100 starting point is suboptimal and makes the AI output look poor.

**Why this priority**: The starting score directly reflects perceived AI quality. A perfect 100/100 gives users confidence and a clear baseline to personalise from.

**Independent Test**: Generate a new workout plan → without any edits, check the quality score → score should display 100/100. Modify one exercise → confirm score decreases appropriately.

**Acceptance Scenarios**:

1. **Given** a user generates a new AI workout plan, **When** the plan is displayed for the first time with no user edits, **Then** the quality score shows 100/100.
2. **Given** a 100/100 plan is shown, **When** the user removes an exercise or reduces a muscle group's coverage, **Then** the score decreases below 100, reflecting the change.
3. **Given** a 100/100 plan, **When** the user edits and saves changes that reduce coverage, **Then** the score after saving reflects the actual quality of the edited plan (not always 100).

---

### Edge Cases

- What if "Log this day" is clicked on a day plan with no food items (all slots empty)? Show an error and log nothing.
- What if a diet plan is deleted that has associated custom meals saved from it? The custom meals remain — only the diet plan record is deleted.
- What if the user edits a sets field and enters a non-numeric value? The field should reject non-numeric input or revert to the previous value on blur.
- What if two diet plan days have the same name? Group them separately under their respective day labels with creation date as a differentiator.
- What if the Day Planner tab has saved day plans but none came from the diet generator? All saved plans still appear regardless of source.

## Requirements *(mandatory)*

### Functional Requirements

**Day Planner Fixes**:
- **FR-001**: Saved day plans MUST appear in the Day Planner tab's saved plans list immediately after being created via "Save Day" on a diet plan — no page reload required.
- **FR-002**: Each saved day plan in the Day Planner MUST have a "Log this day" button that, when clicked, logs all food items from all meal slots to the food log for today's date in a single action.
- **FR-003**: The Day Planner MUST show an empty state when no day plans exist.

**Saved Meals Organisation**:
- **FR-004**: The Saved Meals tab MUST display two sections: "Day Planner Meals" (meals auto-saved from diet plan days) and "My Meals" (user-created custom meals).
- **FR-005**: "Day Planner Meals" MUST group meals by their source diet plan day (e.g., all "Day Planner — Breakfast/Lunch/Dinner/Snack" meals from Day 1 grouped under a "Day 1" heading).
- **FR-006**: "My Meals" MUST contain only meals created manually by the user (not prefixed with "Day Planner —").
- **FR-007**: Each meal in both sections MUST support the "add to today" food log action.
- **FR-008**: If both sections are empty, a single empty state message MUST be shown instead of two empty headings.

**Diet Plan Deletion**:
- **FR-009**: Each AI-generated diet plan card MUST display a delete button.
- **FR-010**: Clicking delete MUST show a confirmation prompt before permanently removing the plan.
- **FR-011**: Confirmed deletion MUST remove the plan from the list immediately without a page reload.

**Workout Plan Editing**:
- **FR-012**: All numeric exercise fields (Sets, Reps, Weight, Rest) in generated workout plan edit mode MUST be freely editable — users must be able to clear and re-enter any value.
- **FR-013**: Edited values MUST persist when the plan is saved and reloaded.

**AI Workout Quality**:
- **FR-014**: Newly generated AI workout plans MUST score 100/100 on the quality scoring system without any user modification.
- **FR-015**: The quality score MUST decrease appropriately when the user removes exercises or reduces coverage from a 100/100 baseline.

### Key Entities

- **Day Plan**: A whole-day meal template with a name, optional date, and entries (one per meal slot). Source of "Log this day" entries.
- **Custom Meal**: An individual named meal. Either user-created ("My Meals") or auto-saved from a diet day ("Day Planner — [Slot]").
- **Diet Recommendation**: An AI-generated multi-day diet plan record. Must be deletable.
- **Workout Recommendation**: An AI-generated workout program. Must score 100/100 on generation.
- **Food Log Entry**: A single food item recorded for a specific date in the food diary.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Saved day plans appear in the Day Planner tab within 1 navigation action after being saved — no page reload required.
- **SC-002**: "Log this day" adds all meal slot entries to the food log in a single interaction (1 button click).
- **SC-003**: The Saved Meals tab shows two labelled sections — 100% of day-planner-sourced meals appear in the "Day Planner Meals" section and 100% of user-created meals appear in the "My Meals" section.
- **SC-004**: Users can delete any AI-generated diet plan within 2 interactions (click delete → confirm).
- **SC-005**: All numeric exercise fields in generated workout edit mode accept freely typed values with 0 restrictions on clearing and re-entering.
- **SC-006**: Newly generated AI workout plans score 100/100 before any user modification.

## Assumptions

- The "Day Planner — [Slot]" naming prefix established in feature 006 is used to distinguish auto-saved meals from user-created ones. This naming convention is stable and used for the section grouping logic.
- "Log this day" uses today's date (the current calendar date at click time); users cannot specify a different date from the Day Planner's "Log this day" action.
- Deleting a diet plan only removes the plan record — associated day plan records and custom meals that were saved from it are NOT deleted.
- The AI workout scoring improvement (FR-014) is achieved by improving the LLM prompt, not by modifying the scoring algorithm.
- The workout edit field fix (FR-012) is a UI input behaviour fix — the scoring and save logic remain unchanged.
- No new backend storage is required; all changes use existing data structures and endpoints.
