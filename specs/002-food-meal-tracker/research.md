# Research: Food & Meal Tracker Enhancements

**Feature**: 002-food-meal-tracker  
**Date**: 2026-04-02

---

## Decision 1: Restaurant Meal Data Source

**Decision**: Use USDA FoodData Central Branded Foods — already integrated.

**Rationale**: The existing `food_search.py` already queries `dataType=Foundation,SR Legacy,Branded`. The `Branded` data type includes hundreds of restaurant chain items (McDonald's, Chipotle, Starbucks, Subway, etc.) sourced from the USDA Branded Food Products Database. No new API key, no new dependency, no license concerns — USDA data is public domain. Simply ensuring `Branded` is included in `dataType` (already the case) surfaces restaurant items in existing search results. Items from restaurant chains carry a `brandOwner` field that already maps to `FoodResult.brand`, which will serve as the "source label" in the UI.

**Alternatives considered**:
- **Nutritionix API**: Best restaurant coverage but proprietary license prohibits caching data — eliminates it per constitution Principle III.
- **CalorieNinjas**: Proprietary, rate-limited (10k/month free). Not suitable for production.
- **Open Food Facts**: CC0/ODbL permissive. Stronger on packaged goods than restaurant items; useful as a supplement but not needed given USDA coverage.

**Implementation note**: No backend changes required. Frontend labeling logic should check `brand` field on `FoodResult` — if present, display it as the restaurant/brand label. If absent, label as "Generic ingredient."

---

## Decision 2: Daily Food Log Storage

**Decision**: New `daily_food_log_entries` table in the existing Supabase PostgreSQL instance (recommendation-service DB).

**Rationale**: Extends the existing data model without introducing a new service or storage system. The recommendation-service already owns all food/meal data (`custom_meals`, `day_plans`, `nutritional_foods`). Adding the food log here maintains co-location and avoids cross-service joins. Indefinite retention (per clarification) means no TTL or cleanup logic needed — straightforward append-only log.

**Alternatives considered**:
- **Embed in day_plans**: Rejected — day plans are forward-looking meal schedules; the food log is a record of what was actually consumed. Merging them would conflate planning and logging.
- **Separate microservice**: Rejected — over-engineered for this scope; no isolation benefit.

---

## Decision 3: Macro Pie Chart Aggregation

**Decision**: Client-side aggregation from daily food log entries fetched via a single `GET /api/recommendations/food-log?date=YYYY-MM-DD` endpoint. No server-side chart state stored.

**Rationale**: Macro totals are simple sums over the day's log entries — O(n) where n = entries/day, which is small (typically 3–20). Computing this client-side after fetching the log avoids a separate aggregation endpoint and keeps the server stateless. The Recharts PieChart already used in the app renders the computed totals directly.

**Alternatives considered**:
- **Server-side aggregation endpoint**: Unnecessary complexity for simple sums. Would create a second round-trip or require denormalization.
- **Store totals on a summary table**: Premature optimization for this scale; adds update logic complexity on every log entry change.

---

## Decision 4: AI Plan "Log This Meal" Integration

**Decision**: Each meal in a generated diet plan gets a "Log this meal" button that creates a `daily_food_log_entry` record tagged with `source=diet_plan` and the `diet_recommendation_id`. This lets the UI distinguish plan-sourced entries from manually searched entries if needed for future features, while both contribute equally to the macro pie chart.

**Rationale**: Per clarification Answer B, plan meals only count when explicitly logged. Tagging the source enables auditing and future "plan adherence" reporting without adding complexity now.

---

## Decision 5: Editable Plan Live Feedback

**Decision**: Both diet plan editing (macro preview) and workout plan editing (quality score) are computed entirely client-side using the same logic already present in the frontend. No new backend endpoint is needed for the live preview — only the final "save" action calls the existing `PATCH /api/recommendations/diet/{id}` or `PATCH /api/recommendations/workout/{id}`.

**Rationale**: The workout scorer already runs client-side for the split builder (debounced 700ms). The macro calculator runs client-side for the custom meal builder. Reusing the same pattern avoids a real-time backend call on every keystroke and keeps latency under 100ms for live feedback.

---

## License Audit (Principle III)

| Dependency / Data Source | License | Verdict |
|--------------------------|---------|---------|
| USDA FoodData Central API | Public Domain (U.S. Gov) | ✅ Permitted |
| Recharts (already in use) | MIT | ✅ Permitted |
| SQLAlchemy (already in use) | MIT | ✅ Permitted |
| asyncpg (already in use) | Apache 2.0 | ✅ Permitted |

No new dependencies required for this feature.
