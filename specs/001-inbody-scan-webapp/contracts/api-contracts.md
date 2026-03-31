# API Contracts: InBody Scan Health Web Application

**Branch**: `001-inbody-scan-webapp` | **Date**: 2026-03-31

All services expose REST APIs. Traefik routes external requests to services by path prefix.
Internal service-to-service calls bypass Traefik and use Docker Compose DNS names directly.

**Base URL** (external, via Traefik): `https://{host}/api`
**Auth header**: `Authorization: Bearer {access_token}` (except login and health endpoints)
**Content-Type**: `application/json` (except file uploads: `multipart/form-data`)
**Error format**: `{"detail": "human-readable message", "code": "machine_readable_code"}`

---

## Auth Service (`/api/auth`)

### POST /api/auth/login

Authenticate a user and issue access + refresh tokens.

**Request**:
```json
{
  "username": "jdoe",
  "password": "MyPassword123"
}
```

**Response 200**:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```
Refresh token is set as an httpOnly cookie (`refresh_token`), not returned in JSON.

**Response 401**: Invalid credentials
**Response 403**: Account deactivated

---

### POST /api/auth/refresh

Exchange a valid refresh token (from cookie) for a new access token.

**Request**: No body. Refresh token read from httpOnly cookie.

**Response 200**:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**Response 401**: Refresh token expired or revoked

---

### POST /api/auth/logout

Revoke the current refresh token.

**Request**: No body.
**Response 204**: No content — logout successful.

---

### GET /api/auth/me

Return the authenticated user's identity (role, username, id).

**Response 200**:
```json
{
  "id": "uuid",
  "username": "jdoe",
  "role": "user",
  "is_active": true
}
```

---

### Internal: POST /internal/auth/verify

Called by other services to validate an access token without full auth middleware.
Not accessible via Traefik (internal Docker network only).

**Request**:
```json
{
  "token": "eyJ..."
}
```

**Response 200**:
```json
{
  "user_id": "uuid",
  "username": "jdoe",
  "role": "user"
}
```
**Response 401**: Token invalid or expired

---

## User Service (`/api/users`)

### GET /api/users/me/profile

Return the authenticated user's profile.

**Response 200**:
```json
{
  "user_id": "uuid",
  "age": 28,
  "biological_sex": "male",
  "height_cm": 178.0,
  "weight_kg": 82.5,
  "updated_at": "2026-03-31T10:00:00Z"
}
```
Any nullable field that has not been set is returned as `null`.

---

### PUT /api/users/me/profile

Update the authenticated user's profile. All fields are optional — only provided fields are updated.

**Request**:
```json
{
  "age": 29,
  "biological_sex": "male",
  "height_cm": 178.0,
  "weight_kg": 83.0
}
```

**Response 200**: Updated profile object (same shape as GET).
**Response 422**: Validation error (e.g., height out of range).

---

### GET /api/users/me/goals

Return the active health goal for the authenticated user.

**Response 200**:
```json
{
  "id": "uuid",
  "goal_type": "lose_body_fat",
  "is_active": true,
  "created_at": "2026-03-01T08:00:00Z"
}
```
**Response 404**: No active goal set.

---

### PUT /api/users/me/goals

Set or update the active health goal. Deactivates any previous active goal.

**Request**:
```json
{
  "goal_type": "lose_body_fat"
}
```
Valid values: `lose_body_fat`, `gain_muscle_mass`, `maintain_weight`, `improve_endurance`

**Response 200**: New goal object.
**Response 422**: Invalid goal_type.

---

### GET /api/users/me/restrictions

Return all dietary restrictions for the authenticated user.

**Response 200**:
```json
{
  "restrictions": [
    {"id": "uuid", "restriction_type": "vegetarian", "custom_value": null},
    {"id": "uuid", "restriction_type": "custom", "custom_value": "tree nuts"}
  ]
}
```

---

### POST /api/users/me/restrictions

Add a dietary restriction.

**Request**:
```json
{
  "restriction_type": "custom",
  "custom_value": "tree nuts"
}
```

**Response 201**: Created restriction object.
**Response 409**: Duplicate restriction_type (for non-custom types).
**Response 422**: Missing custom_value when restriction_type is custom.

---

### DELETE /api/users/me/restrictions/{restriction_id}

Remove a specific dietary restriction.

**Response 204**: Deleted.
**Response 404**: Restriction not found or does not belong to this user.

---

## Scan Service (`/api/scans`)

### POST /api/scans/upload

Upload an InBody scan PDF. Triggers async extraction.

**Request**: `multipart/form-data`
- `file`: PDF file (required, max 10 MB)
- `scan_date`: ISO date string (optional; if omitted, extracted from PDF or defaults to upload date)

**Response 202**: Accepted for async processing.
```json
{
  "scan_id": "uuid",
  "extraction_status": "pending",
  "message": "PDF received. Extraction in progress."
}
```
**Response 409**: Scan with same user_id and scan_date already exists.
**Response 415**: File is not a PDF.
**Response 413**: File exceeds 10 MB.

---

### GET /api/scans

List all scans for the authenticated user, ordered by scan_date descending.

**Query params**: `limit` (default 20, max 100), `offset` (default 0)

**Response 200**:
```json
{
  "total": 5,
  "scans": [
    {
      "id": "uuid",
      "scan_date": "2026-03-15",
      "upload_date": "2026-03-16T09:00:00Z",
      "extraction_status": "success",
      "pdf_filename": "inbody_march2026.pdf"
    }
  ]
}
```

---

### GET /api/scans/{scan_id}

Get a specific scan with all extracted metrics.

**Response 200**:
```json
{
  "id": "uuid",
  "scan_date": "2026-03-15",
  "extraction_status": "success",
  "metrics": [
    {"metric_key": "body_fat_percentage", "metric_value": 18.5, "unit": "%"},
    {"metric_key": "skeletal_muscle_mass_kg", "metric_value": 34.2, "unit": "kg"}
  ]
}
```
**Response 404**: Scan not found or does not belong to this user.

---

### GET /api/scans/{scan_id}/status

Poll extraction status for an in-progress scan.

**Response 200**:
```json
{
  "scan_id": "uuid",
  "extraction_status": "pending" | "success" | "failed",
  "extraction_error": null
}
```

---

### DELETE /api/scans/{scan_id}

Delete a scan and all its metrics.

**Response 204**: Deleted.
**Response 404**: Scan not found or does not belong to this user.

---

## Analytics Service (`/api/analytics`)

### GET /api/analytics/dashboard

Return the dashboard comparison: current scan vs previous scan, with deltas.

**Response 200**:
```json
{
  "current_scan_id": "uuid",
  "current_scan_date": "2026-03-15",
  "previous_scan_id": "uuid",
  "previous_scan_date": "2026-02-10",
  "deltas": {
    "body_fat_percentage": {
      "current": 18.5,
      "previous": 20.1,
      "delta": -1.6,
      "direction": "improved",
      "unit": "%"
    },
    "skeletal_muscle_mass_kg": {
      "current": 34.2,
      "previous": 33.0,
      "delta": 1.2,
      "direction": "improved",
      "unit": "kg"
    }
  }
}
```

`direction` values: `improved`, `declined`, `neutral` — calculated relative to the user's active goal.

**Response 204**: No scans available yet.

---

### GET /api/analytics/metrics/{metric_key}/history

Return time-series values for a specific metric across all scans.

**Response 200**:
```json
{
  "metric_key": "body_fat_percentage",
  "unit": "%",
  "series": [
    {"scan_date": "2026-01-05", "value": 21.3},
    {"scan_date": "2026-02-10", "value": 20.1},
    {"scan_date": "2026-03-15", "value": 18.5}
  ]
}
```
**Response 404**: No data for this metric for this user.

---

### GET /api/analytics/metrics

Return all metric keys that have at least one recorded value for the authenticated user.

**Response 200**:
```json
{
  "available_metrics": [
    {"metric_key": "body_fat_percentage", "unit": "%", "scan_count": 3},
    {"metric_key": "skeletal_muscle_mass_kg", "unit": "kg", "scan_count": 3}
  ]
}
```

---

## Recommendation Service (`/api/recommendations`)

### POST /api/recommendations/diet/generate

Trigger LLM diet recommendation generation for the authenticated user's latest scan.

**Request**: No body required (service fetches scan and profile internally).

**Response 202**: Accepted for async generation.
```json
{
  "recommendation_id": "uuid",
  "status": "pending",
  "message": "Recommendation generation in progress."
}
```
**Response 400**: No active scan or no active health goal set.
**Response 409**: A recommendation is already being generated for this user.

---

### GET /api/recommendations/diet/status/{recommendation_id}

Poll status of a pending diet recommendation.

**Response 200**:
```json
{
  "recommendation_id": "uuid",
  "status": "pending" | "complete" | "failed"
}
```

---

### GET /api/recommendations/diet/latest

Return the most recent completed diet recommendation.

**Response 200**:
```json
{
  "id": "uuid",
  "generated_at": "2026-03-31T12:00:00Z",
  "goal_type": "lose_body_fat",
  "daily_targets": {
    "calories_kcal": 2100,
    "protein_g": 165,
    "carbohydrates_g": 210,
    "fat_g": 65,
    "fiber_g": 30
  },
  "micronutrients": {
    "vitamin_d_mcg": {"target": 15, "unit": "mcg", "pct_daily_value": 75},
    "vitamin_b12_mcg": {"target": 2.4, "unit": "mcg", "pct_daily_value": 100},
    "calcium_mg": {"target": 1000, "unit": "mg", "pct_daily_value": 100},
    "iron_mg": {"target": 8, "unit": "mg", "pct_daily_value": 100},
    "potassium_mg": {"target": 3400, "unit": "mg", "pct_daily_value": 72}
  },
  "meal_suggestions": [
    {
      "meal": "Breakfast",
      "description": "Greek yogurt with blueberries and oats",
      "approx_calories": 420,
      "approx_protein_g": 28
    }
  ],
  "dietary_restrictions_applied": ["vegetarian"]
}
```
**Response 404**: No recommendation generated yet.

---

### GET /api/recommendations/diet/history

List all past diet recommendations, newest first.

**Query params**: `limit` (default 10), `offset` (default 0)

**Response 200**:
```json
{
  "total": 3,
  "recommendations": [
    {"id": "uuid", "generated_at": "2026-03-31T12:00:00Z", "goal_type": "lose_body_fat"}
  ]
}
```

---

### POST /api/recommendations/workout/generate

Trigger LLM workout recommendation generation.

**Response 202**: Same structure as diet generate.
**Response 400**: No active scan or no active health goal set.

---

### GET /api/recommendations/workout/latest

Return the most recent completed workout recommendation.

**Response 200**:
```json
{
  "id": "uuid",
  "generated_at": "2026-03-31T12:00:00Z",
  "goal_type": "lose_body_fat",
  "weekly_sessions": 4,
  "session_duration_min": 45,
  "weekly_plan": {
    "monday": {
      "type": "Cardio",
      "exercises": [
        {"name": "Treadmill run", "duration_min": 30, "intensity": "moderate"},
        {"name": "Jump rope", "duration_min": 10, "intensity": "high"}
      ]
    },
    "wednesday": {
      "type": "Strength",
      "exercises": [
        {"name": "Bodyweight squats", "sets": 3, "reps": 15},
        {"name": "Push-ups", "sets": 3, "reps": 12}
      ]
    },
    "friday": {"type": "Rest/Active recovery"},
    "saturday": {"type": "Cardio", "exercises": []}
  }
}
```

---

## Admin Service (`/api/admin`)

All admin endpoints require `role = admin` in the JWT. Regular users receive 403.

### GET /api/admin/users

List all registered user accounts. Health data is never returned.

**Query params**: `limit` (default 50), `offset` (default 0), `search` (optional username prefix)

**Response 200**:
```json
{
  "total": 42,
  "users": [
    {
      "id": "uuid",
      "username": "jdoe",
      "role": "user",
      "is_active": true,
      "created_at": "2026-01-10T08:00:00Z"
    }
  ]
}
```

---

### POST /api/admin/users

Create a new user account.

**Request**:
```json
{
  "username": "newuser",
  "password": "TemporaryPass123",
  "role": "user"
}
```

**Response 201**:
```json
{
  "id": "uuid",
  "username": "newuser",
  "role": "user",
  "is_active": true,
  "created_at": "2026-03-31T14:00:00Z"
}
```
**Response 409**: Username already exists.
**Response 422**: Password too short (< 8 characters) or invalid username format.

---

### PATCH /api/admin/users/{user_id}/status

Activate or deactivate a user account.

**Request**:
```json
{
  "is_active": false
}
```

**Response 200**: Updated user object (same shape as list item).
**Response 404**: User not found.
**Response 400**: Cannot deactivate the last active admin account.

---

### DELETE /api/admin/users/{user_id}

Permanently delete a user account and all associated data.

**Response 204**: Deleted.
**Response 404**: User not found.
**Response 400**: Cannot delete own admin account.

---

## Common Error Codes

| HTTP Status | Code | Meaning |
|-------------|------|---------|
| 400 | `bad_request` | Missing required precondition (e.g., no active scan) |
| 401 | `unauthorized` | No token or token expired |
| 403 | `forbidden` | Token valid but insufficient role |
| 404 | `not_found` | Resource does not exist or belongs to another user |
| 409 | `conflict` | Duplicate resource |
| 413 | `file_too_large` | Uploaded file exceeds size limit |
| 415 | `unsupported_media_type` | Wrong file type |
| 422 | `validation_error` | Request body failed validation |
| 429 | `rate_limited` | Too many requests |
| 500 | `internal_error` | Unexpected server error |
| 503 | `service_unavailable` | Dependent microservice unreachable |
