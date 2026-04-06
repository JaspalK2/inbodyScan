# API Contracts: Algorithmic Plan Engine

**Feature**: `013-algorithmic-plan-engine`

The generate endpoints' **request and response schemas are unchanged**. The only change is the internal implementation — the LLM call is replaced by the algorithmic engine. No frontend changes required.

---

## Unchanged Endpoints

### POST /api/recommendations/diet/generate
### POST /api/recommendations/workout/generate

Request and response schemas remain identical to the current implementation.

---

## New Endpoint: POST /api/recommendations/food-db/refresh

Manually trigger the food database refresh (admin/maintenance use only — also runs automatically on the weekly schedule).

**Request**: No body required. Authenticated endpoint (JWT).

**Response 200**:
```json
{
  "foods_fetched": 187,
  "foods_written": 187,
  "last_updated": "2026-04-05T02:00:00Z"
}
```

**Response 500** (if USDA API unreachable):
```json
{
  "detail": "Food database refresh failed — USDA API unavailable. Using existing cached data."
}
```

---

## New Endpoint: GET /api/recommendations/food-db/status

Check the age and size of the local food database (useful for monitoring refresh health).

**Response 200**:
```json
{
  "food_count": 187,
  "last_updated": "2026-04-05T02:00:00Z",
  "refresh_interval_days": 7,
  "next_refresh": "2026-04-12T02:00:00Z"
}
```

---

## Internal Contract: `structured_plan` JSON Schema

The `structured_plan` JSON stored in the database must conform to these schemas for the frontend to render correctly.

### Workout `structured_plan`
```json
{
  "plan_explanation": "string (2-4 sentences, references body fat % and goal)",
  "summary": "string (1 sentence overview)",
  "days": [
    {
      "day": 1,
      "focus": "Push – Chest & Triceps",
      "is_rest": false,
      "exercises": [
        {
          "name": "Barbell Bench Press",
          "sets": 4,
          "reps": "8-12",
          "rest_seconds": 90,
          "notes": "Keep shoulder blades retracted"
        }
      ],
      "estimated_duration_minutes": 60
    }
  ],
  "progression_notes": "string"
}
```

### Diet `structured_plan`
```json
{
  "summary": "string",
  "daily_targets": {
    "calories": 2200,
    "protein_g": 165,
    "carbs_g": 250,
    "fat_g": 73,
    "fiber_g": 30
  },
  "days": [
    {
      "day": 1,
      "meals": [
        {
          "meal": "breakfast",
          "foods": ["100g oats", "2 whole eggs", "1 banana"],
          "calories": 550,
          "protein_g": 22,
          "carbs_g": 80,
          "fat_g": 12,
          "fiber_g": 8
        }
      ],
      "day_totals": {
        "calories": 2190,
        "protein_g": 162,
        "carbs_g": 248,
        "fat_g": 72,
        "fiber_g": 29
      }
    }
  ],
  "micronutrient_highlights": ["string"],
  "meal_prep_tips": ["string"],
  "macro_targets": { "calories": 2200, "protein_g": 165, "..." : "..." }
}
```

**Rule**: `day_totals` MUST equal the sum of `meals[*].{calories,protein_g,carbs_g,fat_g,fiber_g}`. The algorithmic engine computes this directly; no estimation.
