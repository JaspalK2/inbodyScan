# API Contracts: Food Log Endpoints

**Service**: recommendation-service (port 8005)  
**Auth**: Bearer JWT required on all endpoints  
**Prefix**: `/api/recommendations`

---

## POST /food-log

Create one or more food log entries for a given date.

**Request body**:
```json
{
  "log_date": "2026-04-02",
  "entries": [
    {
      "fdc_id": 534358,
      "food_name": "Chicken Breast, grilled",
      "brand": null,
      "source": "manual",
      "source_ref_id": null,
      "quantity_g": 200,
      "calories_kcal": 330,
      "protein_g": 62,
      "carbs_g": 0,
      "fat_g": 7.2,
      "fiber_g": 0
    }
  ]
}
```

**Response 201**:
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "log_date": "2026-04-02",
    "fdc_id": 534358,
    "food_name": "Chicken Breast, grilled",
    "brand": null,
    "source": "manual",
    "source_ref_id": null,
    "quantity_g": 200,
    "calories_kcal": 330,
    "protein_g": 62,
    "carbs_g": 0,
    "fat_g": 7.2,
    "fiber_g": 0,
    "created_at": "2026-04-02T14:32:00Z"
  }
]
```

**Errors**: 400 if entries array is empty; 422 if food_name missing or quantity_g ≤ 0.

---

## GET /food-log

Fetch all log entries for a specific date.

**Query params**: `date=YYYY-MM-DD` (required)

**Response 200**:
```json
[
  {
    "id": "uuid",
    "log_date": "2026-04-02",
    "food_name": "Chicken Breast, grilled",
    "brand": null,
    "source": "manual",
    "quantity_g": 200,
    "calories_kcal": 330,
    "protein_g": 62,
    "carbs_g": 0,
    "fat_g": 7.2,
    "fiber_g": 0
  }
]
```

Returns empty array `[]` if no entries for that date.

---

## DELETE /food-log/{entry_id}

Remove a single log entry. User must own the entry.

**Response**: 204 No Content  
**Errors**: 404 if entry not found or not owned by user.

---

## GET /food-log/dates

Return all dates (ISO strings) that have at least one log entry for the user — used to populate a calendar indicator.

**Response 200**:
```json
["2026-04-01", "2026-04-02", "2026-03-28"]
```

---

## Existing Endpoints Unchanged

| Endpoint | Notes |
|----------|-------|
| `GET /food/search?q=...` | Unchanged — `Branded` data type already returns restaurant items labelled by `brand` |
| `GET /food/{fdc_id}` | Unchanged |
| `POST /meals` | Unchanged — saved custom meals |
| `GET /meals` | Unchanged |
| `PATCH /diet/{id}` | Unchanged — saves edited diet plan |
| `PATCH /workout/{id}` | Unchanged — saves edited workout plan |
| `POST /diet/generate` | Unchanged |
| `POST /workout/generate` | Unchanged |
