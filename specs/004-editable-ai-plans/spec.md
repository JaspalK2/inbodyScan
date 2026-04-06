# Feature Specification: Editable AI-Generated Plans with Live Score & Macro Updates

**Feature Branch**: `004-editable-ai-plans`
**Created**: 2026-04-02
**Status**: Draft
**Input**: User description: "As a user I want to generate workout and diet plans. The plans should be editable — editing workout plan exercises/sets/reps should update the workout quality score live, and editing diet plan meals/portions should update the macro pie chart live."

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Generate & View AI Plans (Priority: P1)

A user with an InBody scan on record clicks "Generate" for either a workout plan or a diet plan and receives a complete AI-generated plan. If the AI service is temporarily unavailable or rate-limited, the user sees a clear, actionable error message rather than a generic 500 error.

**Why this priority**: Without a working generation flow nothing else in this feature can function. Fixing the crash and unblocking generation is the prerequisite for all downstream editing work.

**Independent Test**: Navigate to the Recommendations page → click "Generate Workout Plan" → a plan with exercises, sets, and reps appears. Repeat for "Generate Diet Plan" → a plan with meals and macros appears. Trigger a quota error (or mock one) → confirm a retry-friendly message appears instead of a crash.

**Acceptance Scenarios**:

1. **Given** the user has at least one scan uploaded, **When** they click "Generate Workout Plan," **Then** a structured plan with named exercises, sets, reps, and a workout quality score is displayed within 30 seconds.
2. **Given** the user has at least one scan uploaded, **When** they click "Generate Diet Plan," **Then** a structured plan with daily meals, ingredients, and a macro breakdown (protein, carbs, fat, calories) is displayed within 30 seconds.
3. **Given** the AI service is rate-limited or unavailable, **When** the user attempts to generate a plan, **Then** a user-friendly error message is shown (e.g., "Plan generation is temporarily unavailable — please try again shortly") with a retry button; no 500 error page is shown.
4. **Given** the user has no scan on record, **When** they attempt to generate a plan, **Then** they are prompted to upload a scan first.

---

### User Story 2 — Edit Workout Plan with Live Score (Priority: P2)

After a workout plan is generated, the user can edit individual exercises, sets, reps, and notes. The workout quality score recalculates instantly after each edit so the user can see the impact of their changes. The unmodified AI-generated plan starts at the best achievable score for their goals.

**Why this priority**: Personalisation is the primary value of an editable plan. Users need to adapt plans to equipment and physical limitations while understanding the quality trade-off.

**Independent Test**: Generate a workout plan → enter edit mode → change the reps on any exercise → confirm the workout quality score updates within 1 second without a page reload.

**Acceptance Scenarios**:

1. **Given** a workout plan is displayed, **When** the user enters edit mode, **Then** all exercises, sets, reps, and notes become editable inline.
2. **Given** the user is editing, **When** they change any field, **Then** the workout quality score updates within 1 second.
3. **Given** the unedited AI-generated plan, **When** it is first displayed, **Then** the workout quality score reflects the optimal score for the user's goals.
4. **Given** the user saves edits, **When** they return to the page later, **Then** the edited plan and its score are correctly displayed.
5. **Given** the user has unsaved edits, **When** they click discard, **Then** the plan and score revert to the last saved version.

---

### User Story 3 — Edit Diet Plan with Live Macro Chart (Priority: P2)

After a diet plan is generated, the user can edit meal names, food items, and portion sizes. The macro pie chart (protein / carbs / fat) updates in real time to reflect the new totals, giving immediate feedback on whether edits stay within dietary targets.

**Why this priority**: Same motivation as US2 — the diet plan must adapt to food preferences and availability. Real-time macro feedback closes the loop between edits and nutritional goals.

**Independent Test**: Generate a diet plan → enter edit mode → increase the protein portion on any meal → confirm the protein slice of the macro pie chart grows within 1 second without a page reload.

**Acceptance Scenarios**:

1. **Given** a diet plan is displayed, **When** the user enters edit mode, **Then** all meals, food items, and portion sizes become editable inline.
2. **Given** the user is editing, **When** they change any portion size or food item, **Then** the macro pie chart updates within 1 second.
3. **Given** the unedited AI-generated plan, **When** it is first displayed, **Then** the macro totals in the pie chart match the values from the plan generator.
4. **Given** the user saves edits, **When** they return to the page later, **Then** the edited plan and updated macro values are correctly displayed.
5. **Given** the user has unsaved edits, **When** they click discard, **Then** the plan and pie chart revert to the last saved state.

---

### Edge Cases

- What happens when the AI service returns HTTP 429 (quota exhausted)? → Show a retry-friendly error; do not propagate a 500 to the user.
- What happens when the AI returns a plan with missing or malformed data? → Show a parse error with an option to regenerate.
- What happens if the user sets sets or reps to 0 on a workout exercise? → Validate inline; prevent saving with a clear message.
- What happens if a food portion is edited to 0g? → Treat as removed from macro calculation; warn if total daily calories fall below a safe minimum.
- What happens if the user generates a new plan while an edited plan is already saved? → Prompt to confirm overwrite before replacing the saved plan.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST catch AI service rate-limit (quota exhausted) errors and return a user-friendly message with a retry option, rather than a 500 internal server error.
- **FR-002**: The system MUST generate a workout plan containing at minimum: a list of exercises with name, sets, reps, and a 0–100 workout quality score.
- **FR-003**: The system MUST generate a diet plan containing at minimum: a list of daily meals each with food items, portion sizes, and per-meal macro totals (protein g, carbs g, fat g, calories kcal).
- **FR-004**: Users MUST be able to enter an edit mode on any generated workout plan and modify exercise name, sets, reps, and optional notes per exercise.
- **FR-005**: Users MUST be able to enter an edit mode on any generated diet plan and modify meal name, food items, and portion sizes.
- **FR-006**: The workout quality score MUST recalculate and display within 1 second of any edit while in workout edit mode.
- **FR-007**: The macro pie chart MUST update to reflect new totals within 1 second of any edit while in diet edit mode.
- **FR-008**: Users MUST be able to save their edited plans; saved edits MUST persist across page reloads and sessions.
- **FR-009**: Users MUST be able to discard unsaved edits and revert the plan and score/chart to the last saved version.
- **FR-010**: The unedited AI-generated workout plan MUST display the maximum achievable quality score for the user's scan metrics and goal type.

### Key Entities

- **WorkoutPlan**: A generated or user-edited collection of exercises for a specific user and scan; attributes include goal type, quality score, and a list of exercises (name, sets, reps, notes).
- **DietPlan**: A generated or user-edited collection of daily meals; attributes include a list of meals each containing food items with portion sizes and macro totals.
- **WorkoutQualityScore**: A 0–100 numeric score derived from how well a workout plan matches the user's body composition metrics and goal.
- **MacroTotals**: Aggregated daily totals for protein (g), carbohydrates (g), fat (g), and calories (kcal) computed from all food items in a diet plan.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Plan generation succeeds for 95%+ of attempts when the AI service is within quota; rate-limit errors always surface a retry prompt, never a crash.
- **SC-002**: Plan generation completes and is displayed within 30 seconds from button click.
- **SC-003**: Workout score and macro chart updates appear within 1 second of any field edit in edit mode (no full-page reload).
- **SC-004**: Edited plans survive a page reload and display correctly in subsequent sessions.
- **SC-005**: Users complete the full "generate → edit → save" flow for both plan types without encountering an unhandled error.

## Assumptions

- The user has at least one InBody scan uploaded; plan generation requires scan data as input.
- The existing Gemini-backed recommendation service provides the generation endpoints; this feature adds error handling and an editing layer on top.
- Workout quality scoring logic already exists in the codebase (used for workout split scoring) and can be reused for generated workout plan scoring.
- Macro calculation uses the food/ingredient data already stored with the generated diet plan; no external nutrition lookup is needed during editing.
- Edit mode is per-plan (the user enters and exits edit mode for the whole plan at once, not individual exercises/meals).
- Resolving the Gemini free-tier quota issue (enabling billing or switching to a model with available quota) is a deployment/configuration step; this feature adds resilient error handling as a safety net regardless of quota status.
