# Data Model: InBody Scan Health Web Application

**Branch**: `001-inbody-scan-webapp` | **Date**: 2026-03-31

Each microservice owns its own database. Entities are grouped by owning service.
Cross-service references use UUIDs (not foreign keys) — services call each other's APIs to resolve references.

---

## Auth Service (`auth.db`)

### User

The core identity record. Owns authentication credentials and role assignment.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | Generated on creation |
| username | VARCHAR(64) | UNIQUE, not null | Lowercase, alphanumeric + underscore |
| password_hash | VARCHAR(256) | not null | bcrypt hash, never stored in plain text |
| role | ENUM | not null | `user` or `admin` |
| is_active | BOOLEAN | not null, default true | Deactivated accounts cannot log in |
| created_at | DATETIME | not null | UTC, set on creation |
| updated_at | DATETIME | not null | UTC, updated on any change |

**Validation rules**:
- `username`: 3–64 characters, alphanumeric + underscore, must be unique (case-insensitive)
- `password`: minimum 8 characters at input; only the bcrypt hash is stored
- `role`: only `user` or `admin` are valid values
- `is_active = false` blocks login but does not delete data

**Indexes**: `username` (UNIQUE), `role + is_active` (for admin user listing)

---

### RefreshToken

Tracks issued refresh tokens to support revocation.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | |
| user_id | UUID | not null, indexed | References User.id |
| token_hash | VARCHAR(256) | UNIQUE, not null | SHA-256 hash of the raw token |
| expires_at | DATETIME | not null | UTC |
| revoked | BOOLEAN | not null, default false | |
| created_at | DATETIME | not null | UTC |

**Validation rules**:
- Expired tokens (`expires_at < now`) are treated as invalid regardless of `revoked`
- At login, older refresh tokens for the same user are revoked (rolling refresh)

---

## User Service (`user.db`)

### UserProfile

Extended health profile for a registered user. `user_id` references `User.id` in auth-service.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | |
| user_id | UUID | UNIQUE, not null | One profile per user |
| age | INTEGER | nullable | In years; 10–120 valid range |
| biological_sex | ENUM | nullable | `male`, `female`, `prefer_not_to_say` |
| height_cm | FLOAT | nullable | 50–300 cm valid range |
| weight_kg | FLOAT | nullable | May be updated by scan upload |
| created_at | DATETIME | not null | UTC |
| updated_at | DATETIME | not null | UTC |

**Validation rules**:
- Height and weight are optional (can come from InBody scan)
- Age must be a positive integer if provided
- `user_id` must correspond to an active user in auth-service

**Indexes**: `user_id` (UNIQUE)

---

### HealthGoal

A user's selected fitness/health objective. Only one goal is active at a time.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | |
| user_id | UUID | not null, indexed | |
| goal_type | ENUM | not null | See values below |
| is_active | BOOLEAN | not null, default true | Only one active goal per user |
| created_at | DATETIME | not null | UTC |

**Goal types**: `lose_body_fat`, `gain_muscle_mass`, `maintain_weight`, `improve_endurance`

**Validation rules**:
- Setting a new active goal must deactivate the previous active goal for the same user
- At least one active goal must exist before the recommendation service accepts a generation request

**Indexes**: `user_id + is_active` (filtered index for active goal lookup)

---

### DietaryRestriction

Records food restrictions and allergies. A user may have multiple entries.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | |
| user_id | UUID | not null, indexed | |
| restriction_type | ENUM | not null | See values below |
| custom_value | VARCHAR(200) | nullable | Only populated when `restriction_type = custom` |
| created_at | DATETIME | not null | UTC |

**Restriction types**: `vegetarian`, `vegan`, `no_eggs`, `no_dairy`, `no_gluten`, `no_nuts`, `no_shellfish`, `no_fish`, `custom`

**Validation rules**:
- `custom_value` is required when `restriction_type = custom`; must be non-empty
- Duplicate `restriction_type` entries (excluding `custom`) per user are rejected
- Deletions are hard deletes (restrictions can be removed by the user)

**Indexes**: `user_id`

---

## Scan Service (`scan.db`)

### InBodyScan

Represents one uploaded InBody scan PDF and its extracted data.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | |
| user_id | UUID | not null, indexed | |
| scan_date | DATE | not null | From PDF if found; otherwise upload date |
| upload_date | DATETIME | not null | UTC, when the PDF was received |
| pdf_filename | VARCHAR(255) | not null | Original uploaded filename |
| pdf_storage_path | VARCHAR(512) | not null | Path to stored PDF file |
| extraction_status | ENUM | not null | `pending`, `success`, `failed` |
| extraction_error | TEXT | nullable | Error message if extraction_status = failed |
| raw_extraction_json | TEXT | nullable | Full extracted key-value JSON for reprocessing |
| created_at | DATETIME | not null | UTC |

