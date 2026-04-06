# Research: Fix Dietary Restriction Enforcement & Redesign Diet Plan Saved Meals UX

**Branch**: `018-diet-restrictions-plan-ux`  
**Date**: 2026-04-06

---

## Decision 1: Root Cause of Dietary Restriction Violation Bug

**Decision**: The bug is a data-quality defect in `services/recommendation-service/src/data/foods.json`, not a logic or data-flow bug.

**Rationale**: Investigation confirmed:
- The frontend correctly fetches the user's `dietary_restrictions` from `/api/users/me/dietary-restrictions` and maps them to `restriction_type` strings (e.g. `"vegetarian"`).
- The restriction strings are correctly passed in the POST body to `/api/recommendations/diet/generate`.
- The route handler correctly passes `body.dietary_restrictions` → `generate_diet_recommendation()` → `generate_diet_plan()` → `_build_day()` → `_filter_foods()`.
- `_filter_foods` correctly skips any food where `food_restrictions[r] == False` for each restriction `r`.
- **Actual bug**: 6 food items in foods.json have incorrect restriction flags. Specifically, items containing chicken, beef, fish, or shrimp are marked `vegetarian: True` and `vegan: True`, allowing them to pass the vegetarian filter. The items are:
  1. `Chicken, thighs, frozen, breaded, reheated` — `vegetarian: True, vegan: True` (should be `False`)
  2. `ON THE BORDER, soft taco with ground beef, cheese and lettuce` — `vegetarian: True, vegan: True` (should be `False`)
  3. `Fish oil, salmon` — `vegetarian: True, vegan: True` (fish oil is not vegetarian; should be `False`)
  4. `Snacks, shrimp cracker` — `vegetarian: True, vegan: True` (contains shrimp extract; should be `False`)
  5. `APPLEBEE'S, Double Crunch Shrimp` — `vegetarian: True, vegan: True` (shrimp; should be `False`)
  6. `DENNY'S, golden fried shrimp` — `vegetarian: True, vegan: True` (shrimp; should be `False`)

**Alternatives considered**:
- Adding a secondary keyword-based filter in `_filter_foods`: rejected — this is fragile and masks the real data problem; fixing the data source is the correct approach.
- Fetching restrictions server-side from the user profile rather than trusting the client to pass them: considered as a defence-in-depth improvement, but the current data-passing flow is already correct, so a data fix is sufficient to resolve the reported bug. Server-side fetch can be a future hardening step.

**Fix scope**: Correct the 6 incorrect entries. Additionally, a test must be added to `test_diet_engine.py` that generates a vegetarian plan and asserts zero non-vegetarian items slip through (reusing the existing `test_vegetarian_restriction_filters_meat` test pattern but asserting on known non-vegetarian food names).

---

## Decision 2: Auto-Save All 7 Days on Generation

**Decision**: On a successful `POST /api/recommendations/diet/generate` response, the frontend will immediately call `POST /api/recommendations/day-plans` once per day (7 calls) to persist all 7 days, replacing the previous manual "Save day" button.

**Rationale**:
- The `DietRecommendation` record already stores the full 7-day `structured_plan` JSON. However, day plans are stored separately in `day_plans` / `day_plan_entries` tables and are what the "My Saved Meals" section displays.
- The simplest approach with zero backend schema changes is to fire 7 sequential `createDayPlan` calls from the mutation's `onSuccess` callback, using the same payload shape as the existing manual save function.
- Alternatively, a backend batch-save endpoint could be added; this is cleaner but adds scope. Given the 7-day fixed structure, 7 client calls is acceptable latency (~7 lightweight writes).

**Alternatives considered**:
- New backend endpoint `POST /api/recommendations/diet/{id}/save-all-days`: cleaner, single round-trip, but adds backend scope and a new route to test. Deferred to future optimization.
- Auto-save directly inside `generate_diet_recommendation()` in the service layer: would couple recommendation generation to day-plan storage, violating SRP. Rejected.

---

## Decision 3: Saved Plans Section UI Redesign

**Decision**: Redesign the "Saved Day Plans" section within `FoodMealsTab` to display plans grouped by generation event. Since the existing `day_plans` table does not have a `recommendation_id` column, plans saved from the same generation event will be grouped by `plan_date` + a shared name prefix. New auto-saved plans will use a consistent naming convention `AI Plan YYYY-MM-DD (Day N)` so they can be grouped by date prefix on the frontend.

**Rationale**:
- `day_plans` has `name`, `plan_date`, `notes`, and `created_at` columns. The `notes` field already stores the recommendation ID (set by the existing manual save code). We can group auto-saved plans by `notes` (recommendation ID) to identify plans from the same generation event.
- Grouping by `notes` (rec ID) is the most reliable approach: all 7 days from one generation share the same `rec_id` in `notes`.
- The UI becomes: one collapsible card per unique `notes` value (rec ID), labelled with `created_at` date. Each card expands to show Day 1–7 rows. Each day row expands to show meals + macros from `items_snapshot`.

**Alternatives considered**:
- Add `recommendation_id` column to `day_plans`: cleanest data model, but requires a schema migration. The `notes` field already stores this value — using it avoids a migration. Can be migrated properly in a future cleanup ticket.
- Group by `plan_date` + same day of creation: fragile if user generates two plans on the same day. Rejected.

---

## Decision 4: Remove Manual "Save Day" Button

**Decision**: Remove the `saveDayPlan` function and "Save day" button from `DietDayRow`. Replace with a UI indicator showing "Auto-saved" after generation completes.

**Rationale**: Once auto-save is implemented, the manual button is redundant and confusing. The user's request explicitly asked to remove it.

---

## Decision 5: No Schema Changes Required

**Decision**: No database migrations are needed for this feature.

**Rationale**:
- US1 (data fix): only `foods.json` changes.
- US2 (UX redesign): the existing `day_plans`, `day_plan_entries`, and `diet_recommendations` tables have all required fields. Grouping by `notes` (rec ID) enables plan-level display without schema changes.
