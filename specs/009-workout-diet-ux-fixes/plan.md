# Implementation Plan: Workout & Diet UX Fixes

**Branch**: `009-workout-diet-ux-fixes` | **Date**: 2026-04-05 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/009-workout-diet-ux-fixes/spec.md`

## Summary

Fix seven compounding issues across the recommendations page: token expiry blocking the page, 4-week workout plans being condensed to 1 week with a ≥90 score floor, real-time client-side score delta display (vs. original), Tailwind dynamic-class bug breaking macro bars, condensed collapsible day planner cards with simplified labels, removal of individual meal save from day planner, and a compact expandable meal selector surfacing both saved days and saved meals.

All changes are isolated to three locations: the recommendation-service prompt/scorer (backend), the auth API client (frontend), and the single large recommendations page component (frontend).

## Technical Context

**Language/Version**: Python 3.13 (backend services), TypeScript 5.x / Next.js 15 (frontend)  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 async, Pydantic v2 (backend); TanStack Query v5, React 18, Tailwind CSS (frontend)  
**Storage**: Supabase PostgreSQL — no schema changes required  
**Testing**: pytest (backend), Vitest + React Testing Library (frontend)  
**Target Platform**: Web (server + browser)  
**Project Type**: Web application (microservices backend + Next.js frontend)  
**Performance Goals**: Score delta feedback ≤500 ms (client-side, trivially met); macro bar update ≤200 ms (CSS fix, immediate)  
**Constraints**: Client-side scoring must use dimension weights identical to `workout_scorer.py`; legacy 4-week plan JSONs must still render (backward-compat fallback)  
**Scale/Scope**: Single-user recommendations page; no pagination required for this feature

## Constitution Check

| Principle | Gate | Status |
|-----------|------|--------|
| I. Extensibility | Scoring dimension weights extracted to a shared constant; meal selector is a new composable component; token interceptor is generic (not page-specific) | ✅ PASS |
| II. Algorithm Efficiency | Client-side scorer iterates over exercises once per edit — O(n) where n = exercises in plan. No O(n²) paths introduced. | ✅ PASS |
| III. License Compliance | No new dependencies required. All existing deps (React, TanStack Query, Tailwind) are MIT/Apache 2.0. | ✅ PASS |
| IV. Mandatory Test Coverage | Unit tests for scorer weight constant, macro bar color map, token interceptor retry logic. E2E tests for P1 stories (token refresh, workout 1-week, macro bars). | ✅ REQUIRED — tasks must include test work |
| V. UI/UX Consistency | MacroBar fix uses design system colors via explicit map; day planner cards use existing card/border tokens; meal selector uses existing Input/Popover primitives. | ✅ PASS |
| Security & Data Privacy | Token refresh does not log tokens; no PII change in LLM prompt; user-scoped queries unchanged. | ✅ PASS |

## Project Structure

### Documentation (this feature)

```text
specs/009-workout-diet-ux-fixes/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/
│   └── workout-plan-api.md
└── tasks.md             ← Phase 2 output (/speckit.tasks)
```

### Source Code (affected files)

```text
services/recommendation-service/src/
├── services/
│   ├── prompt_builder.py          ← change "4-week" → single week prompt
│   └── recommendation_service.py  ← add score-floor retry logic
├── routers/
│   └── recommendations.py         ← no change expected

frontend/
├── lib/
│   └── api.ts                     ← add 401 interceptor + refresh retry
├── app/(app)/recommendations/
│   └── page.tsx                   ← main change surface (7 fixes):
│       • MacroBar: fix dynamic Tailwind class → explicit color map
│       • WorkoutPlanCard: 1-week rendering + originalScore state
│       • Score delta indicator (vs original, decimal precision)
│       • DayPlannerTab: collapsible day cards + simplified meal labels
│       • Remove saveMealMutation + "Save Meal" button from DietDayRow
│       • Replace <select> with compact MealSelectorWidget component
└── components/
    └── MealSelectorWidget.tsx     ← new compact expandable meal picker