**Validation rules**:
- Only PDF files accepted (validated by MIME type, not filename extension)
- Maximum file size: 10 MB
- Duplicate scan detection: if a scan with the same `user_id` and `scan_date` already exists, the upload is rejected with a conflict error
- `raw_extraction_json` is populated only when `extraction_status = success`

**Indexes**: `user_id`, `user_id + scan_date DESC` (for latest-scan queries)

---

### ScanMetric

Individual metric values extracted from an InBodyScan. One row per metric per scan.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | |
| scan_id | UUID | not null, indexed | References InBodyScan.id |
| user_id | UUID | not null, indexed | Denormalized for efficient user-scoped queries |
| metric_key | VARCHAR(100) | not null | Standardized key (see Metric Key Reference below) |
| metric_value | FLOAT | not null | Numeric value |
| unit | VARCHAR(20) | not null | e.g., `%`, `kg`, `L`, `score` |
| created_at | DATETIME | not null | UTC |

**Standard Metric Keys**:

| Key | Description | Unit |
|-----|-------------|------|
| `body_fat_percentage` | Body fat as % of total body weight | `%` |
| `skeletal_muscle_mass_kg` | Skeletal (lean) muscle mass | `kg` |
| `body_mass_index` | BMI | `score` |
| `total_body_water_l` | Total body water | `L` |
| `visceral_fat_level` | Visceral fat area score | `score` |
| `body_weight_kg` | Total body weight | `kg` |
| `protein_kg` | Total body protein | `kg` |
| `minerals_kg` | Total body mineral content | `kg` |
| `body_fat_mass_kg` | Absolute fat mass | `kg` |
| `fat_free_mass_kg` | Total fat-free body mass | `kg` |
| `right_arm_muscle_kg` | Right arm segmental muscle mass | `kg` |
| `left_arm_muscle_kg` | Left arm segmental muscle mass | `kg` |
| `trunk_muscle_kg` | Trunk segmental muscle mass | `kg` |
| `right_leg_muscle_kg` | Right leg segmental muscle mass | `kg` |
| `left_leg_muscle_kg` | Left leg segmental muscle mass | `kg` |
| `right_arm_fat_kg` | Right arm segmental fat mass | `kg` |
| `left_arm_fat_kg` | Left arm segmental fat mass | `kg` |
| `trunk_fat_kg` | Trunk segmental fat mass | `kg` |
| `right_leg_fat_kg` | Right leg segmental fat mass | `kg` |
| `left_leg_fat_kg` | Left leg segmental fat mass | `kg` |
| `basal_metabolic_rate_kcal` | BMR estimate from InBody | `kcal` |
| `intracellular_water_l` | Intracellular water volume | `L` |
| `extracellular_water_l` | Extracellular water volume | `L` |
| `ecw_tbw_ratio` | Extracellular/Total body water ratio | `ratio` |

**Validation rules**:
- `metric_key` must be from the standard reference above (unknown keys are stored with prefix `custom_`)
- `metric_value` cannot be NaN or Inf
- Duplicate `scan_id + metric_key` is rejected

**Indexes**: `scan_id`, `user_id + metric_key` (for time-series queries per metric)

---

## Analytics Service (`analytics.db`)

The analytics service is primarily a read-model/aggregation layer. It calls scan-service and user-service APIs. It maintains a lightweight cache table to avoid re-aggregating on every dashboard load.

### DashboardCache

Pre-computed dashboard state for a user. Refreshed when a new scan is uploaded.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | |
| user_id | UUID | UNIQUE, not null | One cache entry per user |
| current_scan_id | UUID | nullable | Latest scan ID |
| previous_scan_id | UUID | nullable | Second-latest scan ID |
| delta_json | TEXT | nullable | JSON: `{metric_key: {current, previous, delta, direction}}` |
| generated_at | DATETIME | not null | UTC, when cache was last computed |

**Indexes**: `user_id` (UNIQUE)

---

## Recommendation Service (`recommendation.db`)

### DietRecommendation

