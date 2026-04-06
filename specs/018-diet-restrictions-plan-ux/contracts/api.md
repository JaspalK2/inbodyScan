# API Contracts: Fix Dietary Restriction Enforcement & Redesign Diet Plan Saved Meals UX

**Branch**: `018-diet-restrictions-plan-ux`  
**Date**: 2026-04-06

## No New Endpoints

All existing endpoints are reused unchanged. This section documents their contracts as consumed by this feature.

---

## POST /api/recommendations/diet/generate

**Purpose**: Generate a 7-day diet plan and persist a `DietRecommendation` record.

**Request Body** (`GenerateDietRequest`):
```json
{
  "scan_id": "string",
  "metrics": { "weight": 80.0, "body_fat_percentage": 20.0 },
  "goal_type": "build_muscle",
  "dietary_restrictions": ["vegetarian"],
  "age": 28,
  "height_cm": 178.0,
  "gender": "male",
  "activity_level": "moderate"
}
```

**Response** (`DietRecommendationOut`):
```json
{
  "id": "uuid",
  "user_id": "string",
  "scan_id": "string",
  "goal_type": "build_muscle",
  "structured_plan": {
    "days": [
      {
        "day": 1,
        "meals": [
          {
            "meal_name": "Breakfast",
            "items": [{ "food_name": "...", "grams": 150, "calories": 200.0, "protein_g": 15.0, "carbs_g": 20.0, "fat_g": 5.0 }],
            "meal_totals": { "calories": 200.0, "protein_g": 15.0, "carbs_g": 20.0, "fat_g": 5.0 }
          }
        ],
        "day_totals": { "calories": 2200.0, "protein_g": 165.0, "carbs_g": 247.5, "fat_g": 73.3 }
      }
    ],
    "macro_targets": { "calories": 2200, "protein_g": 165.0, "carbs_g": 247.5, "fat_g": 73.3 }
  },
  "edited_plan": null,
  "created_at": "2026-04-06T12:00:00Z"
}
```

**Contract for this feature**: `dietary_restrictions` must be populated from the user's profile and must not be an empty list when the user has active restrictions. Zero non-compliant food items must appear in the response `structured_plan`.

---

## POST /api/recommendations/day-plans

**Purpose**: Save a single day plan (called 7 times in sequence after generation).

**Request Body** (`DayPlanCreate`):
```json
{
  "name": "AI Plan 2026-04-06 (Day 1)",
  "plan_date": "2026-04-06",
  "notes": "<recommendation_id_uuid>",
  "entries": [
    {
      "meal_slot": "breakfast",
      "custom_meal_name": "Breakfast",
      "calories_kcal": 550.0,
      "protein_g": 41.25,
      "carbs_g": 61.875,
      "fat_g": 18.325,
      "items_snapshot": [
        { "food_name": "Oats", "grams": 80, "calories": 304.0, "protein_g": 11.2, "carbs_g": 52.8, "fat_g": 5.6 }
      ]
    }
  ]
}
```

**Notes field**: Stores the `DietRecommendation.id` UUID so the 7 day plans from one generation can be grouped in the UI.

---

## GET /api/recommendations/day-plans

**Purpose**: Fetch all day plans for the current user.

**Response**: Array of `DayPlanOut` ordered by `created_at DESC`.

**UI grouping**: Frontend groups by `notes` field (recommendation_id) to render one collapsible card per generation event.

---

## GET /api/users/me/dietary-restrictions

**Purpose**: Fetch user's dietary restrictions.

**Response**:
```json
[
  { "id": "uuid", "user_id": "string", "restriction_type": "vegetarian", "created_at": "..." }
]
```

**Contract**: `restriction_type` values must match the keys used in `foods.json` (`vegetarian`, `vegan`, `gluten_free`, `halal`, `kosher`, `dairy_free`).
