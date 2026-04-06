# Contract: Profile API (user-service)

**Service**: user-service (`http://localhost:8002`)  
**Change**: `activity_level` field added to profile read/write endpoints.

---

## GET /api/users/me/profile

**Auth**: Bearer token required  
**Response** (200 OK):

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "first_name": "string | null",
  "last_name": "string | null",
  "age": "integer | null",
  "height_cm": "float | null",
  "weight_kg": "float | null",
  "gender": "male | female | other | null",
  "activity_level": "sedentary | lightly_active | moderately_active | very_active | extra_active | null"
}
```

---

## PATCH /api/users/me/profile

**Auth**: Bearer token required  
**Request body** (all fields optional):

```json
{
  "first_name": "string",
  "last_name": "string",
  "age": 25,
  "height_cm": 175.0,
  "weight_kg": 70.0,
  "gender": "male | female | other",
  "activity_level": "sedentary | lightly_active | moderately_active | very_active | extra_active"
}
```

**Response** (200 OK): Same as GET response above.  
**Error** (422): Validation error — field type mismatch.

---

## GET/PUT /api/users/me/goal — unchanged

No contract changes. See existing implementation.

## GET/POST/DELETE /api/users/me/dietary-restrictions — unchanged

No contract changes. See existing implementation.

---

## Test Requirements

- `GET /me/profile` returns `activity_level: null` for a new user
- `PATCH /me/profile` with `activity_level: "very_active"` persists and is returned on next GET
- `PATCH /me/profile` with unknown `activity_level` value returns 422
- `PATCH /me/profile` without `activity_level` field does not overwrite existing value
