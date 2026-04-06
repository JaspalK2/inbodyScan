# Feature Specification: Food & Meal Tracker Enhancements

**Feature Branch**: `002-food-meal-tracker`  
**Created**: 2026-04-02  
**Status**: Draft  
**Input**: User description: "some additions i want as a user, i want to be able to go into the food and meals tab and find either meals from restaurants or ingredients to create and save a meal. The meal or food items should have some form of a way to add to a list of stuff that I plan to eat on a given day. The user should also have the ability to see a graph possibly a pie chart showing how much of the macros the food that they eat cover. The saved foods should have some way of having a shortcut to add to the food eaten for the day. the generate plans for dieting or workouts should both be implemented and in working condition. The user should also be able to change any part of the diet or workout and this should show an effect to the macro graph."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Daily Food Log with Macro Pie Chart (Priority: P1)

A user opens the Food & Meals tab and searches for either restaurant meals or individual ingredients. They add items to a daily food log for a chosen date. A live macro pie chart updates with each addition, showing the protein/carbs/fat breakdown of everything logged compared to their daily targets — with a clear visual state when they exceed, meet, or fall short of any macro.

**Why this priority**: This is the core daily-use loop. Without it, none of the other enhancements deliver visible value. It directly addresses the user's request for a macro pie chart tied to what they actually eat.

**Independent Test**: Search for "chicken breast," add 200 g, then search for "rice," add 150 g. The pie chart must update to show both entries' combined macros against daily targets. Testable with any food search results — no saved meals or AI plans required.

**Acceptance Scenarios**:

1. **Given** the user is on the Food & Meals tab, **When** they search for a food item and tap "Add to Today," **Then** it appears in today's daily food log and the macro pie chart updates immediately.
2. **Given** the user has items in their daily food log, **When** the total protein consumed exceeds the daily target, **Then** the protein segment of the pie chart visually indicates overflow (e.g., overflow color or label).
3. **Given** the user has logged food items, **When** they remove an item from the log, **Then** the pie chart recalculates instantly without a page reload.
4. **Given** no daily macro targets exist for the user, **When** they view the pie chart, **Then** absolute gram totals are displayed with a prompt to upload a scan or set up a profile for target-relative display.

---

### User Story 2 — Restaurant Meal Search (Priority: P1)

A user can search for restaurant meals by restaurant name or dish name (e.g., "McDonald's Big Mac," "Chipotle bowl") from the same search bar used for ingredients. Restaurant meals appear alongside generic food items in results, clearly labelled with the restaurant name. Adding a restaurant meal to the daily log works identically to adding a generic ingredient.

**Why this priority**: The user explicitly requested restaurant meals as a distinct data source. This significantly expands daily usability beyond home-cooked meals.

**Independent Test**: Search for a well-known fast-food item by name. Confirm a result labelled with the restaurant name is returned with calorie and macro data and can be added to the daily log, updating the pie chart.

**Acceptance Scenarios**:

1. **Given** the user types a restaurant or dish name, **When** results load, **Then** matching restaurant meals appear alongside generic ingredients with a visible source label.
2. **Given** a restaurant meal result is shown, **When** the user adds it, **Then** its full macro data (calories, protein, carbs, fat) is added to the daily log and the pie chart updates.
3. **Given** no restaurant data matches the search query, **When** results are empty, **Then** the user sees a clear no-results message rather than an error screen.

---

### User Story 3 — Saved Food Shortcuts (Priority: P2)

Foods and custom meals that the user has previously saved appear with a one-tap shortcut to add them directly to the daily food log, bypassing the search flow. This makes repeat logging fast for users with consistent eating habits.

**Why this priority**: Builds on the existing saved meals system and dramatically reduces friction for the daily logging loop once a user has established their common meals.

**Independent Test**: Save a custom meal, return to the daily log, confirm the saved meal appears in a shortcut list, tap the shortcut, and verify the full meal's macros are added to the log and the pie chart updates.

**Acceptance Scenarios**:

1. **Given** the user has saved meals or food items, **When** they view the Food & Meals tab, **Then** saved items appear in an accessible "Saved" section with an "Add to Today" shortcut button.
2. **Given** the user taps the shortcut for a saved meal, **Then** the full meal (all items and macros) is added to today's log in a single action — no search required.
3. **Given** the user has no saved meals, **Then** the shortcuts section displays an empty state with a prompt to save items from search results.

---

### User Story 4 — Editable AI Diet Plan with Live Macro Impact (Priority: P2)

A user generates an AI diet plan. Each planned meal shows an inline macro preview and a "Log this meal" button. The user can edit meal quantities before or after logging. Editing a meal updates its inline macro preview immediately; the shared macro pie chart only updates once the user explicitly logs the meal (or updates an already-logged entry).

