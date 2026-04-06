# Implementation Plan: Editable AI-Generated Plans with Live Score & Macro Updates

**Branch**: `004-editable-ai-plans` | **Date**: 2026-04-02 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/004-editable-ai-plans/spec.md`

## Summary

Fix the Gemini 429 quota crash (currently surfaces as a 500 error) and add editing capability to AI-generated workout and diet plans. Workout editing triggers live quality score recalculation via the existing `score_workout_split` algorithm; diet editing triggers live macro pie chart updates computed client-side from the plan JSON. Both plan types already have `edited_plan` DB columns and `PATCH` endpoints — this feature wires the frontend, adds a workout scoring endpoint for generated plans, and adds Gemini error handling.

## Technical Context

**Language/Version**: Python 3.13 (recommendation-service), TypeScript 5.x / Next.js 15 (frontend)  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 async, Pydantic v2, google-generativeai, google-api-core (backend); Recharts, TanStack Query v5, React 18 (frontend)  
**Storage**: Supabase PostgreSQL — no schema changes required (`edited_plan` column already exists on both recommendation tables)  
**Testing**: pytest (backend unit + integration), Jest / React Testing Library (frontend)  
**Target Platform**: Linux server (recommendation-service), browser (Next.js frontend)  
**Project Type**: web-service (backend) + web-application (frontend)  
**Performance Goals**: Score update ≤ 1 s after edit; macro update ≤ 100 ms (client-side); plan generation ≤ 30 s  
**Constraints**: No new DB migrations; scoring algorithm must not be duplicated in frontend; LLM prompts must remain PII-free  
**Scale/Scope**: Single-user plan editing; plans are per-user, per-scan

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate for this Feature | Status |
|-----------|----------------------|--------|
| I — Extensibility | Scoring endpoint exposed as a distinct route; `GeminiClient` error handling isolated to the LLM client class; frontend edit state managed in a dedicated hook | PASS |
| II — Algorithm Efficiency | `score_workout_split` is O(n) in exercises — acceptable. Client-side macro aggregation is O(meals). DB queries use existing user-scoped `WHERE user_id = ?` filters. | PASS |
| III — License Compliance | `google-api-core` is Apache 2.0 (already a transitive dependency of `google-generativeai`). No new dependencies introduced. | PASS |
| IV — Mandatory Tests | Unit tests for Gemini error handler, workout plan score adapter, macro aggregation logic. Integration tests for `POST /score-plan` and `PATCH` save endpoints. E2E test for generate → edit → save flows. | REQUIRED — tasks must include test tasks |
| V — UI/UX Consistency | Edit mode UI must use existing shared component library (buttons, inputs, modals). Macro pie chart reuses existing Recharts `PieChart` component. Score display reuses existing score card component from workout splits. | PASS |

**Security Check**:
- LLM prompts already exclude PII (verified in `prompt_builder.py`)
- All new endpoints enforce `get_current_user_id` and filter by `user_id`
- No health data logged

## Project Structure

### Documentation (this feature)

```text
specs/004-editable-ai-plans/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── recommendation-api.md   # New endpoint + error contract
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code

```text
services/recommendation-service/src/
├── llm/
│   └── gemini_client.py          # ADD: try/except ResourceExhausted → 503
├── schemas/
│   └── recommendation.py         # ADD: WorkoutScorePlanRequest schema
├── routers/
│   └── recommendations.py        # ADD: POST /workout/score-plan endpoint
└── services/
    └── recommendation_service.py  # No changes required

frontend/src/
├── components/recommendations/
│   ├── WorkoutPlanCard.tsx        # NEW: render + edit workout plan
│   ├── DietPlanCard.tsx           # NEW: render + edit diet plan
│   └── MacroPieChart.tsx          # NEW or extend existing chart component
├── hooks/
│   ├── useWorkoutPlanEditor.ts    # NEW: edit state + debounced score API call
│   └── useDietPlanEditor.ts       # NEW: edit state + client-side macro computation
└── app/recommendations/
    └── page.tsx                   # MODIFY: wire generate buttons + plan card components
```

**Structure Decision**: Microservices layout matches existing project. Backend changes are isolated to the recommendation-service. Frontend changes are isolated to the recommendations feature directory.

## Complexity Tracking

No constitution violations.
