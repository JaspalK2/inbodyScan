# Feature Specification: Plan Editing and Log Fixes

**Feature Branch**: `005-plan-editing-fixes`  
**Created**: 2026-04-03  
**Status**: Draft  
**Input**: User description: "for the dieting plan, i should be able to save meals as well so the breakfast meal should be saveable, if i make changes to it it should be able to save the change i made to the plan as well, for the food and meals tab, i cant see saved day plans in my saved meals tab, in the day planner tab i cant select a button to click a saved day plan to put it as what i plan to eat for the day into the food log. The workout plan also is not editable in the sense that it has a fixed option of workouts to select from if editing that actively change the score, i should be able to add more workouts / replace existing ones with a drop down or search for different types and so on."

## Clarifications

### Session 2026-04-03

- Q: Where does the exercise library data come from? → A: Third-party exercise API (e.g. ExerciseDB or Wger); queried live from the backend.
- Q: What UX pattern does the exercise picker use? → A: Inline typeahead — exercise name field becomes a text input showing a dropdown of API results as the user types; selecting replaces the exercise in place.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Save Individual Meals from Diet Plan (Priority: P1)

A user viewing their AI-generated diet plan wants to save a specific meal (e.g. the Monday breakfast) to their saved meals library so they can reuse it in future meal logging. If they have edited that meal (substituted foods or changed items), the saved version should reflect those changes.

**Why this priority**: Core blocker — users cannot preserve meals they like from their plan without this. Directly connects the generated diet plan to the meal-logging workflow.

**Independent Test**: Open the diet plan → expand any day → click "Save meal" on the breakfast entry → navigate to Food & Meals → Saved Meals tab → confirm the breakfast appears with the correct foods and macros.

**Acceptance Scenarios**:

1. **Given** a diet plan is generated and displayed, **When** the user clicks "Save meal" on any meal row (in view or edit mode), **Then** that meal is saved to the user's saved meals library with its name, food items, and macro values.
2. **Given** the user has edited a meal (swapped foods via food search), **When** they click "Save meal", **Then** the saved meal reflects the edited foods and recalculated macros — not the original AI values.
3. **Given** a meal is successfully saved, **When** the user navigates to Food & Meals → Saved Meals, **Then** the saved meal appears in the list with the correct name and macro summary.

---

### User Story 2 - Saved Day Plans Visible in Food & Meals Tab (Priority: P1)

A user who saved a full day plan (from the diet plan "Save day" button) expects to see those saved day plans visible in the Food & Meals tab's Saved Meals section. Currently saved day plans do not appear there.

**Why this priority**: Equally blocking as US1 — saving a day plan produces no visible result in the UI, making the feature feel broken.

**Independent Test**: Save a day plan from the diet plan → navigate to Food & Meals → Saved Meals tab → confirm the day plan appears in a "Day Plans" section, clearly labelled.

**Acceptance Scenarios**:

1. **Given** the user has saved one or more day plans, **When** they open the Food & Meals tab and select Saved Meals, **Then** saved day plans are displayed in a clearly labelled section separate from individual saved meals.
2. **Given** no day plans have been saved, **When** the user opens the Saved Meals tab, **Then** a day plans section shows an empty state ("No saved day plans yet").
3. **Given** a day plan is listed in Saved Meals, **When** the user views it, **Then** they can see the plan name and the list of meal slots with food items.

---

### User Story 3 - Apply Saved Day Plan to Food Log from Day Planner (Priority: P1)

A user in the Day Planner tab wants to select one of their saved day plans and apply it to a specific date, which logs all the meals from that plan into their food diary for that day. Currently there is no action to do this.

**Why this priority**: The Day Planner exists to bridge planned meals and actual food logging — without this action the planner has no functional output.

**Independent Test**: Navigate to Day Planner → select a date → click "Use saved plan" → pick a saved day plan → confirm all meals from that plan appear as food log entries for the selected date.

**Acceptance Scenarios**:

1. **Given** the user is on the Day Planner for a given date and has saved day plans, **When** they select a saved day plan and confirm, **Then** all meal entries from that plan are added to the food log for that date.
2. **Given** the selected date already has food log entries, **When** the user applies a saved day plan, **Then** the plan's entries are appended without overwriting existing entries.
3. **Given** the user has no saved day plans, **When** they open the plan picker, **Then** an empty state is shown with a prompt to save a day plan first.
4. **Given** a saved day plan is successfully applied, **When** the user views the Food Log for that date, **Then** entries reflect the plan's meals with correct food names and macro values.

---