**Why this priority**: The user explicitly described this feedback loop: "changing any part of the diet should show an effect to the graph." Closes the gap between AI-generated plans and the user's actual macro tracking.

**Independent Test**: Generate a diet plan, change one meal's portion size — confirm the inline macro preview updates immediately. Then tap "Log this meal" — confirm the pie chart updates. Save the change and confirm it persists after navigating away and back.

**Acceptance Scenarios**:

1. **Given** the user has a generated diet plan, **When** they change the quantity of any meal component, **Then** the inline macro preview for that meal updates live — but the pie chart does NOT change yet.
2. **Given** the user taps "Log this meal" on a plan meal, **Then** the meal is added to the daily food log and the pie chart updates immediately.
3. **Given** the user edits a meal they have already logged, **When** they save the edit, **Then** they are prompted to update the log entry; confirming updates the pie chart.
4. **Given** edits cause a macro to exceed 100% of the daily target after logging, **Then** the pie chart shows the overflow state for that macro.
5. **Given** the user saves their plan edits, **Then** the edited plan persists on the next login.
6. **Given** the user wants to undo all edits, **When** they revert to the original AI plan, **Then** the original plan values restore (already-logged entries are not automatically removed).

---

### User Story 5 — Editable AI Workout Plan with Live Quality Score Impact (Priority: P2)

A user generates an AI workout plan. They can edit exercises, add or remove workout days, and adjust sets, reps, and weights. After each edit the workout quality score (0–100 across 5 dimensions) recalculates and updates in the UI, showing how the change affects their training effectiveness and muscle-group balance.

**Why this priority**: The user asked for workout edits to "show an effect" analogous to the macro chart for dieting. Uses the existing quality scoring algorithm.

**Independent Test**: Generate a workout plan, remove all cardio exercises, and confirm the cardio sub-score of the quality score decreases without a page reload. Save and confirm persistence.

**Acceptance Scenarios**:

1. **Given** the user has a generated workout plan, **When** they add or remove an exercise or change sets/reps/weights, **Then** the quality score and its sub-scores update immediately.
2. **Given** the user's edits remove all exercises from a muscle group, **Then** the quality score's feedback list indicates the missing group.
3. **Given** the user saves their edits, **Then** the edited workout plan and its current quality score persist on the next session.
4. **Given** the user wants to undo all workout edits, **When** they revert to the original AI plan, **Then** the original plan and its quality score restore.

---

### Edge Cases

- What if a food item has missing macro data (only calories known)? — Display known values; missing macros show as 0 g and do not break the pie chart. A label indicates incomplete data.
- What if the user has no daily macro targets? — The pie chart shows absolute gram totals with a prompt to complete profile setup.
- What if the user adds the same food item twice on the same day? — Both entries are logged as separate line items; macros are summed correctly.
- What if AI plan generation fails or times out? — A descriptive error message and a retry button are shown; no partial plan is saved.
- What if a restaurant meal has no breakdown (only total calories)? — The item is added with calories shown and macros listed as unavailable; it does not contribute to macro slices but is counted in total calories.
- What if the user removes all exercises from a workout plan? — The quality score drops to 0 and a warning is shown; the empty plan can still be saved.
- What if the user logs food for a past date and their macro targets have changed since then? — The pie chart uses the targets currently set on their profile (not historical targets).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow users to search for restaurant meals and individual food ingredients from a single search bar, with each result labelled by source type.
- **FR-002**: The system MUST allow users to add any food search result or restaurant meal to a daily food log for today or a selected past/future date via a single action.
- **FR-003**: The system MUST display a single shared macro pie chart (protein, carbohydrates, fat) per day that aggregates macros from both manually logged food items AND any AI diet plan edits, updating immediately on any change to either source.
- **FR-004**: The macro pie chart MUST visually distinguish three states per macro: under target, at/near target, and over target (overflow).
- **FR-005**: The system MUST display saved meals and food items with a one-tap shortcut to add them to today's daily log without requiring a new search.
- **FR-006**: The AI diet plan generator MUST produce a complete, parseable plan when the user has an active scan and health goal; failures MUST surface a user-readable error message and a retry button.
- **FR-007**: The AI workout plan generator MUST produce a complete, parseable weekly plan when the user has an active scan and health goal; failures MUST surface a user-readable error message and a retry button.
- **FR-008**: Each meal in a generated diet plan MUST have a "Log this meal" action. Only after the user explicitly logs a plan meal does it contribute to the shared macro pie chart. Editing a plan meal's quantity before logging updates the macro preview inline but does not affect the chart until logged.
- **FR-008b**: Once a plan meal is logged, any further edit to that meal in the plan MUST offer to update the corresponding log entry (with user confirmation) and immediately refresh the pie chart if updated.
- **FR-009**: Any edit to a generated workout plan (exercises, sets, reps, or weights) MUST immediately recalculate and update the workout quality score without a page reload.
- **FR-010**: Edited diet plans and edited workout plans MUST be persistable — saved edits survive logout and re-login.
- **FR-011**: The system MUST provide a "Revert to Original" action on edited plans that restores the AI-generated version and updates the chart/score accordingly.
- **FR-012**: The daily food log MUST support multiple separate entries of the same food item on the same date.
- **FR-013**: The daily food log MUST support date navigation — users can view and edit logs for dates other than today via a date picker.

