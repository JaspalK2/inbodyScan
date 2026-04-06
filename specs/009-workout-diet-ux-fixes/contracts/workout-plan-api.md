# API Contract: Workout Plan (009 changes)

## Changed: Generate Workout Plan

**Endpoint**: `POST /api/recommendations/workout/generate`  
**Change**: Response `structured_plan` shape changes from 4-week to single-week.

### Response (new shape)

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "structured_plan": {
    "days": [
      {
        "day": "Monday",
        "focus": "Push",
        "exercises": [
          { "name": "Bench Press", "sets": 4, "reps": "8-10", "rest_seconds": 90 }
        ]
      }
    ]
  },
  "score": 92.5,
  "created_at": "ISO8601"
}
```

**Contract rule**: `score` field MUST be ≥ 90.0 for any newly generated plan. Backend enforces this via retry/clamp logic.

---

## Unchanged: Score a Plan

**Endpoint**: `POST /api/recommendations/workout/score-plan`  
No changes to request/response shape. Used only for initial generation validation; not called per-edit.

---

## Auth: Token Refresh

**Endpoint**: `POST /api/auth/refresh` (existing)  
No contract change. The frontend `api.ts` interceptor now calls this automatically on 401 before retrying the original request.

**Behaviour contract**:
- On `401` response to any authenticated request: refresh once, retry once.
- If refresh returns `401`: clear token, redirect to `/login`.
- If refresh returns any other error: surface error to user, do not redirect silently.
