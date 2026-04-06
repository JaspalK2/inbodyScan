# Implementation Plan: Profile & Diet Fixes

**Branch**: `010-profile-diet-fixes` | **Date**: 2026-04-05 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/010-profile-diet-fixes/spec.md`

## Summary

Fix six usability regressions across the profile page, diet recommendations, and saved meals tab:
1. Move Profile nav item adjacent to Sign Out in `nav.tsx`
2. Add error/success feedback to profile form (data was silently failing)
3. Add `activity_level` field to `UserProfile` DB model, profile page UI, and macro/diet generation calls
4. Add server-side macro validation + retry loop (≤3 attempts) to diet generation in `recommendation_service.py`
5. Add "Saved Days" section to `FoodMealsTab` in `recommendations/page.tsx`

All backend APIs and frontend queries already exist — this is a fix+enhancement pass, not greenfield.

## Technical Context

**Language/Version**: Python 3.13 (user-service, recommendation-service), TypeScript 5.x / Next.js 15 (frontend)  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 async, Pydantic v2 (backend); TanStack Query v5, React 18, react-hook-form, zod (frontend)  
**Storage**: Supabase PostgreSQL — `user_profiles` (add `activity_level` column), `health_goals`, `dietary_restrictions` (exist)  
**Testing**: pytest (backend), vitest (frontend — not yet installed; backend tests only for this feature)  
**Target Platform**: Web — Next.js 15 SSR + FastAPI microservices  
**Project Type**: Web application (multi-service)  
**Performance Goals**: Profile save < 500ms; diet generation retry adds ≤ 2× latency in worst case (acceptable for AI generation)  
**Constraints**: No new npm/pip dependencies; additive DB change only (new column, no table drops)  
**Scale/Scope**: Single-user profile record per user; diet retry loop bounded at 3 attempts

## Constitution Check

| Principle | Gate for this feature | Status |
|-----------|----------------------|--------|
| I — Extensibility | `activity_level` added as nullable column (additive); retry loop isolated in `_validate_diet_plan()` helper | ✓ PASS |
| II — Algorithm Efficiency | Retry loop O(1) bounded at 3; no new queries; `listDayPlans` already paginated | ✓ PASS |
| III — License Compliance | No new dependencies | ✓ PASS |
| IV — Mandatory Tests | pytest tests for diet retry logic + macro validator; profile schema tests | ✓ REQUIRED |
| V — UI/UX Consistency | Uses existing `glass-card`, `Button`, `Input`, `Label`, `Badge`, `select` components; activity level uses same `<select>` pattern as gender | ✓ PASS |
| Security — PII in prompts | Dietary restriction types are enums (no raw user text sent to LLM) | ✓ PASS |
| Security — User-scoped access | `listDayPlans` already filters by `user_id`; no new queries introduced | ✓ PASS |

**Constitution Check Result: PASS — no violations, no Complexity Tracking entries needed.**

## Project Structure

### Documentation (this feature)

```text
specs/010-profile-diet-fixes/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/           ← Phase 1 output
│   ├── profile-api.md
│   └── diet-generation.md
└── tasks.md             ← Phase 2 output (from /speckit.tasks)
```

### Source Code (files to modify)

```text
services/user-service/src/
├── models/profile.py                  ← add activity_level column
├── schemas/user.py                    ← add activity_level to ProfileOut + ProfileUpdate

services/recommendation-service/src/
├── services/recommendation_service.py ← add diet macro validation + retry loop
└── tests/
    ├── test_diet_macro_retry.py        ← NEW: diet retry loop tests
    └── test_profile_schema.py          ← NEW: activity_level schema tests (user-service)

frontend/
├── components/nav.tsx                  ← move Profile out of navItems → near Sign Out
├── app/(app)/profile/page.tsx          ← add activity_level selector + error/success states
├── app/(app)/recommendations/page.tsx  ← FoodMealsTab: add Saved Days section
└── lib/api.ts                          ← add activity_level to UserProfile interface
```

## Complexity Tracking

No constitution violations — table not required.