### Key Entities

- **Daily Food Log Entry**: A single logged food item for a specific date — stores food name, source, quantity consumed (g or serving), and computed macros at time of logging (calories, protein g, carbs g, fat g). Retained indefinitely; no expiry or pruning.
- **Food Search Result**: A searchable food entry from either a nutrition database (ingredient) or a restaurant dataset — includes name, source label, calories, protein, carbs, fat per standard serving, and serving size.
- **Macro Pie Chart State**: A derived view for a selected date — computes totals per macro aggregated from both daily food log entries AND any AI diet plan meals for that date; compared against the user's daily targets with an overflow flag per macro.
- **Edited Diet Plan**: A user-modified version of a generated diet plan stored alongside the original AI output — tracks per-meal overrides (quantity or food substitutions).
- **Edited Workout Plan**: A user-modified version of a generated workout plan — tracks per-exercise overrides (sets, reps, weight) and additions/removals.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After adding a food item to the daily log, the macro pie chart updates in under 1 second.
- **SC-002**: Restaurant meal search returns at least one relevant result for the 20 most popular fast-food chains when searched by name.
- **SC-003**: A new user can complete the "search → add to day → view updated chart" flow in under 30 seconds without instruction.
- **SC-004**: The macro pie chart's displayed gram totals exactly match the sum of all individual log entry macros (within standard floating-point rounding tolerance).
- **SC-005**: Editing a meal in a generated diet plan updates the macro pie chart in under 1 second.
- **SC-006**: Editing an exercise in a generated workout plan updates the quality score in under 1 second.
- **SC-007**: The saved food shortcut adds a meal to the daily log in a single tap — zero additional confirmation steps required.
- **SC-008**: AI diet plan generation succeeds on 95%+ of attempts when the LLM service is available; every failure surfaces a user-readable error.
- **SC-009**: AI workout plan generation succeeds on 95%+ of attempts when the LLM service is available; every failure surfaces a user-readable error.
- **SC-010**: Edited plans (diet and workout) persist across sessions — a user who saves edits sees them intact after logging out and back in.

---

## Assumptions

- Restaurant meal nutritional data will be sourced from an openly licensed dataset (e.g., Open Food Facts, Nutritionix free tier, or similar); the exact source will be determined at planning based on licensing and coverage.
- Daily macro targets are derived from the existing macro calculator already in the system; users without targets see absolute gram totals.
- The macro pie chart lives on the Food & Meals tab alongside the daily food log — not on a separate analytics page.
- "Editable AI plan" means inline editing within the existing recommendations page, not a separate editing tool.
- The workout quality scoring algorithm already implemented (0–100, 5 dimensions) is reused without modification to reflect workout edits.
- All data is strictly user-scoped; users cannot view or modify other users' food logs or plans.
- Restaurant meal nutritional values are read-only — users can log them and adjust quantity consumed, but cannot override the per-100g nutritional values of a restaurant item.
- The feature targets the existing web application; native mobile app support is out of scope for this iteration.

## Clarifications

### Session 2026-04-02

- Q: Should restaurant meal search be a separate mode or integrated into the existing food search bar? → A: Integrated into the same search bar; results are labelled by source type.
- Q: Should the macro pie chart show only today's log or support date selection? → A: Defaults to today; a date picker allows navigating to other dates.
- Q: When the user edits the AI diet plan, does that update the same macro pie chart as the daily food log, or a separate chart? → A: One shared pie chart — both manually logged food AND AI diet plan edits feed the same chart.
- Q: When a user has an AI diet plan, do its meals automatically count toward the shared macro total, or only when explicitly logged? → A: Only when explicitly logged — each plan meal has a "Log this meal" button; the pie chart updates only after that action.
- Q: How long should daily food log entries be retained? → A: Full history kept indefinitely — all past log entries are always accessible.
