# Feature Specification: Algorithmic Plan Engine (Zero-Cost, No-Quota)

**Feature Branch**: `013-algorithmic-plan-engine`  
**Created**: 2026-04-05  
**Status**: Draft  
**Input**: Replace all LLM-based plan generation with a free, deterministic algorithm so plans always generate reliably with no API costs, no quotas, and no external dependencies.

## Background

The current plan generation uses Groq (free tier) and Gemini (free tier) as LLM backends. Both have hit their free-tier quotas, leaving users unable to generate plans. The solution is to replace the LLM dependency with a deterministic rule-based engine built on established fitness and nutrition science — the same principles any certified personal trainer or sports nutritionist uses. This makes plan generation instant, reliable, free forever, and explainable.

The codebase already has:
- A complete macro calculator (Mifflin-St Jeor BMR, TDEE, goal-based macro targets)
- A database of 873 exercises tagged by muscle group, category, and equipment
- Food search via the USDA database

## Clarifications

### Session 2026-04-05

- Q: How should the food database be built and maintained? → A: Seeded from USDA Food Data Central API via a one-time script; refreshed weekly by a scheduled background job. Plan generation reads only the local file — no live API call at generation time.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Algorithmic Workout Plan Generation (Priority: P1)

A user selects a health goal and clicks "Generate Weekly Workout Plan." The system deterministically builds a 7-day workout split (5 training days + 2 rest days) using the exercise database and established training principles — covering all required muscle groups, including compound lifts, and producing the same quality output as the previous AI system. No external API call is made. The plan generates in under 1 second.

**Why this priority**: Workout generation is the most visible broken feature. The exercise database already exists. This is achievable with pure algorithm.

**Independent Test**: Click "Generate Weekly Workout Plan" with no LLM running — a complete 7-day plan with exercises, sets, reps, and a plan explanation must appear.

**Acceptance Scenarios**:

1. **Given** a user with body composition data and a "muscle gain" goal, **When** they generate a workout plan, **Then** a 7-day plan appears covering all major muscle groups (chest, back, shoulders, arms, legs, core) with compound and isolation exercises, sets, reps, rest periods, and a short explanation referencing their body composition.
2. **Given** a user with high body fat percentage, **When** they generate a workout plan, **Then** at least one dedicated cardio session is included and the plan explanation mentions fat loss emphasis.
3. **Given** any user, **When** they generate a workout plan, **Then** the plan is produced in under 2 seconds with no error message.
4. **Given** a user who generates the same plan twice with the same inputs, **Then** the output is consistent and logical (deterministic or stable-random).

---

### User Story 2 - Algorithmic Diet Plan Generation (Priority: P1)

A user selects a health goal and clicks "Generate 7-Day Meal Plan." The system uses the pre-calculated macro targets (already computed by the existing macro calculator) and builds a structured 7-day meal plan algorithmically — selecting meals, foods, and portions that hit the macro targets within ±5% per day. No external API call is made. Day totals are computed by summing individual meal values (never hallucinated).

**Why this priority**: Diet generation is equally broken. The macro targets are already calculated algorithmically — only meal selection needs replacing.

**Independent Test**: Click "Generate 7-Day Meal Plan" with no LLM running — a complete plan with 4 meals/day for 7 days, each with foods and macro values summing correctly to daily targets, must appear.

**Acceptance Scenarios**:

1. **Given** a user with macro targets of 2200 kcal, 165g protein, 250g carbs, 73g fat, **When** they generate a meal plan, **Then** each day's meals sum to within ±5% of those targets.
2. **Given** a user with vegetarian dietary restrictions, **When** they generate a meal plan, **Then** no meat, poultry, or fish appears in any meal.
3. **Given** any user, **When** they generate a diet plan, **Then** the plan is produced in under 2 seconds with no error message.
4. **Given** the generated plan, **Then** the day totals displayed match the sum of the individual meal macros exactly (no discrepancy).

---

### User Story 3 - Plan Explanation Without LLM (Priority: P2)

Each generated plan (diet and workout) includes a short, meaningful explanation of why this plan was chosen — referencing the user's actual body composition metrics (body fat %, lean mass, weight) and goal. This explanation is generated algorithmically from templates populated with real metric values, not from an LLM.

**Why this priority**: The "Why this plan?" explanation was added in feature 011 and must continue working after the LLM is removed.

**Independent Test**: Generate a workout plan for a user with 28% body fat — the explanation must mention body fat, identify areas needing work, and reference the goal without requiring any LLM.

**Acceptance Scenarios**:

1. **Given** a user with 28% body fat and a "lose fat" goal, **When** a plan is generated, **Then** the explanation mentions reducing body fat, includes a cardio emphasis rationale, and references specific metrics.
2. **Given** a user with high lean mass and a "build muscle" goal, **When** a plan is generated, **Then** the explanation acknowledges their strong base and focuses on progressive overload.

---