```

**Structure Decision**: Web application (Option 2). Backend changes are in recommendation-service only; frontend changes are concentrated in `recommendations/page.tsx` with one new component.

## Complexity Tracking

No constitution violations. No complexity justification required.

---

## Phase 0: Research Summary

Research complete — see [research.md](research.md). All NEEDS CLARIFICATION items resolved:

| Unknown | Resolution |
|---------|-----------|
| Score recalculation source | Client-side using dimension weights from `workout_scorer.py` |
| Score delta reference point | Cumulative vs. original AI-generated score |
| Macro bar bug root cause | Tailwind dynamic class purge (`bg-${color}-500`) |
| 4-week structure location | `prompt_builder.py` line 76 + frontend `plan.weeks` renderer |
| Token refresh mechanism | `tryRefresh()` already exists; needs wiring into `api.ts` request function |

---

## Phase 1: Design

### Fix 1 — Token Expiry Interceptor (`frontend/lib/api.ts`)

**Change**: Wrap the `request<T>()` function to catch 401 responses, call `tryRefresh()` once, update the stored token, then retry the original request. On second 401, call `clearAccessToken()` and redirect to `/login`.

**Interface**:
```typescript
// Existing signature — unchanged
async function request<T>(path: string, options?: RequestInit): Promise<T>
```

The interceptor is internal to `api.ts`; no public interface change.

---

### Fix 2 — Single-Week Workout Plan (Backend)

**`prompt_builder.py`**: Replace "create a structured 4-week progressive workout program" with "create a single-week, high-quality, well-balanced workout program". Update JSON schema instruction to return `{ days: [...] }` (flat, no `weeks` wrapper).

**`recommendation_service.py`**: After generating the plan and computing the score, add validation:
```python
if score < 90:
    # retry with strengthened prompt (max 2 retries)
    # if still < 90 after retries, clamp to 90 and log warning
```

---

### Fix 3 — Frontend: 1-Week Rendering + Score Delta

**`recommendations/page.tsx`**:
- Change button label: "Generate 4-Week Workout Plan" → "Generate Weekly Workout Plan"
- Add `originalScore: number` to workout plan state, set once when plan first loads
- Replace `plan.weeks[0].days` rendering with `plan.days` (with legacy fallback: `plan.days ?? plan.weeks?.[0]?.days`)
- Score delta indicator: `(currentScore - originalScore).toFixed(1)` with `+`/`−` sign and color (green = positive, red = negative, gray = zero)

---

### Fix 4 — MacroBar Color Fix (`recommendations/page.tsx` ~line 56)

**Before**:
```typescript
const barColor = ... `bg-${color}-500`;
// <div className={`... ${barColor}`} />
```

**After**:
```typescript
const COLOR_MAP: Record<string, string> = {
  cyan: "#06b6d4", green: "#22c55e", amber: "#f59e0b",
  purple: "#a855f7", red: "#ef4444",
};
// <div style={{ width: `${Math.min(pct, 100)}%`, backgroundColor: COLOR_MAP[color] ?? "#6b7280" }} />
```

---

### Fix 5 — Condensed Day Planner Cards (`recommendations/page.tsx` DayPlannerTab)

**Layout change**: Wrap each day's render block in a collapsible card:
- Collapsed state: shows day label (e.g., "Monday") + total calories summary
- Expanded state: shows all four meal slots
- Default state: all days collapsed

**Label change**: `MEAL_SLOTS.map(slot => ...)` renders `slot.charAt(0).toUpperCase() + slot.slice(1)` (e.g., "Breakfast") — remove any "Day Planner —" prefix from display labels.

---

### Fix 6 — Remove Individual Meal Save (`recommendations/page.tsx` DietDayRow)

**Change**: Delete `saveMealMutation` definition and the "Save Meal" button (line 716). No data model change — the mutation endpoint remains on the backend for the whole-day save flow.

---

### Fix 7 — Compact Meal Selector (`frontend/components/MealSelectorWidget.tsx`)

**New component**: `MealSelectorWidget` — a small collapsed trigger (shows selected meal name or placeholder) that opens a popover/dropdown panel with two sections:

```
┌─────────────────────────────┐
│ [Selected meal name ▾]       │  ← collapsed (single line)
└─────────────────────────────┘

On click:
┌─────────────────────────────┐
│ Saved Days                  │
│   • Monday Plan (Apr 3)     │
│   • Bulk Day                │
│ ─────────────────────────── │
│ Saved Meals                 │
│   • Oat Bowl                │
│   • Chicken & Rice          │
│ ─────────────────────────── │
│ (empty state if none)       │
└─────────────────────────────┘
```

**Props**:
```typescript
interface MealSelectorWidgetProps {
  value: string | null;
  onChange: (id: string | null) => void;
  savedMeals: SavedMeal[];
  savedDays: SavedDayPlan[];
}
```

Uses existing Popover/Command primitives from the shared component library (no new dependencies).
