# inbodyScan-Analyzer Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-04-06

## Active Technologies
- Python 3.13 (recommendation-service backend), TypeScript 5.x / Next.js 15 (frontend) + FastAPI, SQLAlchemy 2.0 async, asyncpg, Pydantic v2, Recharts, TanStack Query v5 — all already presen (002-food-meal-tracker)
- Supabase PostgreSQL (shared instance) — new `daily_food_log_entries` table (002-food-meal-tracker)
- Python 3.13 (auth-service backend), TypeScript 5.x / Next.js 15 (frontend) + FastAPI, SQLAlchemy 2.0 async (existing); `google-auth` 2.37.0 (new, Apache 2.0); `@react-oauth/google` (new, Apache 2.0) (003-google-oauth-login)
- Supabase PostgreSQL — `auth_users` table extended; `google_link_requests` table added (003-google-oauth-login)
- Python 3.13 (recommendation-service), TypeScript 5.x / Next.js 15 (frontend) + FastAPI, SQLAlchemy 2.0 async, Pydantic v2, google-generativeai, google-api-core (backend); Recharts, TanStack Query v5, React 18 (frontend) (004-editable-ai-plans)
- Supabase PostgreSQL — no schema changes required (`edited_plan` column already exists on both recommendation tables) (004-editable-ai-plans)
- Python 3.13 (recommendation-service), TypeScript 5.x / Next.js 15 (frontend) + FastAPI, SQLAlchemy 2.0 async, Pydantic v2 (backend); TanStack Query v5, React 18 (frontend) (005-plan-editing-fixes)
- TypeScript 5.x / Next.js 15 (frontend only) + React 18, TanStack Query v5, existing UI component library (Button, Input, Label, Loader2, etc.) (006-plan-save-workout-ux)
- Supabase PostgreSQL — no schema changes; existing `custom_meals`, `day_plans`, `workout_recommendations`, `workout_splits` tables (006-plan-save-workout-ux)
- Python 3.13 (backend), TypeScript 5.x (frontend) + FastAPI, SQLAlchemy 2.0 async (backend); Next.js 15, TanStack Query v5, React 18 (frontend) (007-plan-log-workout-fixes)
- Python 3.13 (backend services), TypeScript 5.x / Next.js 15 (frontend) + FastAPI, SQLAlchemy 2.0 async, Pydantic v2 (backend); TanStack Query v5, React 18, Tailwind CSS (frontend) (009-workout-diet-ux-fixes)
- Python 3.13 (user-service, recommendation-service), TypeScript 5.x / Next.js 15 (frontend) + FastAPI, SQLAlchemy 2.0 async, Pydantic v2 (backend); TanStack Query v5, React 18, react-hook-form, zod (frontend) (010-profile-diet-fixes)
- Supabase PostgreSQL — `user_profiles` (add `activity_level` column), `health_goals`, `dietary_restrictions` (exist) (010-profile-diet-fixes)
- Python 3.13 (recommendation-service), TypeScript 5.x / Next.js 15 (frontend) + FastAPI, SQLAlchemy 2.0 async, Pydantic v2 (backend); TanStack Query v5, React 18, Tailwind CSS (frontend) (011-plans-fixes-workout-insight)
- Python 3.13 (recommendation-service backend) + FastAPI 0.115, SQLAlchemy 2.0 async, httpx 0.28 (all existing); APScheduler 3.11 (new, MIT) (013-algorithmic-plan-engine)
- Supabase PostgreSQL (existing, unchanged); `src/data/foods.json` (new local file) (013-algorithmic-plan-engine)
- TypeScript 5.x / Next.js 15 (Turbopack) + React 18, TanStack Query v5, existing Tailwind CSS + shadcn/ui component library (014-fix-diet-meal-render)
- No schema change — plan JSON is already stored in `structured_plan` / `edited_plan` columns; fix is rendering-only (014-fix-diet-meal-render)
- TypeScript 5.x / Next.js 15 + React 18, TanStack Query v5, Tailwind CSS + shadcn/ui (all existing) (016-fix-save-day-plan-visibility)
- No schema change — backend endpoint unchanged (016-fix-save-day-plan-visibility)
- Python 3.13 + No new dependencies — stdlib `math` only (all existing) (015-fix-diet-caloric-accuracy)
- No schema change — correction is purely computational in the engine (015-fix-diet-caloric-accuracy)

- Python 3.12 (backend), TypeScript 5.x / Node.js 20.x (frontend) (001-inbody-scan-webapp)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.12 (backend), TypeScript 5.x / Node.js 20.x (frontend): Follow standard conventions

## Recent Changes
- 015-fix-diet-caloric-accuracy: Added Python 3.13 + No new dependencies — stdlib `math` only (all existing)
- 016-fix-save-day-plan-visibility: Added TypeScript 5.x / Next.js 15 + React 18, TanStack Query v5, Tailwind CSS + shadcn/ui (all existing)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
