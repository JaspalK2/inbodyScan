# Research: Editable AI-Generated Plans

**Feature**: 004-editable-ai-plans  
**Date**: 2026-04-02

---

## Decision 1: Gemini 429 / ResourceExhausted Error Handling

**Decision**: Catch `google.api_core.exceptions.ResourceExhausted` inside `GeminiClient.generate()` and raise `fastapi.HTTPException(status_code=503)` with a user-friendly message.

**Rationale**: The error currently propagates uncaught, resulting in a 500 response. The correct HTTP status for "service temporarily unavailable due to quota" is 503 (not 429 — the upstream quota is not the client's quota). A 503 signals to the frontend that a retry is appropriate.

**Implementation location**: `services/recommendation-service/src/llm/gemini_client.py` — wrap `generate_content_async` in `try/except`.

**Alternatives considered**:
- Catching in `recommendation_service.py`: rejected — the LLM client is the right boundary; it owns the Gemini API contract and should not leak Gemini-specific exceptions upward.
- Re-raising as 429 to the client: rejected — 429 means *the client* is rate-limited; 503 correctly indicates a downstream service issue.

---

## Decision 2: Workout Quality Score for Generated Plans

**Decision**: Reuse `score_workout_split(days: list[dict])` from `services/workout_scorer.py`. Add a new endpoint `POST /recommendations/workout/score-plan` that accepts the generated plan's exercise structure and returns a `WorkoutScoreOut`.

**Rationale**: `score_workout_split` already implements the full scoring algorithm. The generated workout plan JSON uses `{"name": ..., "sets": ..., "reps": ...}` while the scorer expects `{"exercise_name": ..., "sets": ..., "reps": ...}`. A thin adapter in the new endpoint normalises the field name before calling the scorer.

**Adapter logic**: In the new endpoint, map each exercise's `name` → `exercise_name` and flatten the week/day nested structure into a flat list of day dicts expected by the scorer.

**Alternatives considered**:
- Scoring inside `generate_workout_recommendation`: rejected — scoring at generation time is correct for the initial display, but re-scoring on every edit requires a separate endpoint anyway. The initial score is computed the same way.
- Modifying `score_workout_split` to accept both field names: rejected — unnecessary complexity; the adapter belongs at the API boundary.

---

## Decision 3: No Database Migration Required

**Decision**: Proceed without any schema changes. Both `WorkoutRecommendation` and `DietRecommendation` models already have `edited_plan: Mapped[str | None] = mapped_column(Text)`. The `PATCH /workout/{id}` and `PATCH /diet/{id}` endpoints already exist and persist edits.

**Rationale**: The editing persistence layer is already implemented from the previous 002 feature work. This feature only needs to wire the frontend to those endpoints and add the live score/macro update logic.

---

## Decision 4: Live Macro Updates — Client-Side Computation

**Decision**: Compute updated macro totals in the browser from the plan JSON, without round-tripping to the backend.

**Rationale**: The diet plan JSON from the LLM already includes `protein_g`, `carbs_g`, `fat_g`, `calories` per meal. When the user edits a portion or food item, the frontend can recompute day-level totals by summing meal values. No server call is needed for display; the save (`PATCH /diet/{id}`) is a separate action.

**Alternatives considered**:
- Server-side macro recalculation endpoint: rejected — unnecessary latency and complexity; all data needed for aggregation is already in the plan JSON held in client state.

---

## Decision 5: Live Workout Score Updates — Debounced API Call

**Decision**: Compute the updated workout score via a debounced call to the new `POST /recommendations/workout/score-plan` endpoint (300 ms debounce) whenever the user changes sets, reps, or exercises in edit mode.

**Rationale**: Unlike macros (pure aggregation), the workout score uses a non-trivial algorithm (`score_workout_split`) that accounts for muscle-group coverage, volume, balance, and cardio. Replicating this in the browser would create a maintenance dual-implementation. A 300 ms debounce prevents excessive calls while still feeling instantaneous per FR-006.

**Alternatives considered**:
- Client-side score recomputation: rejected — the scoring algorithm uses muscle-group heuristics that would be complex to port to TypeScript and would diverge from the Python implementation over time.

---

## Decision 6: Edit Mode Is Per-Plan (Not Per-Exercise)

**Decision**: The user enters and exits edit mode for the whole plan at once, per the spec assumption. No concurrent editing of individual items while others are read-only.

**Rationale**: Simplest UX model. The spec explicitly states this assumption. Per-item edit mode would require more complex state management and optimistic concurrency controls.

---

## Decision 7: Overwrite Confirmation on Re-generate

**Decision**: When the user clicks "Generate" for a plan type that already has a saved plan, show a confirmation dialog before overwriting.

**Rationale**: FR-009 (discard) and the edge case in the spec both require protecting edited work. If a user re-generates, the previous `edited_plan` would be cleared. The confirmation prompt satisfies the edge case requirement.

**Implementation**: Frontend-only check — if `GET /recommendations/workout` or `GET /recommendations/diet` returns an existing record, show a modal before calling the generate endpoint.
