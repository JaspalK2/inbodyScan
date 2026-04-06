# Feature Specification: Workout and Diet Planner UX Improvements

**Feature Branch**: `008-workout-diet-planner-ux`  
**Created**: 2026-04-03  
**Status**: Draft  
**Input**: User description: "for the workout recommendations, it should be just one week that is recommended that is repeated throughout the users journey. the title for each day should be editable, each day should be removable, there should be a way to save a workout day after editing either the recommended workout or if you are making a workout from scratch to paste as a whole day into either the workout recommended planner or the my workout split section. it should be interchangeable. for the day planner, selecting a meal is hard to tell because all you see is the title but if the title just says day planner breakfast the user does not know what it is consisting of, instead of a drop down there should be a better UI showing more detailed samples of the meals. similar to the workout segment, saving a diet day planner from the generated planner should be editable for its title, so should each individual meal."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Workout Plan: Single Repeating Week with Editable Days (Priority: P1)

The AI-generated workout plan currently shows 4 weeks of content. This must be changed to a single repeating weekly template — one set of workout days that the user follows every week indefinitely. Each day in the week must have an editable title (e.g., "Push Day", "Leg Day", "Cardio") and must be individually removable from the plan. The plan should clearly communicate that it repeats each week.

**Why this priority**: This is the core structural change to the workout plan. Without it, the current 4-week design remains and no other workout-related improvements build on a sensible foundation.

**Independent Test**: Generate a new workout plan → confirm only one week of days is shown (not 4) → confirm a "repeats weekly" label is visible → edit a day title → confirm it saves → remove a day → confirm it disappears.

**Acceptance Scenarios**:

1. **Given** a newly generated AI workout plan, **When** it is displayed, **Then** only one week of days is shown (not 4 weeks) with a label indicating it repeats weekly.
2. **Given** a workout plan day, **When** the user clicks the day title, **Then** it becomes editable inline and the change persists on save.
3. **Given** a workout plan is displayed, **When** the user removes a day with confirmation, **Then** the day is permanently removed from the plan.
4. **Given** all days are removed, **When** the plan is viewed, **Then** an empty state and "Add a day" prompt appears.

---

### User Story 2 — Workout Plan: Save a Day and Reuse Across Plans (Priority: P1)

Users must be able to save any individual workout day — from the AI plan or built from scratch in the custom split builder — as a reusable workout day template. Saved workout days can then be inserted into the AI-generated workout plan or added to the "My Workout Splits" builder. The flow is fully interchangeable.

**Why this priority**: This enables the core personalisation workflow — mixing AI-suggested and custom days into one programme.

**Independent Test**: Edit Day 1 of a generated plan → save as a day template → go to My Workout Splits → confirm the saved day appears and can be added → return to generated plan → use "Add Day" to insert the saved day → confirm it appears in the plan.

**Acceptance Scenarios**:

1. **Given** a workout day is being viewed or edited, **When** the user clicks "Save Day", **Then** the day (title + exercises) is saved as a reusable template.
2. **Given** a saved workout day exists, **When** the user edits the AI-generated plan, **Then** they can insert that day into any position in the plan.
3. **Given** a saved workout day exists, **When** the user is in the My Workout Splits builder, **Then** they can add it as a split day.
4. **Given** a workout day is created from scratch in the split builder, **When** saved as a day template, **Then** it appears in both the split builder and the plan's "Add Day" picker.
5. **Given** a saved day is inserted into a plan, **When** the plan is saved and reloaded, **Then** the inserted day persists.

---

### User Story 3 — Day Planner: Rich Meal Cards Instead of Dropdown (Priority: P1)

In the Day Planner tab, the meal slot picker currently shows a dropdown of meal names. This gives no information about contents. It must be replaced with a card-based picker: each saved meal appears as a card showing the meal name, a short food item list, and macro totals. Users select a meal by clicking its card.

**Why this priority**: The current dropdown is unusable — users cannot make informed meal choices without seeing what each meal contains.

**Independent Test**: Save a day from the diet generator → open Day Planner → click a meal slot → confirm cards appear showing meal name + food items + macros → click a card → confirm it is assigned to the slot.

**Acceptance Scenarios**:

1. **Given** saved meals exist, **When** the user opens a meal slot picker, **Then** meals are shown as cards (not a dropdown) each displaying: name, food item list (up to 4, "+N more" if exceeded), calories, protein, carbs, fat.
2. **Given** meal cards are shown, **When** the user clicks a card, **Then** the meal is assigned to the slot and the picker closes.
3. **Given** no saved meals exist, **When** the user opens the slot picker, **Then** an empty state with a link to Food & Meals is shown.
4. **Given** a meal is already assigned to a slot, **When** the picker is opened again, **Then** the currently assigned meal is visually highlighted.

---

### User Story 4 — Diet Day Plan: Editable Plan Title and Meal Names (Priority: P2)

When a day is saved from the AI-generated diet plan, the resulting day plan record gets an auto-generated title ("Day N meal plan"). Users must be able to rename this title and rename each individual meal slot name within the day plan, directly from the Day Planner tab.