### Edge Cases

- What if the user has no scan data (missing body fat %, weight)? Use reasonable defaults and still generate a plan.
- What if the user selects a dietary restriction that removes all protein sources? Fall back gracefully with a message.
- What if the exercise database has no exercises for a required muscle group? Log a warning and use closest available.
- What if the user rapidly regenerates plans back-to-back? Each generation should be fast and stable.

## Requirements *(mandatory)*

### Functional Requirements

**Workout Algorithm:**
- **FR-001**: The workout engine MUST produce a 7-day split covering all of: chest, upper back, lower back, front/side/rear deltoids, biceps, triceps, quadriceps, hamstrings, glutes, calves, core.
- **FR-002**: The workout engine MUST include at least one compound movement from each of: squat pattern, hinge pattern (deadlift), push pattern (bench), pull pattern (row), vertical push (overhead press).
- **FR-003**: The workout engine MUST include at least one dedicated cardio session per week.
- **FR-004**: Each training day MUST specify: exercise name, sets, reps, rest period in seconds, and a brief form note.
- **FR-005**: The workout engine MUST adjust exercise selection and volume based on the user's body fat percentage and goal type (e.g., more cardio for high body fat / fat loss goals).
- **FR-006**: The workout plan MUST include a `plan_explanation` field populated with template text referencing the user's actual metrics.

**Diet Algorithm:**
- **FR-007**: The diet engine MUST use the macro targets produced by the existing macro calculator as its input.
- **FR-008**: The diet engine MUST produce 4 meals per day (breakfast, lunch, dinner, snack) for 7 days.
- **FR-009**: Each meal MUST specify: meal name, list of foods with portions, and macro values (calories, protein, carbs, fat).
- **FR-010**: Each day's meal macro values MUST sum to within ±5% of the daily macro targets.
- **FR-011**: The diet engine MUST respect dietary restrictions (vegetarian, vegan, gluten-free, dairy-free, halal, kosher) by excluding non-compliant foods.
- **FR-012**: The day_totals field in the response MUST be computed by summing the individual meal values — never estimated or assumed.
- **FR-013**: The diet engine MUST use a local food database file seeded from the USDA Food Data Central API. A one-time seed script populates the file; a scheduled background job refreshes it weekly to pick up any updated nutritional data. Plan generation reads only the local file — no live API calls at generation time.

- **FR-013a**: A seed script MUST exist that fetches ~100–200 common whole foods from the USDA Food Data Central API and writes them to a local JSON file in the recommendation service.
- **FR-013b**: A scheduled job MUST run weekly to re-run the seed script and update the local food database file, keeping nutritional data current without manual intervention.

**General:**
- **FR-014**: Both engines MUST produce a complete plan in under 2 seconds.
- **FR-015**: Both engines MUST NOT make any external API calls during plan generation.
- **FR-016**: The LLM client (`get_llm_client`) MUST be completely removed from both generation functions; the new engines replace it entirely.
- **FR-017**: The existing response schema (JSON structure, field names) MUST be preserved so the frontend requires no changes.

### Key Entities

- **Meal Template**: A named combination of foods with macro values that fits a meal slot (breakfast/lunch/dinner/snack) and respects dietary restrictions.
- **Weekly Workout Split**: An assignment of muscle groups and exercises to each of 7 days, with 5 training days and 2 rest days.
- **Plan Explanation**: Template-populated text referencing the user's body fat %, lean mass, weight, and goal type.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of plan generation requests succeed — zero "temporarily unavailable" or error responses under normal conditions.
- **SC-002**: Plans are delivered in under 2 seconds for 100% of requests.
- **SC-003**: Diet plan day totals are within ±5% of macro targets for 100% of generated days.
- **SC-004**: Workout plans cover all 13 required muscle groups in 100% of generated plans.
- **SC-005**: Zero external API calls are made during plan generation (verifiable by running with all API keys removed).
- **SC-006**: All existing tests continue to pass; no frontend changes are required.

## Assumptions

- The existing 873-exercise database is sufficient to cover all required muscle groups and movement patterns.
- The food database is seeded from USDA Food Data Central (free API, no billing required) via a one-time script and refreshed weekly by a scheduled job. ~100–200 common whole foods are sufficient to generate varied 7-day plans.
- The frontend response schema (the JSON structure of `structured_plan`) does not need to change — only the generation mechanism changes.
- Dietary restriction filtering is based on ingredient category exclusion (e.g., no meat for vegetarian), not live ingredient parsing.
- The `plan_explanation` field will use template strings populated with actual metric values rather than natural language generation — this is acceptable since the explanations are factual and structured.
- The LLM provider code (`gemini_client.py`, `prompt_builder.py`) will be retained as dead code for now rather than deleted, to avoid breaking any imports.
- Plans need not be perfectly varied across all 7 days — reasonable repetition (e.g., same breakfast 2–3 days) is acceptable for an algorithmic engine.
