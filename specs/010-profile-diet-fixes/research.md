# Research: Profile & Diet Fixes (010)

All decisions were resolved during clarification (2026-04-05). No external research required — all answers come from direct codebase inspection.

---

## Decision 1: Profile API Existence

**Decision**: All profile/goal/restriction APIs exist in user-service; no new endpoints needed.  
**Rationale**: Inspected `services/user-service/src/routers/users.py` — full CRUD exists for profile, health goal, and dietary restrictions. Frontend `profile/page.tsx` already calls all of them via TanStack Query.  
**Root Cause of Bug**: Silent failures — no error state displayed on the profile page. If the user-service returns an error (DB table missing, network issue), the form silently fails with no user feedback.  
**Alternatives considered**: Building new endpoints (rejected — they already exist).

---

## Decision 2: Diet Macro Accuracy Fix Approach

**Decision**: Server-side retry loop (up to 3 attempts) in `recommendation_service.py` — validate each day's `day_totals` after generation; retry if any macro is >10% off target.  
**Rationale**: Prompt already says "within ±5%" and the LLM ignores it. Prompt strengthening alone has already failed. Retry loop is proven effective (used for workout score floor in feature 009). Post-processing (scaling quantities) would change the LLM's food choices and may produce nutritionally incoherent plans.  
**Validator logic**: For each day, check `abs(day_totals.calories - target_calories) / target_calories > 0.10` (and same for protein_g, carbs_g, fat_g). If any day fails, retry the full generation.  
**Alternatives considered**: Prompt strengthening only (rejected — already tried), post-processing quantity scaling (rejected — nutritionally unsafe).

---

## Decision 3: activity_level Field

**Decision**: Add `activity_level: Mapped[str | None]` to `UserProfile` SQLAlchemy model; add to `ProfileOut` and `ProfileUpdate` Pydantic schemas; add `<select>` to profile page UI; pass saved value to `calculateMacros` and `generateDiet` calls in `FoodMealsTab`.  
**Rationale**: Activity level is a TDEE multiplier (1.2–1.9×). Without it, macro targets can be off by 500–800 kcal/day. The `calculateMacros` API already accepts `activity_level?: string` but it's hardcoded to "moderate" in the frontend. No DB migration needed — Supabase uses `create_all` on startup.  
**Activity level options** (matching `calculateMacros` API): `sedentary`, `lightly_active`, `moderately_active`, `very_active`, `extra_active`.  
**Alternatives considered**: Keep hardcoded "moderate" (rejected — too inaccurate for the app's purpose).

---

## Decision 4: Saved Days in My Saved Meals

**Decision**: Add `useQuery(["day-plans"], recommendations.listDayPlans)` to `FoodMealsTab`; render a "Saved Day Plans" section above the "Saved Meals" section. Day Planner tab retains its existing saved day plans list.  
**Rationale**: `FoodMealsTab` currently only queries `custom-meals`. `listDayPlans` already exists and is used by `DayPlannerTab`. Reusing the same query key means React Query caches the result — no extra network call if both tabs are mounted.  
**Alternatives considered**: Consolidate to one location only (rejected — Day Planner needs its list for the "Apply" action).

---

## Decision 5: Profile Nav Relocation

**Decision**: Remove `{ href: "/profile", label: "Profile", icon: User }` from `navItems` array in `nav.tsx`; add a Profile `<Link>` directly above the Sign Out `<Button>` in the bottom section of the sidebar.  
**Rationale**: The sidebar already has a bottom section with the Sign Out button. Profile is an account-level control, not a content tab — it belongs with account controls.  
**No new components needed** — same `Link` + `div` pattern as existing nav items.
