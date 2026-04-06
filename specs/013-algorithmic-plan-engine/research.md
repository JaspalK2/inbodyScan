# Research: Algorithmic Plan Engine

**Feature**: `013-algorithmic-plan-engine`  
**Date**: 2026-04-05

---

## Decision 1: Food Database Source & Seed Strategy

**Decision**: Seed from USDA FoodData Central `/fdc/v1/foods/list` (Foundation Foods category), store as a static JSON file in the repo, refresh weekly via APScheduler.

**Rationale**:
- USDA FoodData Central is public domain — no license fees, no copyleft issues (Constitution §III satisfied).
- The existing `food_search.py` already has the nutrient ID mapping (1008=calories, 1003=protein, 1005=carbs, 1004=fat, 1079=fiber) and httpx client pattern — the seed script reuses this directly.
- Foundation Foods dataset has ~1,400 foods with lab-verified nutrient values. Filtering to common whole foods (chicken, rice, oats, eggs, vegetables, dairy) gives ~100–200 entries.
- Static file: plan generation reads local JSON in <1ms — no network dependency.

**Endpoint**: `GET /fdc/v1/foods/list?dataType=Foundation&pageSize=200&api_key={USDA_API_KEY}`  
**Rate limits**: 3,500 req/hour, 1 req/sec — seed script runs once and then weekly, well within limits.  
**Nutrient extraction**: Each food has a `foodNutrients` array; match `nutrientId` against the existing `_NUTRIENT_MAP` from `food_search.py`.

**Alternatives considered**:
- Hand-curated JSON: fast to build but requires manual maintenance and introduces human error in macro values.
- Live USDA API at generation time: violates offline/no-quota requirement (FR-015).

---

## Decision 2: Weekly Refresh Mechanism

**Decision**: APScheduler (MIT license) `AsyncIOScheduler` started in the FastAPI `lifespan` context manager, running the seed script as a weekly `cron` job.

**Rationale**:
- APScheduler 3.x is MIT licensed — constitution-compliant.
- `AsyncIOScheduler` integrates natively with FastAPI's asyncio event loop; no extra threads or processes.
- The lifespan pattern (`@asynccontextmanager` on `app = FastAPI(lifespan=...)`) is the FastAPI-recommended approach for startup/shutdown tasks.
- Weekly cadence (Sunday 02:00 UTC) is appropriate for nutritional data that changes rarely.
- Alternative: a separate cron script run by the OS. Simpler but requires external scheduler (cron daemon), is harder to test, and doesn't co-locate with the service.

**Implementation pattern**:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app):
    scheduler.add_job(refresh_food_db, "cron", day_of_week="sun", hour=2)
    scheduler.start()
    yield
    scheduler.shutdown()
```

---

## Decision 3: Workout Split Algorithm Design

**Decision**: Pre-defined 5-day split templates per goal type, with exercises selected from the 873-exercise database by muscle group and category filters.

**Rationale**:
- The exercise database tags each exercise with `primaryMuscles`, `category`, and `level` — sufficient for deterministic selection.
- Pre-defined splits (Push/Pull/Legs, Upper/Lower, Full Body) map cleanly to goal types and are evidence-based (Schoenfeld et al. 2016, ACSM guidelines).
- The existing `workout_scorer.py` defines the exact muscle groups and volume thresholds the algorithm must satisfy — it can be used as a validation step on the generated plan.

**Split templates by goal**:
| Goal | Split Pattern | Cardio |
|------|--------------|--------|
| muscle_gain / build_muscle | Push / Pull / Legs / Upper / Lower + 2 rest | 1 LISS session |
| lose_fat / weight_loss | Full Body x3 + Cardio x2 + 2 rest | 2 cardio sessions |
| general_health / maintain | Full Body x3 + Active Recovery x2 | 1–2 cardio sessions |
| improve_endurance | Upper / Lower / Cardio x3 + 2 rest | 3 cardio sessions |

---

## Decision 4: Diet Algorithm Design

**Decision**: Proportional meal-slot assembly — for each day, allocate macro targets across 4 meal slots using fixed ratios (breakfast 25%, lunch 35%, dinner 30%, snack 10%), then select foods from the seeded database to fill each slot within ±5%.

**Rationale**:
- Fixed macro-split ratios per meal slot are standard practice in sports nutrition and eliminate the need for optimization algorithms.
- Portion scaling: given a food's macro values per 100g, compute the portion in grams needed to hit the slot's macro target, then express as a human-readable amount.
- Variety: rotate across a pool of 3–5 pre-selected foods per slot per goal, cycling through the 7 days.
- Dietary restrictions: tag each food with restriction flags (vegetarian, vegan, gluten-free, etc.) and filter at food selection time.

**Alternatives considered**:
- Linear programming (PuLP) to optimise macro matching: more precise but adds a dependency and is overkill for ±5% tolerance with pre-portioned foods.
- Random selection with retry: simpler but can produce repetitive or nutritionally poor plans.

---

## Decision 5: Plan Explanation Templates

**Decision**: String templates with conditional branches based on body fat %, goal type, and lean mass, populated at generation time.

**Template structure**:
```
"Your body composition (body fat: {bf}%, lean mass: {lm}kg) with a {goal} goal informed 
this plan. {specific_observation}. {emphasis}. {progression}."
```
- `specific_observation`: conditional on body fat (e.g., "Your body fat is above 25%, so cardio volume is elevated")
- `emphasis`: maps to goal type
- `progression`: standard advice per split type

---

## License Audit

| Dependency | License | Status |
|------------|---------|--------|
| APScheduler 3.11 | MIT | ✅ Permitted |
| USDA FoodData Central data | Public Domain (USDA) | ✅ Permitted |
| exercises.json (existing) | CC0 / public domain (free exercise DB) | ✅ Permitted |
| httpx (existing) | BSD 3-Clause | ✅ Permitted |
