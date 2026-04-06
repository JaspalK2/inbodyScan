# Implementation Plan: Food & Meal Tracker Enhancements

**Branch**: `002-food-meal-tracker` | **Date**: 2026-04-02 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/002-food-meal-tracker/spec.md`

---

## Summary

Extends the existing Food & Meals tab with: (1) a daily food log with date navigation, (2) a live macro pie chart aggregating all logged items against daily targets, (3) restaurant meal search via existing USDA Branded Foods data, (4) saved-meal shortcuts to log previously saved meals in one tap, and (5) editable AI diet/workout plans with live macro and quality score feedback. One new database table (`daily_food_log_entries`) and four new API endpoints are required; no new external dependencies or services.

---

## Technical Context

**Language/Version**: Python 3.13 (recommendation-service backend), TypeScript 5.x / Next.js 15 (frontend)  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 async, asyncpg, Pydantic v2, Recharts, TanStack Query v5 — all already present  
**Storage**: Supabase PostgreSQL (shared instance) — new `daily_food_log_entries` table  
**Testing**: pytest + pytest-asyncio (backend), Vitest + React Testing Library (frontend), Playwright (E2E)  
**Target Platform**: Web (Vercel + Supabase) and local dev (`uvicorn` + `next dev`)  
**Performance Goals**: Pie chart updates ≤ 1 second (client-side compute); food log fetch ≤ 300 ms  
**Constraints**: User-scoped data access on every query; no new external API keys; no new npm/pip packages  
**Scale/Scope**: Single-user health app; food log entries per user estimated at ~10–30/day; indefinite retention

---

## Constitution Check

*GATE: Must pass before implementation. Re-checked after design.*

| Principle | Gate | Status |
|-----------|------|--------|
| **I. Extensibility** | New `DailyFoodLog` service and model expose clean interfaces; `source` + `source_ref_id` fields allow future plan-adherence features without schema changes | ✅ Pass |
| **II. Algorithm Efficiency** | Macro aggregation is O(n) client-side sum; `(user_id, log_date)` composite index ensures O(log n) DB lookups; no unbounded full-table scans | ✅ Pass |
| **III. License Compliance** | No new dependencies; USDA data is public domain; Recharts MIT; all existing packages already audited | ✅ Pass |
| **IV. Mandatory Test Coverage** | Unit tests for log service, integration tests for all 4 new endpoints, E2E tests for all P1 acceptance scenarios (US1 + US2) required before merge | ✅ Required |
| **V. UI/UX Consistency** | Pie chart uses Recharts (already in use); new components use existing shadcn/ui primitives and glassmorphism CSS tokens; no ad-hoc colors | ✅ Pass |
| **Security** | All food log queries include `WHERE user_id = :current_user_id`; no PII in log entries; source_ref_id is a UUID reference only | ✅ Pass |

---

## Project Structure

### Documentation (this feature)

```text
specs/002-food-meal-tracker/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/
│   └── food-log-api.md  ← Phase 1 output
└── tasks.md             ← Phase 2 output (speckit.tasks)
```

### Source Code Changes

```text
services/recommendation-service/src/
├── models/
│   └── food_log.py                    ← NEW: DailyFoodLogEntry SQLAlchemy model
├── services/
│   └── food_log_service.py            ← NEW: create_entries, get_entries_for_date,
│                                              delete_entry, get_logged_dates
├── schemas/
│   └── recommendation.py              ← EXTEND: FoodLogEntryIn, FoodLogEntryOut,
│                                              FoodLogBatchCreate
└── routers/
    └── recommendations.py             ← EXTEND: 4 new food-log endpoints

frontend/app/(app)/recommendations/
└── page.tsx                           ← EXTEND: macro pie chart, date picker,
                                                   food log panel, restaurant labels,
                                                   saved shortcuts, "Log this meal" button,
                                                   live diet plan macro preview,
                                                   live workout quality score
frontend/lib/
└── api.ts                             ← EXTEND: createFoodLog, getFoodLog,
                                                   deleteFoodLogEntry, getFoodLogDates
