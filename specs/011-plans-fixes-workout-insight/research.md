# Research: Plans UX Fixes and Workout Insights

**Feature**: 011-plans-fixes-workout-insight  
**Date**: 2026-04-05

---

## Decision 1: Diet Day Totals Fix Strategy

**Decision**: Compute day totals on the frontend by summing individual meal values; discard AI-returned `day_totals`.

**Rationale**: The AI currently returns a `day_totals` object per day that does not match the arithmetic sum of the meals it also returns. The clarified approach (US1, Q1) is to ignore AI-provided totals entirely and derive them on the display side. This is the simplest, most reliable fix — it is O(n) over meals, always correct, and requires no prompt changes or backend work.

**Alternatives considered**:
- Fix the AI prompt to generate accurate totals — rejected: prompt engineering is non-deterministic; even a corrected prompt may occasionally produce totals that still don't match meal values
- Fix server-side after LLM response — rejected: adds backend complexity for something that can be done purely on the display layer

**Implementation note**: In `recommendations/page.tsx`, replace all reads of `day.day_totals` with a computed sum over `day.meals` (or equivalent meal array). The existing "Live Macro Totals" edit-mode code (line 569-599) already demonstrates this pattern and can be extracted into a shared helper.

---

## Decision 2: Activity Level Source for Plan Generation

**Decision**: Remove the activity level `<select>` from the Plans page. Read `profile.activity_level` from the already-fetched user profile query and pass it directly to `generateDiet`. Default to `"moderately_active"` if unset.

**Rationale**: The Plans page already fetches the user profile via TanStack Query (`useQuery(["profile"])`). The `activity_level` field is available in the `UserProfile` interface (added in feature 010). Removing the duplicate selector eliminates the inconsistency risk identified in US2. The backend `generateDiet` call already accepts `activity_level` as a parameter (api.ts line 153).

**Alternatives considered**:
- Keep selector but pre-populate from profile — rejected: user can still override and introduce inconsistency
- Pass activity level from profile to workout generation as well — adopted: the workout prompt builder can benefit from this context too even though it doesn't currently use it for macro calculation

---

## Decision 3: Saved Day Plans Visibility

**Decision**: The `dayPlans` query already exists (`recommendations.listDayPlans()`) and data is already fetched. The bug is a rendering/filtering issue: the "My Saved Meals" section filters by `!m.name.startsWith("Day Planner")` and the Day Planner section reads from custom meals rather than the `dayPlans` list. Fix: render `dayPlans` directly from the `listDayPlans` query result in both sections.

**Rationale**: No backend change needed. The data pipeline (Log button → POST day plan → DB) is confirmed working. The disconnect is purely in how the frontend renders the results.

**Alternatives considered**:
- Re-architect the day plan storage — rejected: the existing `day_plans` table and `listDayPlans` endpoint already provide what's needed

---

## Decision 4: Workout Plan Deletion

**Decision**: Add a `DELETE /api/recommendations/workout/{rec_id}` endpoint to the recommendation-service. Add a delete button + confirmation dialog to the workout plan cards in the frontend.

**Rationale**: The diet plan already has a delete endpoint (line 267 of recommendations.py). The workout router is missing the equivalent. Adding it follows the exact same pattern (auth check, ownership check, delete from DB, return 204).

**Implementation note**: Hard delete, no recovery. The confirmation UI should be an inline "Are you sure?" state on the card (show Confirm/Cancel buttons), not a modal — consistent with the existing diet plan delete pattern if one exists, or following the project's glass-card component style.

---

## Decision 5: Workout Plan Body-Composition Explanation

**Decision**: Enhance the workout prompt to explicitly request a `plan_explanation` field (separate from `summary`) that references the user's specific scan metrics (muscle mass, body fat %, segmental lean analysis if available) and explains which muscle groups need work vs. are strong. Display this field at the top of each workout plan card before the exercise list.

**Rationale**: The existing `summary` field (prompt line 98) is a generic program description. The new `plan_explanation` field needs to be specifically tied to the user's body composition data passed in the prompt. Since the scan metrics are already included in the workout prompt, the LLM has the data it needs — the prompt just needs to instruct it to produce this explanation in a dedicated field.

**Implementation note**: No DB schema change needed — `plan_explanation` can be a top-level key within the `structured_plan` JSON blob (same pattern as `summary`). The frontend reads it from `structured_plan.plan_explanation` and falls back to `structured_plan.summary` if absent (for backward compatibility with existing plans).

**Alternatives considered**:
- Store `plan_explanation` as a separate DB column — rejected: unnecessary schema migration; the JSON blob is the established pattern for this service
- Generate explanation separately post-creation — rejected: adds latency and complexity; the LLM already has all needed context at generation time
