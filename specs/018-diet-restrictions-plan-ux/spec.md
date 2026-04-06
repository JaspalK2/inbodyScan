# Feature Specification: Fix Dietary Restriction Enforcement & Redesign Diet Plan Saved Meals UX

**Feature Branch**: `018-diet-restrictions-plan-ux`  
**Created**: 2026-04-06  
**Status**: Draft  
**Input**: User description: "saving a day shows up in the saved meals category, but does not show each individual meal and what the macros for each one is. Upon generation all days are saved automatically. My Saved Meals should show generated AI diet plans as expandable date-stamped blocks with all 7 days and per-meal macros. Dietary restrictions from user profile are not being followed during plan generation - vegetarian user received shrimp and salmon meals. This is a critical safety issue."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dietary Restrictions Enforced During Plan Generation (Priority: P0)

When a user has dietary restrictions set in their profile (e.g. vegetarian, vegan, gluten-free), every generated diet plan MUST contain zero meals or food items that violate those restrictions. A vegetarian user must never receive fish, seafood, or meat in any generated plan. This is a safety-critical requirement: serving an allergen or prohibited food to a user who has declared a restriction could cause serious harm.

**Why this priority**: Safety-critical. Serving contraindicated foods (e.g. shrimp to a vegetarian user) is a product defect of the highest severity. Must be resolved before any other work ships.

**Independent Test**: Set profile restrictions to "vegetarian", generate a new diet plan. Inspect every meal in all 7 days. Zero non-vegetarian items (meat, fish, seafood, poultry) must appear.

**Acceptance Scenarios**:

1. **Given** a user has "vegetarian" set in their profile dietary restrictions, **When** they generate a diet plan, **Then** every food item across all 7 days and all meals must be vegetarian (no meat, fish, seafood, or poultry).
2. **Given** a user has "vegan" set in their profile dietary restrictions, **When** they generate a diet plan, **Then** every food item across all 7 days and all meals must be vegan (no animal products including dairy and eggs).
3. **Given** a user has "gluten_free" set in their profile dietary restrictions, **When** they generate a diet plan, **Then** no gluten-containing items appear in any generated meal.
4. **Given** a user has no dietary restrictions set, **When** they generate a diet plan, **Then** the plan is generated normally with no restriction filtering.
5. **Given** a user's profile restrictions change after a plan was generated, **When** they generate a new plan, **Then** the new plan honours the updated restrictions; previously generated plans are unchanged.

---

### User Story 2 - Auto-Save Generated Plans & Redesigned Saved Plans Display (Priority: P1)

When a user generates a diet plan, all 7 days are automatically saved and appear in the "My Saved Meals" section without any manual "Save Day" action required. The saved plans section is reorganised: generated AI diet plans appear as date-stamped collapsible blocks (one block per plan generation). Expanding a block reveals all 7 days; expanding a day reveals its individual meals with per-meal macro totals. Users can find specific foods via the food database search if they want to make substitutions.

**Why this priority**: P1 — removes friction (no per-day save needed) and makes the saved plans section actually useful by exposing the full structured data the backend already returns.

**Independent Test**: Generate a plan. Navigate to the saved plans section. A new block labelled with today's date appears. Expand it → 7 day rows visible. Expand a day row → meals and macro totals visible.

**Acceptance Scenarios**:

1. **Given** a user generates a diet plan, **When** the plan generation completes, **Then** all 7 days are automatically persisted and appear in the saved plans section labelled with the generation date.
2. **Given** the saved plans section is visible, **When** the user views it, **Then** each generated plan appears as a collapsed block showing the generation date and goal type.
3. **Given** a saved plan block is collapsed, **When** the user clicks/taps it, **Then** it expands to show all 7 day rows with day-level macro totals.
4. **Given** a day row is visible within an expanded plan, **When** the user expands the day, **Then** each meal slot (breakfast, lunch, dinner, snack) is listed with its food items and macro totals (calories, protein, carbs, fat).
5. **Given** multiple plans have been generated, **When** the user views the saved plans section, **Then** plans are ordered by generation date (newest first).
6. **Given** a saved plan block exists, **When** the user deletes it, **Then** it is removed from the saved plans section.
7. **Given** the user wants to customise a meal, **When** they use the food database search, **Then** they can find and add foods to a custom meal as an alternative.