### User Story 4 - Searchable Exercise Replacement in Workout Plan Editor (Priority: P2)

A user editing their AI-generated workout plan wants to replace an existing exercise or add a new one by searching a third-party exercise API. Changes should immediately update the workout quality score.

**Why this priority**: Without this, workout editing is cosmetic only and the score does not respond to meaningful changes.

**Independent Test**: Open workout plan → edit mode → click on an exercise name → type in the search box → results appear from the exercise API → select a replacement → confirm score updates within 1 second → save → reload → replacement persists.

**Acceptance Scenarios**:

1. **Given** the workout plan is in edit mode, **When** the user clicks on an exercise name, **Then** a search input appears that queries a third-party exercise API and displays matching results as the user types.
2. **Given** the user selects a replacement exercise from the search results, **When** the replacement is confirmed, **Then** the workout quality score recalculates immediately.
3. **Given** the user is editing a workout day, **When** they click "Add exercise", **Then** they can search the exercise API, set sets/reps, add it to that day, and the score updates.
4. **Given** the edited workout is saved, **When** the page is reloaded, **Then** all replaced and added exercises persist correctly.

---

### Edge Cases

- What if the user saves a meal with no food items (all removed)? → Prevent saving; show validation message "Meal must have at least one food item."
- What if a saved day plan is applied to a date that already has a full day of entries? → Append entries (do not overwrite); no confirmation prompt required for v1.
- What if the exercise API is unavailable or returns an error? → Show an inline error "Exercise search unavailable — try again shortly"; allow the user to keep the existing exercise name as a fallback.
- What if the exercise search returns no results? → Show "No exercises found — try different keywords."
- What if the user saves the same meal multiple times? → Each save creates a new entry; no deduplication for v1.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Users MUST be able to save any individual meal from a diet plan to their saved meals library, from both view mode and edit mode.
- **FR-002**: Saved meals MUST carry the meal name, food item list, and per-meal macro values (calories, protein, carbs, fat).
- **FR-003**: Saving a meal with zero food items MUST be blocked with a validation message.
- **FR-004**: Saved day plans MUST be visible in the Food & Meals tab's Saved Meals section in a clearly labelled "Day Plans" area.
- **FR-005**: The Day Planner tab MUST provide an action to apply a saved day plan to the currently selected date.
- **FR-006**: Applying a saved day plan MUST append its meal entries to the food log for that date without overwriting existing entries.
- **FR-007**: In workout plan edit mode, exercise name fields MUST use an inline typeahead control — clicking the field activates a text input that queries a third-party exercise API and shows a dropdown of results as the user types; selecting a result replaces the exercise in place.
- **FR-008**: Users MUST be able to add a new exercise to any workout day using the same exercise search control.
- **FR-009**: After replacing or adding an exercise, the workout quality score MUST recalculate and update within 1 second.
- **FR-010**: All workout exercise changes MUST persist when the plan is saved and reloaded.
- **FR-011**: If the third-party exercise API is unavailable, the exercise search MUST show a graceful error and allow the user to retain the existing exercise name.

### Key Entities

- **SavedMeal**: User-owned library entry with a name, list of food items (name + quantity), and aggregate macro values.
- **SavedDayPlan**: User-owned collection of meal slots (breakfast, lunch, dinner, snack), each with food items and macros; applicable to a calendar date to generate food log entries.
- **ExerciseLibrary**: Results sourced from a third-party exercise API (queried live); each result has at minimum a name and muscle group.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can save any meal from a diet plan in 2 interactions or fewer.
- **SC-002**: Saved day plans appear in the Saved Meals section within 1 second of navigating to that tab, with zero additional steps.
- **SC-003**: A user can apply a saved day plan to a date and see food log entries appear within 2 seconds of confirming.
- **SC-004**: Exercise search in the workout editor returns results within 1 second of typing 2 or more characters (when the API is available).
- **SC-005**: Workout quality score updates within 1 second of any exercise replacement or addition in edit mode.
- **SC-006**: 100% of saved workout exercise changes persist correctly after a full page reload.

## Assumptions

- The saved meals library and day plan storage already exist from feature 002; this feature surfaces and connects them to new UI entry points.
- The exercise library is sourced from a third-party API (e.g. ExerciseDB at exercisedb.io or Wger); a backend proxy endpoint will call this API to avoid exposing keys to the client and to enable caching.
- Applying a saved day plan appends entries; no merge conflict UI is required for v1.
- Saving a meal always creates a new entry — no in-place update of previously saved meals is required for v1.
- The workout score algorithm accepts arbitrary exercise names; the exercise API is for discovery and UX, not enforcement.
