# Feature Specification: Profile & Diet Fixes

**Feature Branch**: `010-profile-diet-fixes`  
**Created**: 2026-04-05  
**Status**: Draft  
**Input**: User description: "the profile tab should not be grouped up with dashboard and the other tabs, it should be near sign out. In the profile tab, input is not saved, the buttons for goals do not click and show the option selected, nor do the dietary restrictions. That should also be taken into account when recommending food. the dietary recommendations dont add up to the recommended amount of macros, its far under in some cases this has to be fixed. I also do not see the saved days in my saved meals section of the tab"

## Clarifications

### Session 2026-04-05

- Q: Does the user profile API (for reading/writing name, age, height, weight, gender, goal, dietary restrictions) already exist, or does it need to be built? → A: API fully exists in user-service (GET/PATCH /api/users/me/profile, GET/PUT /api/users/me/goal, GET/POST/DELETE /api/users/me/dietary-restrictions). Frontend profile page already calls these APIs. Root cause of "not saving" is silent failures with no error display — fixes are: add error states to profile page, ensure user-service DB tables are migrated in Supabase.
- Q: For the diet macro accuracy fix, which approach should be used? → A: Server-side retry loop — validate day_totals after generation, retry up to 3× if any day is >10% off target (same pattern as workout score floor).
- Q: Should `activity_level` be added to the user profile (DB model + UI)? → A: Yes — add `activity_level` column to `UserProfile` model and a selector to the profile page UI; pass the saved value to `calculateMacros` and `generateDiet`.
- Q: Should saved days appear in "My Saved Meals" in addition to staying in Day Planner, or consolidated only in one place? → A: Both — add a "Saved Days" section to FoodMealsTab; Day Planner keeps its own saved days list for quick apply.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Profile Navigation Moved Near Sign Out (Priority: P2)

The Profile tab is currently grouped with Dashboard and other navigation tabs. Users expect profile and account-level controls to live near the Sign Out button, not alongside content tabs.

**Why this priority**: Navigation misplacement is a UX issue that affects every session but doesn't block core functionality.

**Independent Test**: Open the app navigation; verify the Profile link/tab is positioned adjacent to (or in the same group as) the Sign Out button, and is no longer listed alongside Dashboard and other content tabs.

**Acceptance Scenarios**:

1. **Given** a logged-in user views the navigation, **When** they look at the main tab bar, **Then** "Profile" does not appear alongside "Dashboard" and other content tabs.
2. **Given** a logged-in user looks near the Sign Out control, **When** they scan that area, **Then** a Profile link or icon is visibly accessible there.

---

### User Story 2 - Profile Inputs Save Correctly (Priority: P1)

Users fill in profile fields (name, age, height, weight, gender, activity level) and click save, but the data is not persisted. On page reload, all fields are empty or reset.

**Why this priority**: Profile data drives macro calculations and recommendations — unsaved data means the entire recommendation system operates on incorrect or missing inputs.

**Independent Test**: Fill in all profile fields, click Save, reload the page, and verify all entered values are still displayed correctly.

**Acceptance Scenarios**:

1. **Given** a user fills in their profile details and clicks Save, **When** they reload the page, **Then** all entered values are still displayed in the profile fields.
2. **Given** a user updates a previously saved value (e.g., changes weight), **When** they save and reload, **Then** the updated value is shown — not the old one.
3. **Given** a save operation fails (e.g., network error), **When** the error occurs, **Then** the user sees a clear error message and the form retains their entered values.

---

### User Story 3 - Goal Buttons Show Selected State (Priority: P1)

Goal selection buttons (e.g., "Muscle Gain", "Weight Loss", "General Health") are clickable but do not visually indicate which option is selected, and the selection is not saved.

**Why this priority**: Goal type is a required input for generating diet and workout recommendations. Without it, recommendations default to generic values that may not serve the user's actual objective.

**Independent Test**: Click a goal button, reload the page, and verify the selected goal button appears in a visually distinct "selected" state and the same goal is still selected after reload.

**Acceptance Scenarios**:

1. **Given** a user clicks a goal button, **When** the click is registered, **Then** the selected button displays a visually distinct active state (e.g., highlighted, checked, different color) and the others do not.
2. **Given** a user selects a goal and saves, **When** they reload the page, **Then** the previously selected goal is still shown as selected.
3. **Given** no goal has been selected, **When** the profile page loads, **Then** a clear prompt or empty state indicates no goal is set.

---

### User Story 4 - Dietary Restriction Buttons Save and Show Selected State (Priority: P1)

Dietary restriction toggles/buttons (e.g., "Vegetarian", "Gluten-Free", "Dairy-Free") do not retain a selected/active visual state and are not saved. As a result, the recommendation system ignores dietary restrictions entirely.

**Why this priority**: Ignoring dietary restrictions in food recommendations can cause health harm (e.g., recommending gluten-containing foods to someone with celiac disease) and fundamentally breaks the dietary recommendation feature.

**Independent Test**: Toggle a dietary restriction, reload the page, and verify the restriction is still active; generate a diet recommendation and verify restricted food categories are absent.

**Acceptance Scenarios**:

1. **Given** a user toggles a dietary restriction, **When** the selection is made, **Then** the restriction button/badge appears in a visually active/selected state.
2. **Given** saved dietary restrictions exist, **When** the profile page loads, **Then** all previously saved restrictions are displayed in their active state.
3. **Given** saved dietary restrictions exist, **When** a diet recommendation is generated, **Then** the recommendation content excludes foods that conflict with the user's saved restrictions.

---

### User Story 5 - Diet Recommendations Hit Macro Targets (Priority: P1)

Generated diet recommendations produce daily meal plans whose macro totals (calories, protein, carbs, fat) are significantly below the calculated targets. Users see a plan that tells them to eat 2000 kcal but the actual meal contents only add up to 1200 kcal.

**Why this priority**: Incorrect macro totals make the diet plan nutritionally invalid and undermine user trust in the app's core functionality.

**Independent Test**: Generate a diet recommendation; sum the actual food quantities for one day; verify the total calories, protein, carbs, and fat are within ±5% of the displayed daily targets for that day.

**Acceptance Scenarios**:

1. **Given** a diet recommendation is generated with a calculated macro target, **When** the daily meal contents are summed, **Then** each macro (calories, protein, carbs, fat) is within ±10% of the stated daily target.
2. **Given** a user views a specific day in the diet plan, **When** they expand all meals, **Then** the visible per-meal macro values add up to the day's total without unexplained shortfalls.
3. **Given** macro targets are recalculated (e.g., after a profile update), **When** a new recommendation is generated, **Then** the new meal plan reflects the updated targets.

---

### User Story 6 - Saved Days Visible in "My Saved Meals" Tab (Priority: P2)

Users who save full-day meal plans cannot find them in the "My Saved Meals" tab — only individually saved meals are shown. Saved days are invisible to the user in that section.

**Why this priority**: This makes saved day plans effectively inaccessible through the primary discovery path.

**Independent Test**: Save a day plan; navigate to the "My Saved Meals" tab; verify the saved day plan appears in a clearly labelled "Saved Days" section.

**Acceptance Scenarios**:

1. **Given** a user has saved one or more day plans, **When** they open the "My Saved Meals" tab, **Then** saved day plans are displayed in a dedicated "Saved Days" section.
2. **Given** no day plans have been saved, **When** the user opens "My Saved Meals", **Then** the "Saved Days" section either shows an empty state or is hidden gracefully.
3. **Given** a saved day plan is displayed, **When** the user views it, **Then** the plan's name, date (if set), and meal slots are visible.

---

### Edge Cases

- What if a user saves profile data with missing optional fields (e.g., no height) — the system must save the fields that are provided without requiring all fields to be filled.
- What if a diet recommendation was generated before dietary restrictions were saved — re-generating should now respect the updated restrictions.
- What if macro targets are zero or not yet computed — the diet recommendation system must wait for valid macro targets before generating or display a clear prerequisite prompt.
- What if a user has both saved days and saved meals — both sections must co-exist clearly in "My Saved Meals".

## Requirements *(mandatory)*

### Functional Requirements

**Navigation**

- **FR-001**: The Profile navigation item MUST be repositioned to appear near the Sign Out control and MUST NOT be listed alongside Dashboard and other content tabs.