---

### Edge Cases

- What happens when a dietary restriction is set but the food database has very few compliant items? → Plan generation must still attempt; no restriction violations are acceptable regardless of food pool size.
- What happens when the user has multiple restrictions simultaneously (e.g. vegetarian + gluten_free)? → All restrictions must be satisfied simultaneously.
- What happens if the user has no previous plans? → The saved plans section shows an empty state message.
- What happens if plan generation fails? → The UI shows an error; no partial data appears in saved plans.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The plan generation flow MUST read the authenticated user's dietary restrictions from their profile and pass them to the diet engine before generating any food items.
- **FR-002**: The diet engine MUST filter out all food items whose restriction flags are incompatible with the user's active restrictions (the existing `_filter_foods` logic must be invoked with the user's actual profile restrictions, not an empty list).
- **FR-003**: A generated diet plan MUST contain zero food items that violate any of the user's declared dietary restrictions; this constraint is non-negotiable and supersedes caloric targets if the available food pool is small.
- **FR-004**: Upon successful plan generation, all 7 days MUST be automatically saved to persistent storage without requiring any manual save action from the user.
- **FR-005**: The saved plans section MUST display generated AI diet plans as date-stamped collapsible blocks, one block per plan generation event.
- **FR-006**: Each plan block MUST be expandable to reveal all 7 day rows; each day row MUST be further expandable to reveal individual meals with per-meal macro totals (calories, protein_g, carbs_g, fat_g).
- **FR-007**: The saved plans section MUST order plans by generation date, newest first.
- **FR-008**: The user MUST be able to delete a saved plan block, removing all associated data.
- **FR-009**: The manual "Save Day" button/flow that previously existed MUST be removed; saving is now fully automatic on generation.
- **FR-010**: The food database search MUST remain accessible so users can find foods to add to custom meals as an alternative to editing generated plans.

### Key Entities

- **GeneratedDietPlan**: A single plan generation event; contains a generation date, goal type, caloric target, and 7 DietDay records.
- **DietDay**: One day within a plan; contains day number, 4 meal slots, and day-level macro totals.
- **DietMeal**: One meal slot (breakfast/lunch/dinner/snack); contains food items and meal-level macro totals.
- **DietaryRestriction**: A restriction tag on the user's profile (e.g. "vegetarian", "vegan", "gluten_free"); used to filter food items at plan generation time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero food items that violate the user's declared dietary restrictions appear in any generated plan (100% compliance, no exceptions).
- **SC-002**: After plan generation, the saved plans section reflects the new plan within the same page load (no manual refresh required).
- **SC-003**: All 7 days of a generated plan are visible within at most 2 UI interactions (click plan → see days).
- **SC-004**: Per-meal macro totals are visible within at most 3 UI interactions from the saved plans section landing state.
- **SC-005**: Existing plans previously saved remain visible and are not deleted by this change.

## Assumptions

- The user's dietary restrictions are stored in the `dietary_restrictions` table (already exists) and are accessible via the user's profile API.
- The recommendation service's `_filter_foods` function already correctly filters by restriction keys when passed; the bug is that the generation route passes an empty list instead of the user's actual restrictions fetched from their profile.
- The existing `structured_plan` JSON stored in diet recommendation records already contains the full 7-day meal data needed for display; no schema change is required for the display redesign.
- Auto-save on generation replaces the previous per-day save mechanism.
- The food database search feature already exists and does not require changes.
- Mobile-responsive layout is required for expanded plan/day/meal rows.
