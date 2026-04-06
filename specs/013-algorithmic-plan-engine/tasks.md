# Tasks: Algorithmic Plan Engine (013)

**Branch**: `013-algorithmic-plan-engine`  
**Input**: `specs/013-algorithmic-plan-engine/` — plan.md, spec.md, data-model.md, research.md, contracts/, quickstart.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: US1=Workout engine, US2=Diet engine, US3=Plan explanation

---

## Phase 1: Setup

- [X] T001 Add `apscheduler==3.11.2` to `services/recommendation-service/requirements.txt` and install it in the venv: `cd services/recommendation-service && .venv/bin/pip install apscheduler==3.11.2`

---

## Phase 2: Foundational (blocking all user stories)

**Purpose**: Food database seed + shared data loading — both diet and workout engines depend on this.

- [X] T002 Create `services/recommendation-service/src/services/food_seeder.py` — async function `seed_food_database(usda_api_key: str, output_path: Path) -> int` that: (1) fetches Foundation Foods from `GET https://api.nal.usda.gov/fdc/v1/foods/list?dataType=Foundation&pageSize=200&api_key={key}`, (2) extracts calories/protein/carbs/fat/fiber using the nutrient ID map already defined in `food_search.py` (`_NUTRIENT_MAP` with IDs 1008/1003/1005/1004/1079), (3) tags each food with restriction flags (vegetarian/vegan/gluten_free/dairy_free/halal/kosher) based on food category string, (4) assigns `meal_slots` (`["breakfast","lunch","dinner","snack"]` or subset) based on category, (5) writes the result to `output_path` as JSON matching the schema in `data-model.md`, (6) returns the count of foods written. Also expose `async def refresh_food_db_job()` that calls `seed_food_database` using env vars and the default `src/data/foods.json` path.

- [X] T003 Run the seed script once to populate `services/recommendation-service/src/data/foods.json`: `cd services/recommendation-service && set -a && source ../../.env && set +a && .venv/bin/python -c "import asyncio, os, pathlib; from src.services.food_seeder import seed_food_database; n=asyncio.run(seed_food_database(os.environ['USDA_API_KEY'], pathlib.Path('src/data/foods.json'))); print(f'Seeded {n} foods')"`. Verify the file exists and contains >50 entries.

- [X] T004 Create `services/recommendation-service/src/services/plan_explainer.py` — function `build_workout_explanation(metrics: dict, goal_type: str) -> str` that returns a 2–4 sentence string using template branches: body_fat_percentage thresholds (<15% lean, 15–25% normal, 25–35% elevated, >35% high) × goal_type to produce contextualised text referencing actual metric values. Also `build_diet_explanation(macro_targets, goal_type: str) -> str` for diet plans.

- [X] T005 [P] Write unit tests for `food_seeder.py` in `services/recommendation-service/tests/test_food_seeder.py`: (a) mock the USDA HTTP call and verify correct nutrient extraction; (b) verify restriction tags are applied correctly (poultry category → vegetarian=False, vegan=False); (c) verify the output JSON matches the schema; (d) verify `seed_food_database` returns the correct count.

- [X] T006 [P] Write unit tests for `plan_explainer.py` in `services/recommendation-service/tests/test_plan_explainer.py`: (a) user with BF=32% + lose_fat goal → explanation mentions body fat and cardio; (b) user with BF=12% + muscle_gain goal → explanation mentions lean base and progressive overload; (c) missing BF metric → explanation still returns a valid string (no KeyError).

**Checkpoint**: `foods.json` exists with >50 foods; `plan_explainer.py` unit tests pass.

---

## Phase 3: User Story 1 — Algorithmic Workout Plan Generation (P1) 🎯 MVP

**Goal**: Replace LLM workout generation with deterministic engine; frontend unchanged.

**Independent Test**: POST `/api/recommendations/workout/generate` with no LLM keys configured → HTTP 201, 7-day plan, all muscle groups covered, `plan_explanation` populated.

### Tests for User Story 1