**Profile — Data Persistence**

- **FR-002**: When a user saves their profile (name, age, height, weight, gender, activity_level), the data MUST be persisted and displayed correctly on next page load. The `activity_level` field MUST be added to the `UserProfile` DB model and the profile page UI (options: sedentary, lightly_active, moderately_active, very_active, extra_active).
- **FR-003**: The Save action MUST provide visual feedback confirming success or failure.

**Profile — Goal Selection**

- **FR-004**: Goal option buttons MUST display a visually distinct active/selected state when clicked.
- **FR-005**: The selected goal MUST be persisted so it remains selected on page reload.
- **FR-006**: The selected goal MUST be passed to the recommendation engine when generating diet and workout plans.

**Profile — Dietary Restrictions**

- **FR-007**: Dietary restriction options MUST display a visually distinct active/toggled state when selected.
- **FR-008**: Selected dietary restrictions MUST be persisted and remain active on page reload.
- **FR-009**: When generating a diet recommendation, all active dietary restrictions MUST be included in the generation request so the recommendation excludes conflicting foods.

**Diet Recommendations — Macro Accuracy**

- **FR-010**: Generated diet plans MUST include sufficient food quantities so that the sum of all meal macros for each day is within ±10% of the stated daily targets for calories, protein, carbs, and fat.
- **FR-011**: A server-side retry loop MUST validate each day's `day_totals` after generation and retry up to 3 times if any macro is >10% off target; the approach mirrors the workout score-floor retry in `recommendation_service.py`.

**Saved Meals Tab — Saved Days Visibility**

- **FR-012**: The "My Saved Meals" tab (`FoodMealsTab`) MUST display saved day plans in a dedicated "Saved Days" section above individually saved meals. Day Planner tab retains its own saved day plans list. `FoodMealsTab` must add `useQuery(["day-plans"], recommendations.listDayPlans)` and render the results.
- **FR-013**: Each saved day plan entry MUST show at minimum its name, date (if set), and a summary of meal slots.

### Key Entities

- **User Profile**: Personal data (name, age, height, weight, gender) used to calculate macro targets.
- **Health Goal**: A single selection indicating the user's primary fitness objective (e.g., muscle gain, weight loss, general health); drives recommendation parameters.
- **Dietary Restriction**: One or more active restrictions (e.g., vegetarian, gluten-free) that exclude certain food categories from recommendations.
- **Diet Recommendation**: An AI-generated 7-day meal plan calibrated to the user's macro targets and dietary restrictions.
- **Saved Day Plan**: A full-day meal plan saved by the user, accessible in the "My Saved Meals" tab.
- **Saved Meal**: An individually created or saved meal item, also accessible in the "My Saved Meals" tab.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After saving profile data, 100% of entered values are displayed correctly on page reload with no data loss.
- **SC-002**: Selected goals and dietary restrictions persist across page reloads 100% of the time.
- **SC-003**: Diet recommendations are generated only when the user's active dietary restrictions are included in the request; 0 recommendations are generated that violate active restrictions.
- **SC-004**: For every generated diet plan, each day's actual macro totals (summed from food items) are within ±10% of the stated daily targets.
- **SC-005**: Saved day plans are visible in the "My Saved Meals" tab within 1 second of the tab loading, alongside individually saved meals.
- **SC-006**: The Profile navigation item is no longer present in the main content tab bar; it is accessible only from the account/sign-out area.

## Assumptions

- Profile data (name, age, height, weight, gender) and goal/restriction selections are stored persistently in the user's account, not just in local/session storage.
- Dietary restriction options available in the UI correspond exactly to the restriction types the recommendation engine understands and filters on.
- The macro calculation logic already exists and produces correct targets; the issue is that the diet plan generation prompt does not enforce those targets strictly enough.
- "My Saved Meals" is an existing tab that currently shows individually saved meals; adding saved days requires adding a new section to the same tab.
- The Sign Out control is in a sidebar, header dropdown, or footer — the Profile link should be co-located with it regardless of exact placement.
- Activity level may be an additional profile field that also affects macro targets; it is treated the same as other profile fields for persistence purposes.
