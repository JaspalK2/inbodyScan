# Data Model: Profile & Diet Fixes (010)

## Modified Entities

### UserProfile (modified)

**Table**: `user_profiles`  
**Service**: `user-service`  
**File**: `services/user-service/src/models/profile.py`

| Field | Type | Nullable | Change |
|-------|------|----------|--------|
| id | String(36) PK | No | — existing — |
| user_id | String(36) UNIQUE | No | — existing — |
| first_name | String(100) | Yes | — existing — |
| last_name | String(100) | Yes | — existing — |
| age | Integer | Yes | — existing — |
| height_cm | Float | Yes | — existing — |
| weight_kg | Float | Yes | — existing — |
| gender | String(20) | Yes | — existing — |
| **activity_level** | **String(30)** | **Yes** | **NEW** |
| created_at | DateTime(tz) | No | — existing — |
| updated_at | DateTime(tz) | No | — existing — |

**Valid values for `activity_level`**: `sedentary`, `lightly_active`, `moderately_active`, `very_active`, `extra_active`  
**Default**: `null` (not set; frontend falls back to `"moderately_active"` when null)

---

## Unchanged Entities

### HealthGoal

**Table**: `health_goals` — no schema changes.  
Fields: `id`, `user_id`, `goal_type`. Existing CRUD in user-service unchanged.

### DietaryRestriction

**Table**: `dietary_restrictions` — no schema changes.  
Fields: `id`, `user_id`, `restriction_type`, `notes`. Existing CRUD in user-service unchanged.

### DayPlanOut / CustomMealOut

No schema changes. `FoodMealsTab` reuses the existing `listDayPlans` query.

---

## Pydantic Schema Changes

**File**: `services/user-service/src/schemas/user.py`

```python
# ProfileOut — add activity_level field
class ProfileOut(BaseModel):
    ...existing fields...
    activity_level: str | None = None

# ProfileUpdate — add activity_level field
class ProfileUpdate(BaseModel):
    ...existing fields...
    activity_level: str | None = None
```

---

## Frontend Interface Changes

**File**: `frontend/lib/api.ts`

```typescript
// UserProfile interface — add activity_level
export interface UserProfile {
  ...existing fields...
  activity_level: string | null;
}
```

**File**: `frontend/app/(app)/profile/page.tsx`

```typescript
// profileSchema — add activity_level
const profileSchema = z.object({
  ...existing fields...
  activity_level: z.enum(["sedentary", "lightly_active", "moderately_active", "very_active", "extra_active"]).optional(),
});
```
