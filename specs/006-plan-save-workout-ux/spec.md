# Feature Specification: Plan Save Flow and Workout UX Fixes

**Feature Branch**: `006-plan-save-workout-ux`  
**Created**: 2026-04-03  
**Status**: Draft  
**Input**: User description: "if i make a generated meal plan and save it, i should be able to see it as a saved day plan, as well as saved meals from that given day..."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Save Generated Meal Plan Day as Both Day Plan and Individual Meals (Priority: P1)

When a user clicks "Save Day" on a day in a generated diet plan, the system saves the whole day as a day plan record AND saves each meal slot (breakfast, lunch, dinner, snack) as a separate custom meal. Meals saved this way are labelled to indicate their source (e.g., "Day Planner — Breakfast") so users can tell them apart from meals they created manually.

**Why this priority**: This is the foundational save flow. Without it, users lose generated meal data and cannot reuse it elsewhere.

**Independent Test**: Generate a diet plan → click "Save Day" on Day 1 → navigate to Food & Meals → Saved Meals tab → confirm breakfast/lunch/dinner/snack appear as individual meals labelled "Day Planner — [Slot]" → navigate to Day Planner tab → confirm the day appears as a saved day plan with all entries.

**Acceptance Scenarios**:

1. **Given** a generated diet plan is displayed, **When** the user clicks "Save Day" on any day row, **Then** one day plan record is created containing all meal entries AND one custom meal record is created for each non-empty meal slot.
2. **Given** meals were auto-saved from a day planner action, **When** the user views the Saved Meals tab, **Then** those meals appear with a name prefix identifying their source (e.g., "Day Planner — Breakfast").
3. **Given** both user-named and day-planner-sourced meals exist in Saved Meals, **When** the user browses the list, **Then** user-named meals display only the name the user chose, with no prefix appended.
4. **Given** the user clicks "Save Day" on a day where all meal slots are empty, **When** the save action triggers, **Then** an error message is shown and no records are created.

---

### User Story 2 — Correct Tab Content: Day Planner Shows Day Plans, Food & Meals Shows Individual Meals (Priority: P1)

The Day Planner tab exclusively shows saved day plan records (full-day templates). The Food & Meals → Saved Meals sub-tab exclusively shows individual custom meals, regardless of whether the user created them manually or they were auto-saved from a day planner save. Users should not need to hunt across tabs to find their saved content.

**Why this priority**: The current confusion about where to find saved content is a core usability blocker.

**Independent Test**: Save a custom meal manually → save a day plan via "Save Day" → open Food & Meals → Saved Meals: confirm both the user meal and the day-planner-sourced individual meals appear → open Day Planner: confirm only the whole day plan record appears, not individual meal cards.

**Acceptance Scenarios**:

1. **Given** the user is on the Food & Meals → Saved Meals sub-tab, **When** the page loads, **Then** all individual custom meals are listed (user-created and day-planner-sourced), each showing name, macro summary, and item count.
2. **Given** the user is on the Day Planner tab, **When** saved day plans exist, **Then** only whole-day plan records are shown (name, date, total macros) with no individual meal cards in the list.
3. **Given** a day-planner-sourced individual meal is shown in the Saved Meals tab, **When** the user clicks "Add to today", **Then** all food items from that meal are logged to the food diary, identical to a user-created meal.

---

### User Story 3 — Exercise Field Labels in Workout Plans (Priority: P1)

Every exercise row in a workout plan or custom split must show clearly labelled data fields. In view mode, each value (sets, reps, weight, rest period) must have a visible label. In edit mode, each input must have a label or descriptive placeholder so the user always knows what they are entering.

**Why this priority**: Unlabelled fields make the workout plan unreadable and undermine trust in the feature.

**Independent Test**: Open any saved workout plan (AI-generated or custom split) → expand a training day → confirm every exercise shows labelled fields (e.g., "Sets: 3 · Reps: 8–12 · Weight: 60 kg · Rest: 90 s") → enter edit mode → confirm each input field has a label or placeholder identifying it.

**Acceptance Scenarios**:

1. **Given** a workout plan is in view mode, **When** a training day is expanded, **Then** each exercise row shows labels: Sets, Reps, Weight (kg), Rest (s) next to their respective values.
2. **Given** a workout plan is in edit mode, **When** the exercise input row is displayed, **Then** each input field is accompanied by a label or placeholder text identifying its purpose (Sets, Reps, Weight, Rest).
3. **Given** a field has no value (e.g., no weight entered), **When** in view mode, **Then** that field is either hidden or shows a dash — it does not show an unlabelled blank.

---

### User Story 4 — Add and Remove Exercises in Any Workout Plan Edit Mode (Priority: P1)

In edit mode for any workout plan (both AI-generated plans and user-built custom splits), users can add new exercise entries to any non-rest training day and remove any existing exercise. The live quality score updates after each change.

**Why this priority**: Generated plans are starting points; users must be able to customise them. Without add/remove, the plan is locked.

**Independent Test**: Open generated workout plan → Edit → expand Week 1 Day 1 → click "Add exercise" → fill in name (using typeahead), sets, reps → confirm it appends → click remove on an existing exercise → confirm it disappears → score updates within 1 second of each change.

**Acceptance Scenarios**:

1. **Given** a workout plan is in edit mode on a non-rest day, **When** the user clicks "Add exercise", **Then** a new empty exercise row is added to that day with the typeahead name input and fields for sets, reps, weight, and rest.
2. **Given** a workout plan is in edit mode, **When** the user clicks the remove icon on an exercise row, **Then** that exercise is immediately removed from the day's list.
3. **Given** exercises are added or removed, **When** the change occurs, **Then** the live quality score recalculates and the updated score is visible within 1 second.
4. **Given** a day is designated as a rest day, **When** in edit mode, **Then** no "Add exercise" button appears for that day.

---

### User Story 5 — Live Score for User-Built Custom Splits (Priority: P2)

The live quality score (which already works for AI-generated workout plan edits) also updates in real time when users build or edit their own custom workout splits in the Split Builder. Any change to exercises, sets, or reps triggers a score recalculation.

**Why this priority**: Users creating their own splits need the same feedback loop as AI plan editors to optimise their training.

**Independent Test**: Navigate to Workout → Split Builder → add exercises across multiple days → confirm a live score panel appears and updates each time an exercise is added, changed, or removed.

**Acceptance Scenarios**:

1. **Given** the user is building a custom split and adds at least one exercise, **When** the exercise is added, **Then** a live score panel appears showing the current quality score.
2. **Given** the user modifies a set count or reps value in the split builder, **When** the field changes, **Then** the score updates within 1 second.
3. **Given** the user removes all exercises from all days in the split builder, **When** the last exercise is removed, **Then** the score resets to 0 or hides the panel.

---

### Edge Cases

- What if "Save Day" is clicked on a day where all meal slots are empty? Show an error; create no records.
- What if the user adds an exercise with no name? Block saving that exercise; highlight the name field as required.
- What if a day-planner-sourced individual meal is deleted from the Saved Meals tab? The parent day plan record remains intact; only the individual custom meal entry is removed.
- What if the score calculation service is unavailable during exercise changes? The UI stays functional; the score shows a loading state or retains its last value.
- What if a day is toggled to rest after exercises were added? Exercises are cleared from view and not preserved on save.

## Requirements *(mandatory)*

### Functional Requirements

**Diet Plan Save Flow**:
- **FR-001**: System MUST, when saving a generated diet day, create one day plan record AND one custom meal record per non-empty meal slot in that day.
- **FR-002**: Custom meals auto-saved from a day plan save MUST use the naming format "Day Planner — [Meal Slot]" (e.g., "Day Planner — Breakfast").
- **FR-003**: User-created custom meals MUST display only the user-chosen name — no source prefix is added.
- **FR-004**: The Food & Meals → Saved Meals tab MUST list all custom meals (user-created and day-planner-sourced) in one unified list.
- **FR-005**: The Day Planner tab MUST list only whole day plan records, not individual custom meals.

**Workout UX — Labels**:
- **FR-006**: Every exercise row in view mode MUST show labelled fields: Sets, Reps, Weight (kg), Rest (s) alongside their values.
- **FR-007**: Every exercise input row in edit mode MUST include a visible label or descriptive placeholder for each field: Sets, Reps, Weight, Rest.

**Workout UX — Add/Remove**:
- **FR-008**: In edit mode for any workout plan or custom split, users MUST be able to add a new exercise row to any non-rest training day.
- **FR-009**: In edit mode for any workout plan or custom split, users MUST be able to remove any individual exercise from a day.
- **FR-010**: Rest days MUST NOT expose an "Add exercise" control.

**Live Score**:
- **FR-011**: The live quality score MUST recalculate within 1 second of any exercise change (add, remove, name, sets, reps) in both generated plans and user-built splits.
- **FR-012**: The live score panel MUST be visible whenever exercises exist in the plan being edited or viewed.

### Key Entities

- **Day Plan**: A whole-day meal template with a name, optional date, and meal slot entries. Shown in the Day Planner tab.
- **Custom Meal**: An individual named meal with food items and macros. Shown in the Food & Meals → Saved Meals tab. May be user-named or auto-named with a day-planner source prefix.
- **Exercise Entry**: A single exercise within a workout day, with fields: name, sets, reps, weight, rest period.
- **Quality Score**: A composite score (0–100) evaluating workout coverage, volume, balance, cardio, and frequency.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After clicking "Save Day" on a generated diet day, the saved day plan and all individual meals are accessible within 2 navigation steps, with no page reload required.
- **SC-002**: 100% of exercise data fields in view and edit modes carry visible, human-readable labels — zero unlabelled numeric fields remain.
- **SC-003**: Users can add a new exercise to any training day in edit mode within 3 interactions (clicks or taps).
- **SC-004**: Users can remove any existing exercise from a training day in 1 interaction.
- **SC-005**: The quality score updates within 1 second of every exercise change in both generated plans and user-built custom splits.
- **SC-006**: Users can distinguish day-planner-sourced meals from user-created meals by reading the meal name alone, without opening the meal detail.

## Assumptions

- Users are authenticated and have already generated at least one diet plan or workout plan.
- The existing custom meal and day plan storage are reused as-is; no new database tables are required.
- Auto-saved meals from "Save Day" use the "Day Planner — [Slot]" naming by default; users may rename them later through existing meal management flows.
- The quality score calculation endpoint is already implemented; this feature wires it to more entry points without rebuilding the scoring logic.
- Deleting a day-planner-sourced custom meal from the Saved Meals tab does not cascade to the parent day plan record.
- The exercise typeahead (searching the CC0 exercise dataset) is already implemented for generated plan edits; this feature extends it to the user-built split editor as well.
- Mobile-responsive layout is assumed; no separate mobile-only design needed.
