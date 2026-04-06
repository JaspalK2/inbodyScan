# API Contracts: Plan Editing and Log Fixes (005)

All endpoints are on the `recommendation-service` (default port 8003). All require `Authorization: Bearer <jwt>` header.

---

## New Endpoint

### GET /api/recommendations/exercises/search

Search the in-memory CC0 exercise dataset by name (case-insensitive substring match).

**Query Parameters**:
| Param | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| q | string | Yes | — | Search term (min 2 chars) |
| limit | int | No | 20 | Max results returned |

**Response 200**:
```json
[
  {
    "name": "Barbell Bench Press",
    "primary_muscles": ["chest"],
    "secondary_muscles": ["triceps", "shoulders"],
    "category": "strength",
    "equipment": "barbell",
    "level": "intermediate"
  }
]
```

**Response 400**: `{ "detail": "Query must be at least 2 characters" }`

**Notes**:
- Data loaded from `yuhonas/free-exercise-db` CC0 JSON at service startup; held in application memory.
- No authentication bypass — user must be authenticated (existing JWT middleware applies).
- No per-user data; same dataset for all users.

---

## Existing Endpoints Used (No Changes)

### POST /api/recommendations/meals
Create a saved meal (US1 — save meal from diet plan).
- Already exists. No changes to schema or behaviour.
- `items[].food_name` stores the full food string (e.g. "200g chicken breast").
- `items[].quantity_g` = 100 (placeholder; quantity is encoded in food_name).

### GET /api/recommendations/meals
List saved meals for the authenticated user.
- Already exists. Used by Saved Meals tab.

### GET /api/recommendations/day-plans
List saved day plans for the authenticated user.
- Already exists. Used by Saved Meals tab (US2) and Day Planner picker (US3).

### POST /api/recommendations/food-log/batch (or existing createFoodLog)
Create food log entries for a date.
- Already exists. Used to apply day plan to food log (US3).
- `source = "day_plan"`, `source_ref_id = <day_plan_id>` for traceability.

### POST /api/recommendations/workout/score-plan
Score current edited workout plan (live score update).
- Already exists. Called after exercise replacement/addition in edit mode.