```

---

## Phase 0: Research Findings

All research complete — see [research.md](research.md).

Key decisions:
1. **Restaurant data**: USDA Branded Foods already included in `food_search.py` — no change needed. Frontend labels result by `brand` field.
2. **Food log storage**: New `daily_food_log_entries` table in recommendation-service DB.
3. **Pie chart**: Client-side aggregation from log entries — no server-side aggregation endpoint needed.
4. **"Log this meal"**: Creates `daily_food_log_entry` records with `source=diet_plan`; doesn't auto-add.
5. **Live feedback**: Client-side computation for both macro previews and workout quality score.

---

## Phase 1: Design

### New Model: `DailyFoodLogEntry`

See [data-model.md](data-model.md) for full schema. SQLAlchemy model at `services/recommendation-service/src/models/food_log.py`:

- `id` UUID PK, `user_id`, `log_date` DATE, `fdc_id` nullable INT
- `food_name`, `brand` (nullable), `source` (manual/diet_plan/saved_meal)
- `source_ref_id` (nullable UUID), `quantity_g`, macro columns (all nullable FLOAT)
- Composite index `(user_id, log_date)`, single index `user_id`

### New Service: `FoodLogService`

`services/recommendation-service/src/services/food_log_service.py`:

- `create_log_entries(session, user_id, log_date, entries: list[dict]) -> list[DailyFoodLogEntry]`
- `get_entries_for_date(session, user_id, log_date) -> list[DailyFoodLogEntry]`
- `delete_entry(session, entry_id, user_id) -> bool`
- `get_logged_dates(session, user_id) -> list[date]`

### New Schemas

In `services/recommendation-service/src/schemas/recommendation.py`:

```python
class FoodLogEntryIn(BaseModel):
    fdc_id: int | None = None
    food_name: str
    brand: str | None = None
    source: str = "manual"          # manual | diet_plan | saved_meal
    source_ref_id: str | None = None
    quantity_g: float
    calories_kcal: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None

class FoodLogBatchCreate(BaseModel):
    log_date: date
    entries: list[FoodLogEntryIn]

class FoodLogEntryOut(FoodLogEntryIn):
    id: str
    user_id: str
    log_date: date
    created_at: datetime
```

### New API Endpoints

See [contracts/food-log-api.md](contracts/food-log-api.md) for full contracts.

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/recommendations/food-log` | Batch-create log entries |
| GET | `/api/recommendations/food-log?date=YYYY-MM-DD` | Fetch day's entries |
| DELETE | `/api/recommendations/food-log/{entry_id}` | Remove one entry |
| GET | `/api/recommendations/food-log/dates` | All dates with entries |

### Frontend Changes (page.tsx)

All changes are within the existing `frontend/app/(app)/recommendations/page.tsx` and `frontend/lib/api.ts`.

**Macro Pie Chart** (new component within page):
- Recharts `PieChart` with 3 slices: protein (purple), carbs (cyan), fat (amber)
- Each slice fills proportionally to `consumed/target`; slices beyond 100% shown in red overflow color
- If no macro targets: shows absolute gram totals with "Set up profile" prompt
- Date picker (`<input type="date">` or shadcn DatePicker) controls which date's log is shown

**Food Log Panel** (new section in Food & Meals tab):
- List of `DailyFoodLogEntry` records for selected date
- Each row: food name, brand label (if present), quantity, calories, delete button
- Running totals shown below list (matching pie chart values)

**Restaurant labeling** (enhancement to existing search):
- Search result cards show `brand` field as a badge if non-null (e.g., "McDonald's")
- No backend change — `brand` already returned from USDA search

**"Add to Today" on search results** (existing button enhancement):
- Calls `POST /api/recommendations/food-log` with `source=manual`
- On success, invalidates `["food-log", selectedDate]` query to refresh log + pie chart

**Saved meal shortcuts** (new section in Food & Meals tab):
- Query `GET /api/recommendations/meals` → list with "Add to Today" button per meal
- Button creates one log entry per meal item with `source=saved_meal`, `source_ref_id=meal.id`

**"Log this meal" on diet plan** (new button on each plan meal card in Diet tab):
- Parses meal macros from the current plan (edited or original)
- Calls `POST /api/recommendations/food-log` with `source=diet_plan`, `source_ref_id=rec.id`
- Invalidates food log query

**Live macro preview on diet plan edit** (enhancement to existing edit UI):
- As user changes quantity in edit mode, compute new macro values client-side (multiply per-gram values by new quantity)
- Display inline under the meal — updates at every keystroke (no debounce needed, pure math)

**Live workout quality score on workout plan edit** (enhancement to existing edit UI):
- Reuse the existing `scoreSplit` client-side logic (already imported) to rescore on every exercise change
- Debounce at 300ms (existing pattern uses 700ms — 300ms is snappier for text edits)

---

## Complexity Tracking

No constitution violations. No entries required.

---

## Post-Design Constitution Re-check

All principles confirmed clear:
- **I**: `source` + `source_ref_id` fields on log entries provide extension points for adherence tracking. New service is independently testable.
- **II**: All DB queries use indexed `(user_id, log_date)` lookup. Client-side aggregation is O(n), n bounded to ~30 entries/day.
- **III**: Zero new dependencies. USDA data public domain confirmed.
- **IV**: Test plan in tasks.md will cover unit (FoodLogService), integration (4 endpoints), E2E (US1 + US2 primary flows).
- **V**: Pie chart uses Recharts + existing design tokens. Date picker uses shadcn. No ad-hoc styles.
- **Security**: Every food log query scoped by `user_id`; no PII in log entries.
