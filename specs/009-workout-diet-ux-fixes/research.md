# Research: Workout & Diet UX Fixes (009)

## 1. Workout Score Generation

**Decision**: Score enforcement (90-point floor) lives in the backend `workout_scorer.py`. Post-generation edit scoring is replicated client-side using the same five-dimension rubric.

**Findings**:
- `services/recommendation-service/src/services/workout_scorer.py` — full scoring engine
- Five dimensions: Coverage (25 pts), Volume (30 pts), Balance (20 pts), Cardio (15 pts), Frequency (10 pts)
- Score is computed dynamically on-demand; the `WorkoutRecommendation` model stores the plan JSON but not the score
- Two scoring endpoints exist: `/api/recommendations/splits/score` (manual splits) and `/api/recommendations/workout/score-plan` (generated plans)
- Frontend already has live-score debounce logic at lines 1675–1685 of `recommendations/page.tsx`

**Rationale**: The backend scorer already implements the full rubric. For client-side edit scoring, we expose the same dimension weights as a JS constant and compute locally — no new network call per edit.

**Alternatives considered**:
- Call backend on every keystroke: rejected — adds latency, contradicts clarification Q1 answer (Option A).
- Debounced backend call: rejected — same latency concern; local rule set is sufficient for feedback.

---

## 2. Workout Plan Structure (4-Week → 1-Week)

**Decision**: Change prompt to generate a single week; update frontend rendering to not map over `weeks` array.

**Findings**:
- `services/recommendation-service/src/services/prompt_builder.py` line 76 — hardcoded "4-week progressive workout program"
- `frontend/app/(app)/recommendations/page.tsx` line 1534 — button text "Generate 4-Week Workout Plan"
- Lines 1750–1824 — renders `plan.weeks` array; each week maps days with exercises
- JSON schema returned by LLM has shape: `{ weeks: [{ week_number, days: [{ day, exercises }] }] }`

**Rationale**: Changing the prompt to request a single week and renaming the schema from `weeks[0]` to a flat `days[]` is the minimal change. Frontend rendering drops the outer `weeks` map.

**Alternatives considered**:
- Keep multi-week structure but only show week 1: rejected — wastes LLM tokens and storage; misleads users.

---

## 3. Score Floor Enforcement (≥ 90)

**Decision**: Add post-generation validation in the recommendation service. If score < 90, retry generation up to 2 times, then clamp to 90 as last resort.

**Findings**:
- `workout_scorer.py` `score_workout_split()` returns a `WorkoutScore` dataclass
- Current prompt does not specify score targets to the LLM
- Adding "design a high-quality, well-balanced program" language to the prompt and validating post-generation score is the cleanest path

**Rationale**: Retry-with-improved-prompt is safer than clamping; clamping is a safety net only.

---

## 4. Score Delta Display (vs. Original)

**Decision**: Store the original generated score at load time; all subsequent deltas shown as `current − original` with sign.

**Findings**:
- Score is recomputed on the frontend from the plan JSON (lines 1675–1685)
- Original score not currently stored in state; need to capture it on first load and freeze it
- Delta indicator: `(currentScore − originalScore).toFixed(1) + " pts from original"`

**Rationale**: Cumulative drift (vs. original) gives more meaningful signal than per-keystroke delta (clarification Q2 answer: Option B).

---

## 5. Token Expiry / Refresh

**Decision**: Add a 401 interceptor in `frontend/lib/api.ts`. On first 401, call `auth.refresh()`, retry the original request once with the new token. On second 401, redirect to login.

**Findings**:
- `frontend/lib/api.ts` lines 19–31 — `request<T>()` function, no 401 handling
- `frontend/lib/auth-context.tsx` lines 36–47 — `tryRefresh()` already calls `auth.refresh()` on app boot
- Access token stored as module-level variable `_accessToken`; refresh token stored in the auth service session (httpOnly cookie or equivalent)
- No existing request retry logic

**Rationale**: Interceptor pattern is the standard approach; `tryRefresh()` already exists so reuse is straightforward.

---

## 6. Macro Bars Bug

**Decision**: Replace the dynamic Tailwind class template literal with an explicit color map or inline `background-color` style.

**Root Cause**: `bg-${color}-500` in `MacroBar()` at `recommendations/page.tsx` line 63 — Tailwind cannot statically analyze this template literal and purges the class at build time. The bar DOM element exists but has no background color, so it appears invisible/static.

**Fix**: Use a `colorMap` object (`{ cyan: "#06b6d4", green: "#22c55e", ... }`) and apply via `style={{ width: ..., backgroundColor: colorMap[color] }}`.

**Alternatives considered**:
- Safelist in `tailwind.config`: works but couples config to runtime data — rejected.
- Switch to static class names only: requires color logic in calling code — more invasive.

---

## 7. Day Planner Layout & Labels

**Decision**: Wrap each day in a collapsible `<details>`/card component; change meal slot labels from `"Day Planner — breakfast"` to simply `"Breakfast"`.

**Findings**:
- `DayPlannerTab()` at lines 1137–1282
- Label format at line 647: `"Day Planner — ${slot}"` — used in save-day mutation
- `MEAL_SLOTS = ["breakfast", "lunch", "dinner", "snack"]` at line 1135
- Slot labels in the UI are currently the raw slot string (lowercase) — need capitalization + removal of day prefix

**Rationale**: Minimal DOM change — wrap existing day rendering in a card container; label fix is a one-line string change.

---

## 8. Remove Individual Meal Save / Compact Meal Selector

**Decision**: Remove `saveMealMutation` and its "Save Meal" button from the diet tab day rows (line 716). Replace the native `<select>` in day planner (lines 1247–1254) with a custom compact combobox showing two sections: "Saved Days" and "Saved Meals".

**Findings**:
- Individual meal save button at line 716 in `DietDayRow` component
- Native `<select>` at lines 1247–1254 only surfaces `savedMeals`; does not show saved days
- `savedMeals` query uses `queryKey: ["custom-meals"]`; need to also fetch `savedDays` from the day plans endpoint

**Rationale**: Removing the save button is a single-line deletion. The new compact selector is a new small component using existing data already available via TanStack Query.