**Why this priority**: P2 — personalised naming improves organisation but the primary save-and-log workflow works without it.

**Independent Test**: Save Day 2 from a diet plan → open Day Planner → edit the plan title to "High Protein Day" → save → reload → confirm the title persists → edit the "Breakfast" meal name to "Morning Shake" → reload → confirm it persists.

**Acceptance Scenarios**:

1. **Given** a saved day plan in the Day Planner, **When** the user clicks the plan title, **Then** it becomes editable inline and saves on confirm.
2. **Given** a saved day plan is expanded, **When** the user clicks a meal slot name, **Then** it becomes editable inline and saves on confirm.
3. **Given** titles have been edited, **When** the page reloads, **Then** all custom names persist.
4. **Given** a meal slot name has been edited, **When** viewed in the Saved Meals section, **Then** the custom name is reflected.

---

### Edge Cases

- What if all days are removed from the workout plan? Show an empty state with an "Add a day" prompt.
- What if a saved workout day name conflicts with an existing day in the target plan? Allow duplicates — do not block insertion.
- What if a meal card has more than 4 food items? Show 4 with a "+N more" indicator.
- What if a day plan title is cleared? Revert to the previous title on save.
- What if a workout day template is deleted after being inserted into a plan? The inserted copy remains — it is a copy, not a reference.
- What if the user opens the Day Planner meal picker with a meal already assigned? The assigned meal card is highlighted and re-selectable.

## Requirements *(mandatory)*

### Functional Requirements

**Workout Plan — Single Week**:
- **FR-001**: AI-generated workout plans MUST display as a single repeating weekly template (not 4 weeks of distinct content).
- **FR-002**: The workout plan view MUST include a label indicating the week repeats (e.g., "Repeating weekly programme").
- **FR-003**: Each day in the workout plan MUST have an inline-editable title that persists on save.
- **FR-004**: Each day MUST be individually removable with a confirmation prompt.

**Workout Plan — Day Save and Reuse**:
- **FR-005**: Each workout day (in the generated plan or split builder) MUST have a "Save Day" action that stores it as a reusable workout day template.
- **FR-006**: Saved workout day templates MUST be insertable into any position in the AI-generated workout plan.
- **FR-007**: Saved workout day templates MUST be addable to the My Workout Splits builder as a split day.
- **FR-008**: Workout days created from scratch in the split builder MUST also be saveable as day templates.
- **FR-009**: A saved day inserted into a plan is a copy — changes to the template after insertion do not affect the plan.

**Day Planner — Rich Meal Picker**:
- **FR-010**: The meal slot picker in the Day Planner MUST replace the dropdown with a scrollable card-based list.
- **FR-011**: Each card MUST show: meal name, up to 4 food items (with "+N more" if more exist), and macro totals (kcal, protein, carbs, fat).
- **FR-012**: Selecting a meal card MUST assign it to the slot and close the picker.
- **FR-013**: When no meals exist, the picker MUST show an empty state with a link to Food & Meals.
- **FR-014**: The currently assigned meal (if any) MUST be visually distinguished in the picker.

**Diet Day Plan — Editable Titles**:
- **FR-015**: Saved day plan titles in the Day Planner MUST be inline-editable and persist on save.
- **FR-016**: Individual meal slot names within a saved day plan MUST be inline-editable and persist on save.

### Key Entities

- **Workout Day Template**: A new reusable entity storing a workout day title and exercise list. Can be created from the AI plan or the split builder. Insertable into either location as a copy.
- **Weekly Workout Plan**: The existing workout recommendation displayed as a single week (week 1 of the stored plan). Each day has an editable title.
- **Day Plan**: Existing entity. Extended: editable plan title, editable per-meal slot names.
- **Custom Meal**: Existing entity. Now displayed as rich cards in the Day Planner picker.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The AI-generated workout plan view shows exactly 1 week of days — 100% of plans display single-week layout on first load.
- **SC-002**: A user can save a workout day and insert it into the generated plan or the split builder within 3 interactions.
- **SC-003**: Each meal card in the Day Planner picker shows meal name, food items, and macros — users can identify meal contents without navigating away from the Day Planner.
- **SC-004**: A saved day plan title or meal name can be edited and persisted in 2 interactions (click → type → confirm).
- **SC-005**: Saved workout day templates appear in both the generated plan "Add Day" picker and the split builder day list within 1 navigation action of saving.

## Assumptions

- The AI workout prompt generates daily exercises; the display change from 4-week to 1-week view uses only week 1 data from the existing structured plan (no prompt change needed).
- A new backend endpoint is required to store and retrieve Workout Day Templates.
- The Day Planner meal picker replacement is purely a UI change — the underlying CustomMeal records are unchanged.
- Editing a day plan title or meal name patches the existing DayPlan record; no new database tables are required for this.
- The single-week display applies to both newly generated plans and existing stored plans (week 1 data is used for existing multi-week plans).
- "Save Day" for a workout day creates a persistent template. No authentication scope change is needed — templates are user-scoped like all other records.
