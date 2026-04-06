# Implementation Plan: Algorithmic Plan Engine

**Branch**: `013-algorithmic-plan-engine` | **Date**: 2026-04-05 | **Spec**: [spec.md](spec.md)

## Summary

Replace Groq/Gemini LLM-based plan generation with a deterministic algorithmic engine that:
1. Generates workout plans from the existing 873-exercise database using pre-defined goal-based splits
2. Generates diet plans from a USDA-seeded local food database using proportional macro allocation
3. Produces plan explanations via template strings populated with real body composition metrics
4. Refreshes the food database weekly via APScheduler — zero ongoing API cost

No frontend changes. No database schema changes.

## Technical Context

**Language/Version**: Python 3.13 (recommendation-service backend)  
**Primary Dependencies**: FastAPI 0.115, SQLAlchemy 2.0 async, httpx 0.28 (all existing); APScheduler 3.11 (new, MIT)  
**Storage**: Supabase PostgreSQL (existing, unchanged); `src/data/foods.json` (new local file)  
**Testing**: pytest + pytest-asyncio (existing)  
**Target Platform**: Linux server (Supabase/Vercel deployment)  
**Performance Goals**: Plan generation <2s (target <200ms deterministic)  
**Constraints**: Zero paid API calls at generation time; food DB reads from local file only  
**Scale/Scope**: Single recommendation-service; ~100–200 foods; 873 exercises

## Constitution Check

| Principle | Gate | Status |
|-----------|------|--------|
| I. Extensibility | New engines exposed via `DietPlanEngine` / `WorkoutPlanEngine` classes — swappable without touching router or recommendation_service | ✅ |
| II. Algorithm Efficiency | Food selection: O(n) over ~200 foods; exercise selection: O(n) over 873. All bounded, O(n). | ✅ |
| III. License Compliance | APScheduler: MIT. USDA data: public domain. All existing deps unchanged. | ✅ |
| IV. Mandatory Tests | Unit tests for all 4 new service files; integration tests for generate endpoints; end-to-end via quickstart scenarios | ✅ |
| V. UI/UX Consistency | No UI changes — same JSON schema, same frontend components | ✅ |
| Security | No PII in external calls; food DB seed uses only USDA_API_KEY; no health data sent externally | ✅ |

## Project Structure

### Documentation (this feature)
```text
specs/013-algorithmic-plan-engine/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/recommendation-api.md
└── tasks.md
```

### Source Code Changes
```text
services/recommendation-service/
├── requirements.txt                          # + apscheduler==3.11.2
├── src/
│   ├── main.py                               # Add APScheduler lifespan
│   ├── data/
│   │   └── foods.json                        # NEW — USDA-seeded food database
│   ├── services/
│   │   ├── recommendation_service.py         # MODIFIED — replace llm calls with engine calls
│   │   ├── diet_engine.py                    # NEW — algorithmic diet plan builder
│   │   ├── workout_engine.py                 # NEW — algorithmic workout plan builder
│   │   ├── plan_explainer.py                 # NEW — template-based explanation generator
│   │   └── food_seeder.py                    # NEW — USDA seed + weekly refresh
│   └── routers/
│       └── recommendations.py               # MODIFIED — add /food-db/refresh and /food-db/status
└── tests/
    ├── test_diet_engine.py                   # NEW
    ├── test_workout_engine.py                # NEW
    ├── test_plan_explainer.py                # NEW
    ├── test_food_seeder.py                   # NEW
    └── integration/
        └── test_generate_algorithmic.py      # NEW — end-to-end generate scenarios
```

## Architecture

### Diet Engine (`diet_engine.py`)

```
Input: MacroTargets + dietary_restrictions + goal_type
↓
1. Meal slot ratios: breakfast=25%, lunch=35%, dinner=30%, snack=10%
2. For each of 7 days:
   a. For each slot:
      - Compute slot macro target (ratio × daily_targets)
      - Filter foods.json by: allowed meal_slot, restriction flags
      - Select protein food + carb food + vegetables
      - Scale portions (g) to hit slot macros within ±5%
      - Compute exact meal macros from scaled portions
   b. day_totals = sum of meal macros (exact, never estimated)
3. Return structured plan matching the existing JSON schema
```

**Portion scaling**: `portion_g = target_macro_g / (food.macro_per_100g / 100)`

### Workout Engine (`workout_engine.py`)

```
Input: metrics{body_fat_percentage, weight} + goal_type
↓
1. Select split template by goal_type:
   - muscle_gain / build_muscle → PPL/Upper/Lower (5 days)
   - lose_fat / weight_loss → Full Body x3 + Cardio x2
   - general_health / maintain → Full Body x3 + Active Rest x2
   - improve_endurance → Upper/Lower/Cardio x3
2. For each training day:
   a. For each muscle group in day's focus:
      - Select 1 compound + 1-3 isolation from exercises.json
      - Assign sets/reps/rest by goal (muscle_gain: 4×8-12/90s; lose_fat: 3×12-15/60s)
3. Validate with existing workout_scorer.py (score ≥ 70)
4. Build plan_explanation via plan_explainer.py
```

### Plan Explainer (`plan_explainer.py`)

Template selection by body fat % and goal, populated with actual metrics:
- BF < 15%: lean profile messaging
- BF 15–25%: balanced profile
- BF 25–35%: elevated fat, cardio emphasis
- BF > 35%: high fat, strong cardio/diet emphasis

### Food Seeder (`food_seeder.py`)

```
GET /fdc/v1/foods/list?dataType=Foundation&pageSize=200&api_key={USDA_API_KEY}
→ Extract nutrients using existing _NUTRIENT_MAP
→ Tag with restriction flags by food category
→ Write to src/data/foods.json
→ Return count of foods written
```

On startup: if `foods.json` missing, run seed immediately before arming scheduler.  
Weekly: APScheduler `AsyncIOScheduler`, cron `sun@02:00 UTC`.

## Complexity Tracking

No O(n²) algorithms — all scans are O(n) over bounded datasets. No justification required.

## Implementation Notes

- `recommendation_service.py`: replace the `get_llm_client()` + `llm.generate()` calls in both `generate_diet_recommendation` and `generate_workout_recommendation` with calls to the new engine classes. The `llm_response` DB column stores the serialised plan JSON for audit.
- `prompt_builder.py` and `gemini_client.py` are NOT deleted — retained to avoid breaking existing imports/tests.
- `foods.json` is seeded once and committed to the repo. Weekly scheduler keeps it fresh in production.
- APScheduler is added to `requirements.txt` (`apscheduler==3.11.2`, MIT license, verified).