- [X] T007 [P] [US1] Write unit tests for `workout_engine.py` in `services/recommendation-service/tests/test_workout_engine.py`: (a) muscle_gain goal → plan has exactly 5 training days + 2 rest days; (b) all required muscle groups (chest, back, shoulders, biceps, triceps, quads, hamstrings, glutes, calves, core) appear across training days; (c) at least one compound lift (squat/deadlift/bench/row/OHP) per plan; (d) lose_fat goal → at least 2 cardio days; (e) plan passes `score_workout_split()` with score ≥ 70; (f) missing body_fat_percentage in metrics → uses default (20%) and still generates a valid plan.

- [X] T008 [P] [US1] Write integration test in `services/recommendation-service/tests/integration/test_generate_algorithmic.py`: POST `/api/recommendations/workout/generate` with valid body and auth headers → HTTP 201, `structured_plan` is valid JSON, contains `days` array of length 7.

### Implementation for User Story 1

- [X] T009 [US1] Create `services/recommendation-service/src/services/workout_engine.py` with:
  - `SPLIT_TEMPLATES` dict mapping goal_type → list of 7 day descriptors, e.g. `{"muscle_gain": [{"focus":"Push – Chest & Triceps","muscle_groups":["chest","triceps","shoulders"],"is_rest":False}, ...]}` covering PPL+Upper/Lower for muscle goals, Full Body+Cardio for fat loss, etc.
  - `_load_exercises() -> list[dict]` — reads `src/data/exercises.json` once at module load
  - `_select_exercises(muscle_group: str, goal_type: str, count: int) -> list[dict]` — filters exercises.json by `primaryMuscles` containing the muscle group and `category == "strength"`, prioritises compound movements, returns `count` exercises
  - `_sets_reps_rest(goal_type: str) -> tuple[int, str, int]` — returns `(sets, reps_str, rest_seconds)` per goal: muscle_gain→(4,"8-12",90), lose_fat→(3,"12-15",60), general_health→(3,"10-15",75), improve_endurance→(2,"15-20",45)
  - `generate_workout_plan(metrics: dict, goal_type: str) -> dict` — assembles the full plan dict matching the JSON schema in `contracts/recommendation-api.md`, calls `plan_explainer.build_workout_explanation()`, validates with `score_workout_split()`, returns the dict

- [X] T010 [US1] Modify `services/recommendation-service/src/services/recommendation_service.py` function `generate_workout_recommendation` (lines ~116–157): remove `llm = get_llm_client()`, `prompt_builder` import usage, and the retry loop. Replace with: `from .workout_engine import generate_workout_plan` then `structured = generate_workout_plan(metrics, goal_type)`. Set `raw_response = json.dumps(structured)` and `structured_json = json.dumps(structured)`. Keep the rest of the function (DB write) unchanged.

- [X] T011 [US1] Verify `test_workout_engine.py` and `test_generate_algorithmic.py` (workout) pass: `cd services/recommendation-service && .venv/bin/pytest tests/test_workout_engine.py tests/integration/test_generate_algorithmic.py -v -k workout`

**Checkpoint**: Workout generation works end-to-end with zero LLM calls. Run quickstart Scenario 1.

---

## Phase 4: User Story 2 — Algorithmic Diet Plan Generation (P1)

**Goal**: Replace LLM diet generation with deterministic engine; macro targets hit within ±5% per day.

**Independent Test**: POST `/api/recommendations/diet/generate` → HTTP 201, each day's meal macros sum to within ±5% of `daily_targets`, `day_totals` matches the sum exactly.

### Tests for User Story 2

- [X] T012 [P] [US2] Write unit tests for `diet_engine.py` in `services/recommendation-service/tests/test_diet_engine.py`: (a) for a 2200 kcal target, each day's meals sum within ±5% of 2200; (b) `day_totals` equals the sum of individual meal macros (use the `compute_day_totals` function from `test_diet_macro_display.py` as reference); (c) vegetarian restriction → no meal contains meat/poultry/fish foods; (d) plan has exactly 7 days × 4 meals = 28 meal slots; (e) each meal slot has `foods` list with at least 2 items and non-zero macros.

