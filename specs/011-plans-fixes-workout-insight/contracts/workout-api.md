# Contract: Workout Recommendation API Changes

**Feature**: 011-plans-fixes-workout-insight  
**Service**: recommendation-service (port 8005)

---

## New Endpoint: Delete Workout Plan

```
DELETE /api/recommendations/workout/{rec_id}
Authorization: Bearer <JWT>
```

**Path parameter**: `rec_id` — UUID of the workout recommendation to delete.

**Authorization rule**: The authenticated user MUST own the record (`workout_recommendations.user_id == current_user_id`). Return 404 (not 403) if the record does not exist or belongs to another user.

**Response**:
- `204 No Content` — successfully deleted
- `404 Not Found` — record not found or not owned by user
- `401 Unauthorized` — missing or invalid JWT

**Side effects**: Hard delete from `workout_recommendations` table. No recovery.

---

## Modified Endpoint: Generate Workout Plan

```
POST /api/recommendations/workout/generate
Authorization: Bearer <JWT>
```

**Request body changes** (additive):
```json
{
  "scan_id": "uuid",
  "metrics": { ... },
  "goal_type": "build_muscle"
}
```

No request body change needed. Activity level is not used in workout macro calculation.

**Response `structured_plan` shape change** (additive — new `plan_explanation` key):
```json
{
  "plan_explanation": "Your scan shows strong upper body development but below-average lower body lean mass. This plan prioritizes compound leg movements and posterior chain work to address the imbalance. Upper body sessions maintain your existing strength while adding hypertrophy volume where needed.",
  "summary": "6-day PPL split targeting muscle hypertrophy",
  "days": [ ... ]
}
```

The `plan_explanation` field is a top-level key within `structured_plan`. Existing plans without this key fall back to displaying `summary` on the frontend.

---

## Unchanged Endpoints

All other endpoints remain unchanged:
- `POST /api/recommendations/workout/generate`
- `PATCH /api/recommendations/workout/{rec_id}`
- `GET /api/recommendations/workout`
- `POST /api/recommendations/diet/generate`
- `PATCH /api/recommendations/diet/{rec_id}`
- `DELETE /api/recommendations/diet/{rec_id}`
- `GET /api/recommendations/diet`
- `GET /api/recommendations/day-plans`
