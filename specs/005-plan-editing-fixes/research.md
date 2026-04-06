# Research: Plan Editing and Log Fixes (005)

## Decision 1: Exercise Library Data Source

**Decision**: Bundle `yuhonas/free-exercise-db` (CC0 public domain) as a static JSON asset in the recommendation-service; expose a single backend search endpoint that filters in-process.

**Rationale**: The constitution (Principle III) permits only MIT, Apache 2.0, BSD, ISC, CC0, and equivalent permissive licenses. All live-API candidates fail this gate:
- **ExerciseDB (RapidAPI)**: Proprietary — prohibited without legal review.
- **Wger (wger.de)**: CC BY-SA 4.0 ShareAlike — not on the permitted list; requires legal review.
- **API Ninjas**: Proprietary — prohibited without legal review.
- **yuhonas/free-exercise-db**: CC0 public domain — fully permitted, no attribution required.

The dataset (~800 exercises, ~500 KB JSON) is loaded once at service startup and filtered in-memory. Name search is O(n) over 800 items — well within the constitution's efficiency requirements (O(n²) or worse requires justification; this is O(n) and n is small and fixed).

**Alternatives considered**:
- Live API with backend proxy (all options fail license gate — see above).
- Frontend-only embed (viable, but keeping data server-side is consistent with the existing food-search pattern and allows future caching/expansion without frontend deploys).

**Source**: `https://raw.githubusercontent.com/yuhonas/free-exercise-db/main/dist/exercises.json`  
**License**: CC0 1.0 Universal (Public Domain Dedication) ✅

---

## Decision 2: Save Meal from Diet Plan — Data Mapping

**Decision**: Reuse the existing `POST /api/recommendations/meals` (CustomMeal) endpoint. Each meal's `foods: string[]` entries are stored as `CustomMealItem` rows with `food_name = the full string` (e.g. "200g chicken breast") and `quantity_g = 100` as a placeholder. Macro totals are stored at the meal level.

**Rationale**: The `CustomMeal` + `CustomMealItem` models already exist and the frontend `createMeal` API call is already wired. No new backend model, migration, or endpoint is needed. The `items_snapshot` in DayPlanEntry already follows the same pattern.

**Alternatives considered**: Parsing "200g chicken breast" into `quantity_g=200, food_name="chicken breast"` — rejected because the parsing is fragile (free-form AI text) and the exact quantity is already embedded in the human-readable string. The stored string is the canonical label.

---

## Decision 3: Saved Day Plans in Saved Meals Tab

**Decision**: Frontend-only change. Add a "Day Plans" section to the existing `FoodMealsTab` "saved" sub-tab by querying the existing `listDayPlans()` API call (which already exists). No new backend endpoint.

**Rationale**: `GET /api/recommendations/day-plans` already exists and returns all user day plans. The frontend simply wasn't rendering them in the Saved Meals view. Zero backend work required.

---

## Decision 4: Apply Day Plan to Food Log

**Decision**: In `DayPlannerTab`, add an "Apply saved plan" action. On confirmation, iterate `DayPlanEntry.items_snapshot` for each meal slot and batch-create food log entries via the existing `POST /api/recommendations/food-log/batch` (or the existing `createFoodLog` call). No new backend endpoint.

**Rationale**: `createFoodLog` already accepts a batch payload (`FoodLogBatchCreate` with `entries[]`). The `DayPlanEntry.items_snapshot` contains the food items and macro values needed. One `createFoodLog` call per meal slot (or a single batch across all slots) covers the requirement.

---

## Decision 5: Workout Exercise Picker UX

**Decision**: Inline typeahead — in edit mode, exercise name field becomes a text input with a debounced dropdown showing results from `GET /api/recommendations/exercises/search?q=`. Selecting a result writes the exercise name to the plan and triggers the existing live score recalculation (debounced `POST /workout/score-plan`).

**Rationale**: Matches the food-search pattern already established in `FoodMealsTab` and `DietDayRow`. Consistent with the constitution's UI/UX consistency principle (Principle V). Confirmed by clarification session (Option B).