- [X] T013 [P] [US2] Add diet integration test to `services/recommendation-service/tests/integration/test_generate_algorithmic.py`: POST `/api/recommendations/diet/generate` with valid body → HTTP 201, `structured_plan.days` length == 7, day 1 `day_totals.calories` within ±5% of `daily_targets.calories`.

### Implementation for User Story 2

- [X] T014 [US2] Create `services/recommendation-service/src/services/diet_engine.py` with:
  - `MEAL_SLOT_RATIOS = {"breakfast": 0.25, "lunch": 0.35, "dinner": 0.30, "snack": 0.10}`
  - `_load_foods() -> list[dict]` — reads `src/data/foods.json`; raises clear error if file missing
  - `_filter_foods(foods: list, slot: str, restrictions: list[str]) -> list[dict]` — filters by `meal_slots` containing slot and all restriction flags set to True
  - `_select_and_scale(slot: str, target_cals: float, target_protein: float, target_carbs: float, target_fat: float, foods: list) -> MealSlot` — picks a protein food + carb food + vegetable, scales portions in grams using `portion_g = target / (food.macro_per_100g / 100)`, computes exact meal macros, returns a `MealSlot` dataclass with `foods` list of strings like "150g Chicken Breast"
  - `generate_diet_plan(macro_targets: MacroTargets, restrictions: list[str], goal_type: str) -> dict` — builds 7 days × 4 meals, computes `day_totals` by summing meal macros (never estimated), returns dict matching the JSON schema in `contracts/recommendation-api.md` including `macro_targets` key

- [X] T015 [US2] Modify `services/recommendation-service/src/services/recommendation_service.py` function `generate_diet_recommendation` (lines ~38–94): remove `llm = get_llm_client()`, the retry loop, and `best_structured`/`best_raw` tracking. Replace with: `from .diet_engine import generate_diet_plan` then `structured = generate_diet_plan(macro_targets, restrictions, goal_type)`. Set `raw_response = json.dumps(structured)` and `structured_json = json.dumps(structured)`. Keep `structured["macro_targets"] = asdict(macro_targets)` line and the DB write unchanged.

- [X] T016 [US2] Verify `test_diet_engine.py` and `test_generate_algorithmic.py` (diet) pass: `cd services/recommendation-service && .venv/bin/pytest tests/test_diet_engine.py tests/integration/test_generate_algorithmic.py -v -k diet`

**Checkpoint**: Diet generation works end-to-end. Run quickstart Scenarios 2 and 3.

---

## Phase 5: User Story 3 — Plan Explanation Without LLM (P2)

**Goal**: Both generated plans include a meaningful explanation referencing actual body composition metrics, generated from templates (no LLM).

**Independent Test**: Generate workout plan for user with BF=28% + lose_fat goal → `plan_explanation` mentions body fat and cardio emphasis.

### Tests for User Story 3

*(Tests already created in T006 — no additional test tasks needed)*

### Implementation for User Story 3

- [X] T017 [US3] Verify that `workout_engine.generate_workout_plan()` calls `plan_explainer.build_workout_explanation(metrics, goal_type)` and stores the result in `structured["plan_explanation"]`. Verify `diet_engine.generate_diet_plan()` stores `plan_explainer.build_diet_explanation(macro_targets, goal_type)` in `structured["summary"]`. Run `tests/test_plan_explainer.py` to confirm.

**Checkpoint**: All 3 user stories functional. Run quickstart Scenario 5 (high BF → cardio emphasis in explanation).

---

## Phase 6: Weekly Food DB Refresh (APScheduler)

**Goal**: Food database refreshes weekly automatically; manual trigger endpoint available.

- [X] T018 Modify `services/recommendation-service/src/main.py` to: (1) import `AsyncIOScheduler` from `apscheduler.schedulers.asyncio`; (2) add a `lifespan` async context manager that starts the scheduler with a weekly cron job (`day_of_week="sun", hour=2`) calling `refresh_food_db_job` from `food_seeder.py`; (3) on startup, check if `src/data/foods.json` is missing or older than 8 days — if so, run `refresh_food_db_job()` immediately before arming the scheduler; (4) update `app = FastAPI(...)` to `app = FastAPI(lifespan=lifespan, ...)`.