A generated dietary plan for a user at a point in time.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | |
| user_id | UUID | not null, indexed | |
| scan_id | UUID | not null | The scan used as input |
| goal_type | ENUM | not null | Copied from active HealthGoal at generation time |
| generated_at | DATETIME | not null | UTC |
| daily_calories_kcal | FLOAT | not null | |
| protein_g | FLOAT | not null | |
| carbohydrates_g | FLOAT | not null | |
| fat_g | FLOAT | not null | |
| fiber_g | FLOAT | not null | |
| micronutrients_json | TEXT | not null | JSON: `{nutrient_key: {target_amount, unit, pct_daily_value}}` |
| meal_suggestions_json | TEXT | not null | JSON array of meal objects |
| dietary_restrictions_applied | TEXT | not null | JSON array of restriction keys used at generation time |
| llm_model_used | VARCHAR(100) | not null | e.g., `gemini-2.0-flash` |
| llm_prompt_version | VARCHAR(20) | not null | Prompt template version for reproducibility |

**Micronutrients tracked** (minimum — stored in `micronutrients_json`):
`vitamin_d_mcg`, `vitamin_b12_mcg`, `vitamin_c_mg`, `vitamin_a_mcg`, `vitamin_e_mg`,
`iron_mg`, `calcium_mg`, `potassium_mg`, `magnesium_mg`, `zinc_mg`, `sodium_mg`

**Indexes**: `user_id`, `user_id + generated_at DESC` (for latest recommendation)

---

### WorkoutRecommendation

A generated exercise plan for a user at a point in time.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK, not null | |
| user_id | UUID | not null, indexed | |
| scan_id | UUID | not null | The scan used as input |
| goal_type | ENUM | not null | Copied from active HealthGoal at generation time |
| generated_at | DATETIME | not null | UTC |
| weekly_sessions | INTEGER | not null | Recommended sessions per week |
| session_duration_min | INTEGER | not null | Recommended minutes per session |
| weekly_plan_json | TEXT | not null | JSON: 7-day plan with exercises, sets, reps, intensity |
| llm_model_used | VARCHAR(100) | not null | |
| llm_prompt_version | VARCHAR(20) | not null | |

**Indexes**: `user_id`, `user_id + generated_at DESC`

---

## Nutritional Reference Cache (`recommendation.db`, shared table)

### NutritionalFood

Pre-fetched USDA FoodData Central data cached locally.

| Field | Type | Constraints | Notes |
|-------|------|-------------|-------|
| id | UUID | PK | |
| fdc_id | INTEGER | UNIQUE, not null | USDA FoodData Central food ID |
| food_name | VARCHAR(300) | not null | |
| food_category | VARCHAR(100) | nullable | |
| calories_per_100g | FLOAT | nullable | |
| protein_g_per_100g | FLOAT | nullable | |
| carbs_g_per_100g | FLOAT | nullable | |
| fat_g_per_100g | FLOAT | nullable | |
| fiber_g_per_100g | FLOAT | nullable | |
| nutrients_json | TEXT | nullable | Full micronutrient data per 100g |
| is_vegetarian | BOOLEAN | not null, default false | |
| is_vegan | BOOLEAN | not null, default false | |
| contains_eggs | BOOLEAN | not null, default false | |
| contains_dairy | BOOLEAN | not null, default false | |
| contains_gluten | BOOLEAN | not null, default false | |
| contains_nuts | BOOLEAN | not null, default false | |
| contains_shellfish | BOOLEAN | not null, default false | |
| contains_fish | BOOLEAN | not null, default false | |
| last_synced_at | DATETIME | not null | UTC |

**Indexes**: `fdc_id` (UNIQUE), `is_vegetarian`, `is_vegan` (for fast restriction filtering)

---

## Cross-Service Reference Rules

- Services NEVER share a database or access another service's tables directly.
- Cross-service data is fetched via authenticated internal HTTP calls using service-to-service JWT tokens.
- If a dependent service is unavailable, the calling service returns a `503 Service Unavailable` — it does not silently return stale or partial data.
- `user_id` (UUID) is the universal cross-service correlation key.

---

## State Transitions

### InBodyScan extraction lifecycle

```
PDF uploaded → extraction_status: pending
      ↓
Background worker processes PDF
      ↓
Success: extraction_status: success, raw_extraction_json populated
Failed:  extraction_status: failed, extraction_error populated
```

### Recommendation generation lifecycle

```
User requests recommendation
      ↓
System validates: active scan exists + active goal selected + profile complete
      ↓
Celery task queued → LLM prompt constructed → LLM call made
      ↓
Response parsed → DietRecommendation / WorkoutRecommendation saved
      ↓
Frontend polls status → displays recommendation on completion
```
