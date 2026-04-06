# API Contracts: Editable AI-Generated Plans

**Service**: recommendation-service (port 8004)  
**Base path**: `/api/recommendations`  
**Auth**: Bearer JWT (all endpoints require `get_current_user_id`)

---

## Existing Endpoints (unchanged)

These endpoints already exist and are used as-is:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/workout/generate` | Generate a new AI workout plan |
| GET | `/workout` | List all workout recommendations for user |
| PATCH | `/workout/{rec_id}` | Save edited workout plan |
| POST | `/diet/generate` | Generate a new AI diet plan |
| GET | `/diet` | List all diet recommendations for user |
| PATCH | `/diet/{rec_id}` | Save edited diet plan |

---

## New Endpoint: Score a Workout Plan

**Purpose**: Compute a workout quality score for a generated (or edited) workout plan without saving. Used for live score updates during editing.

```
POST /api/recommendations/workout/score-plan
Authorization: Bearer <token>
Content-Type: application/json
```

### Request Body

```json
{
  "plan": {
    "weeks": [
      {
        "week": 1,
        "days": [
          {
            "day": 1,
            "focus": "Upper Body",
            "exercises": [
              {
                "name": "Bench Press",
                "sets": 4,
                "reps": "8-10",
                "rest_seconds": 90,
                "notes": "optional"
              }
            ]
          }
        ]
      }
    ]
  }
}
```

**Notes**:
- `plan` is the full structured plan JSON (same shape as `structured_plan` or `edited_plan` from the DB)
- All weeks and days are flattened before scoring — the score reflects total program coverage
- `sets` must be an integer ≥ 1 for the exercise to count toward volume scoring
- `name` field is mapped to `exercise_name` internally before passing to `score_workout_split`

### Response (200 OK)

```json
{
  "overall": 87,
  "coverage_score": 90,
  "volume_score": 85,
  "balance_score": 88,
  "cardio_score": 75,
  "frequency_score": 95,
  "covered_groups": ["chest", "back", "legs", "shoulders", "arms"],
  "missing_groups": ["core"],
  "weekly_sets_per_group": {"chest": 16, "back": 20, "legs": 24},
  "feedback": ["Add 2-3 sets of core work", "Good push/pull balance"],
  "label": "Excellent"
}
```

### Error Responses

| Status | Condition |
|--------|-----------|
| 400 | Missing or malformed `plan` field |
| 401 | Missing or invalid JWT |
| 422 | Validation error (Pydantic) |

---

## Modified Endpoint: Generate Workout Plan (error handling)

**Change**: `POST /workout/generate` now returns 503 (not 500) when the Gemini API quota is exhausted.

```
POST /api/recommendations/workout/generate
POST /api/recommendations/diet/generate
```

### New Error Response (503 Service Unavailable)

```json
{
  "detail": "Plan generation is temporarily unavailable — please try again shortly."
}
```

This response is returned when:
- Gemini API returns HTTP 429 (`ResourceExhausted`)
- The `Retry-After` header is not forwarded (client should apply its own retry delay, recommended 30 s)

Previously these conditions produced a 500 Internal Server Error. The fix is in `GeminiClient.generate()`.

---

## Schema: WorkoutScorePlanRequest

```python
class WorkoutScorePlanRequest(BaseModel):
    plan: dict  # full structured_plan or edited_plan JSON
```

This schema is added to `schemas/recommendation.py`.

---

## Frontend Consumption Notes

### Live Score Update Flow

```
user edits exercise → debounce 300ms → POST /workout/score-plan → update score UI
```

The frontend sends the current in-memory plan state (not the saved DB version) to get the live score.

### Live Macro Update Flow

```
user edits meal → recompute in-browser:
  total_protein_g = sum(meal.protein_g for day in days for meal in day.meals)
  total_carbs_g   = sum(meal.carbs_g ...)
  total_fat_g     = sum(meal.fat_g ...)
  total_calories  = protein*4 + carbs*4 + fat*9
→ update pie chart
```

No API call needed for macro updates — all values are present in the plan JSON.

### Save Flow

```
user clicks Save →
  PATCH /workout/{rec_id}  body: { "edited_plan": <current plan JSON> }
  OR
  PATCH /diet/{rec_id}     body: { "edited_plan": <current plan JSON> }
→ response: full recommendation object → update local state
```

### Discard Flow

```
user clicks Discard →
  restore in-memory plan to last saved state (from initial GET response)
  re-run score computation on original plan
```