- [X] T019 Add two endpoints to `services/recommendation-service/src/routers/recommendations.py`: (1) `POST /api/recommendations/food-db/refresh` — calls `refresh_food_db_job()`, returns `{"foods_fetched": n, "last_updated": "..."}` per the contract in `contracts/recommendation-api.md`; (2) `GET /api/recommendations/food-db/status` — reads `foods.json`, returns `{"food_count": n, "last_updated": "...", "refresh_interval_days": 7}`.

- [ ] T020 [P] Write unit test in `services/recommendation-service/tests/test_food_seeder.py` (add to existing file): mock the POST to `/food-db/refresh` and verify it returns 200 with `foods_fetched` field; mock the GET to `/food-db/status` and verify it returns `food_count` > 0.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T021 Remove the `from ..llm.gemini_client import get_llm_client` import and `asyncio` import (if no longer used) from `services/recommendation-service/src/services/recommendation_service.py`. Verify no other file breaks by running: `cd services/recommendation-service && .venv/bin/python -c "from src.services.recommendation_service import generate_diet_recommendation, generate_workout_recommendation; print('OK')"`.

- [X] T022 Run the full test suite and verify all existing tests still pass: `cd services/recommendation-service && .venv/bin/pytest tests/ -v --ignore=tests/integration/test_edit_workout.py -x 2>&1 | tail -20`. Expected: all unit tests + new tests pass; integration tests that depend on real LLM may be skipped or updated.

- [X] T023 [P] Update `specs/013-algorithmic-plan-engine/tasks.md` marking all completed tasks as [X].

---

## Dependencies & Execution Order

- **T001**: First — installs new dependency
- **T002–T006**: Foundational — T002 and T004 can run in parallel [P]; T003 depends on T002; T005 depends on T002; T006 depends on T004
- **T007–T011**: US1 workout — T007 and T008 [P] can run alongside T009; T010 depends on T009; T011 validates
- **T012–T016**: US2 diet — T012 and T013 [P] can run alongside T014; T015 depends on T014; T016 validates
- **T017**: US3 — depends on T009 (workout_engine) and T014 (diet_engine) being complete
- **T018–T020**: Scheduler — T018 and T019 can be done in parallel; T020 after T019
- **T021–T023**: Polish — after all story phases complete

---

## Parallel Opportunities

```
Phase 2 parallel:  T002 + T004 can run simultaneously (different files)
                   T005 + T006 can run simultaneously (different test files)
Phase 3 parallel:  T007 + T008 + T009 can all start simultaneously
Phase 4 parallel:  T012 + T013 + T014 can all start simultaneously
Phase 6 parallel:  T018 + T019 can run simultaneously
```

---

## Implementation Strategy

### MVP (US1 + US2 core, no scheduler)

1. T001: Install APScheduler
2. T002–T003: Seed food database
3. T004: Build plan explainer
4. T009: Build workout engine
5. T010: Wire workout engine into recommendation_service
6. T014: Build diet engine
7. T015: Wire diet engine into recommendation_service
8. **VALIDATE**: Both generate endpoints return plans with no LLM running
9. Then add tests (T005–T008, T012–T013) and scheduler (T018–T020)

### Key File Locations

| File | Change |
|------|--------|
| `src/services/recommendation_service.py` | Remove LLM calls, wire engines (T010, T015, T021) |
| `src/services/diet_engine.py` | NEW (T014) |
| `src/services/workout_engine.py` | NEW (T009) |
| `src/services/plan_explainer.py` | NEW (T004) |
| `src/services/food_seeder.py` | NEW (T002) |
| `src/data/foods.json` | NEW — USDA seeded (T003) |
| `src/main.py` | Add lifespan + scheduler (T018) |
| `src/routers/recommendations.py` | Add 2 food-db endpoints (T019) |
| `requirements.txt` | + apscheduler==3.11.2 (T001) |
