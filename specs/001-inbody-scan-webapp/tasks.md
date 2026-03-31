---
description: "Task list for InBody Scan Health Web Application"
---

# Tasks: InBody Scan Health Web Application

**Input**: Design documents from `/specs/001-inbody-scan-webapp/`
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅

**Note**: Per project constitution Principle IV (Mandatory Test Coverage), test tasks are REQUIRED for this project. All user story phases include test tasks that must be written before implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US8)
- Exact file paths included in all task descriptions

## Path Conventions

- Backend services: `services/{service-name}/src/`
- Frontend: `frontend/src/`
- Shared Python: `shared/python/`
- Infrastructure: `vercel.json` (production routing), `scripts/` (local dev helpers)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project skeleton, Vercel configuration, local dev tooling, and design system initialization. No Docker or Traefik — services run with `uvicorn` locally and deploy as Vercel serverless functions.

- [ ] T001 Create full project directory structure: `services/{auth,user,scan,analytics,recommendation,admin}-service/`, `frontend/`, `shared/python/`, `scripts/` at repository root
- [ ] T002 [P] Initialize each FastAPI service with `pyproject.toml` and `requirements.txt` (include `fastapi`, `mangum`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pydantic[email]`, `pyjwt`, `passlib[bcrypt]`, `httpx`, `supabase`) for all 6 services under `services/`
- [ ] T003 [P] Initialize Next.js 15 project with TypeScript, Tailwind CSS 3.x, and shadcn/ui in `frontend/` (`npx create-next-app@latest` with App Router + TypeScript + Tailwind)
- [ ] T004 [P] Create `vercel.json` at repository root configuring: (a) Next.js framework build for `frontend/`, (b) Python serverless function rewrites routing `/api/auth/*` → `services/auth-service/src/main.py`, `/api/users/*` → `services/user-service/src/main.py`, `/api/scans/*` → `services/scan-service/src/main.py`, `/api/analytics/*` → `services/analytics-service/src/main.py`, `/api/recommendations/*` → `services/recommendation-service/src/main.py`, `/api/admin/*` → `services/admin-service/src/main.py`
- [ ] T005 [P] Create `.env.example` with all required variables (with inline comments): `GOOGLE_API_KEY`, `USDA_API_KEY`, `JWT_SECRET_KEY`, `JWT_ALGORITHM=HS256`, `ACCESS_TOKEN_EXPIRE_MINUTES=15`, `REFRESH_TOKEN_EXPIRE_DAYS=7`, `INITIAL_ADMIN_USERNAME`, `INITIAL_ADMIN_PASSWORD`; per-service `DATABASE_URL=postgresql+asyncpg://postgres:[password]@[host]:5432/[db]`; `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_STORAGE_BUCKET=scan-pdfs`; `ALLOWED_ORIGINS=http://localhost:3000`
- [ ] T006 [P] Create `shared/python/` as an installable package (`pyproject.toml`) containing `auth_utils/` (JWT encode/decode, get_current_user dependency) and `http_client/` (base async httpx client with auth header injection)
- [ ] T007 [P] Configure Alembic for each of the 5 database-owning services (auth, user, scan, analytics, recommendation) — one `alembic/` directory per service with async-compatible `env.py` that reads `DATABASE_URL` env var (`postgresql+asyncpg://...` pointing to Supabase)
- [ ] T008 [P] Create local dev run script `scripts/start-local.sh` that launches all 6 FastAPI services with `uvicorn` on ports 8001–8006 and prints per-service URLs
- [ ] T009 [P] Configure linting and formatting: `ruff` + `mypy` for all Python services (shared `pyproject.toml` root config); ESLint + TypeScript strict mode for `frontend/`
- [ ] T010 Configure Option D glassmorphism design theme in `frontend/tailwind.config.ts` (tokens: bg `#0D1117`→`#1A0A2E`, card `rgba(255,255,255,0.05)` + backdrop-blur, primary `#A855F7`, secondary `#06B6D4`, font Geist) and `frontend/src/styles/globals.css` (CSS variables + Tailwind base)
- [ ] T011 [P] Install Geist font (MIT) and shadcn/ui chart components (Recharts-based) in `frontend/`: `npm install geist` and initialize shadcn CLI with chart component

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared infrastructure patterns that ALL user stories depend on. No user story work can begin until this phase is complete.

- [ ] T012 Create SQLAlchemy 2.0 async session factory in `shared/python/auth_utils/database.py` — async engine from `DATABASE_URL` env var (`postgresql+asyncpg://...` pointing to Supabase in all environments), `AsyncSession` dependency for FastAPI route injection, reused across all 5 DB services
- [ ] T013 [P] Create `BaseModel` SQLAlchemy mixin (id UUID PK auto-generated, created_at UTC datetime, updated_at UTC auto-updated) in `shared/python/auth_utils/base_model.py`
- [ ] T014 [P] Implement JWT access token encode/decode (HS256, configurable expiry) and refresh token utilities in `shared/python/auth_utils/jwt.py` using PyJWT 2.x
- [ ] T015 [P] Implement bcrypt password hashing (`hash_password`, `verify_password`) using passlib[bcrypt] in `services/auth-service/src/core/security.py`
- [ ] T016 Implement `get_current_user` FastAPI dependency (extracts and validates JWT from `Authorization: Bearer` header, returns `{user_id, username, role}`) in `shared/python/auth_utils/dependencies.py` — used by all 5 non-auth services
- [ ] T017 [P] Create `require_role("admin")` FastAPI dependency (wraps `get_current_user`, raises 403 if role ≠ admin) in `shared/python/auth_utils/dependencies.py`
- [ ] T018 [P] Implement base async HTTP client in `shared/python/http_client/base_client.py` using httpx: configurable base URL per service, automatic Bearer token injection for internal calls, structured error handling
- [ ] T019 [P] Add `handler = Mangum(app)` entry point to each of the 6 FastAPI `main.py` files so Vercel can invoke the ASGI app as a serverless function; add `mangum` to each service's `requirements.txt`
- [ ] T020 [P] Configure pytest + pytest-asyncio for each service with `conftest.py` providing: async test client, isolated Supabase test schema (or `pytest-postgresql` ephemeral instance) for DB setup/teardown, and mock JWT token factory
- [ ] T021 [P] Configure Vitest for frontend in `frontend/vitest.config.ts` with jsdom environment and React Testing Library
- [ ] T022 Configure Playwright in `frontend/playwright.config.ts` with base URL `http://localhost:3000` (local `next dev` stack) and create `frontend/tests/e2e/` directory with shared fixture for authenticated sessions (calls local uvicorn services)
- [ ] T023 [P] Create sample InBody scan PDF test fixtures in `services/scan-service/tests/fixtures/` — at minimum one valid InBody PDF and one invalid/corrupt PDF for parser testing

**Checkpoint**: Foundation ready — all user story implementations can now begin in parallel.

---

## Phase 3: User Story 1 — Secure Login and Account Access (Priority: P1) 🎯 MVP

**Goal**: Fully functional login, session management, JWT-based route protection, and strict per-user data isolation.

**Independent Test**: Create two users, log in as each, confirm neither can access the other's data via direct URL manipulation.

### Tests for User Story 1 ⚠️ Write and verify these FAIL before implementing

- [ ] T025 [P] [US1] Integration test: `POST /auth/login` with valid credentials returns 200 + access token + sets refresh cookie in `services/auth-service/tests/integration/test_auth_router.py`
- [ ] T026 [P] [US1] Integration test: `POST /auth/login` with wrong password returns 401 in `services/auth-service/tests/integration/test_auth_router.py`
- [ ] T027 [P] [US1] Integration test: `POST /auth/refresh` with valid cookie returns new access token in `services/auth-service/tests/integration/test_auth_router.py`
- [ ] T028 [P] [US1] Integration test: `GET /internal/auth/verify` with valid token returns user payload; expired token returns 401 in `services/auth-service/tests/integration/test_auth_router.py`
- [ ] T029 [P] [US1] Unit test: `hash_password` + `verify_password` round-trip succeeds; wrong password fails in `services/auth-service/tests/unit/test_security.py`
- [ ] T030 [P] [US1] Unit test: `encode_access_token` / `decode_access_token` round-trip in `shared/python/tests/test_jwt.py`; expired token raises error
- [ ] T031 [P] [US1] E2E test: login page renders, submits credentials, redirects to `/dashboard` in `frontend/tests/e2e/test_login.spec.ts`

### Implementation for User Story 1

- [ ] T032 [P] [US1] Create `User` SQLAlchemy model (id UUID PK, username VARCHAR UNIQUE, password_hash, role ENUM, is_active BOOL, created_at, updated_at) in `services/auth-service/src/models/user.py`
- [ ] T033 [P] [US1] Create `RefreshToken` SQLAlchemy model (id UUID PK, user_id UUID indexed, token_hash VARCHAR UNIQUE, expires_at, revoked BOOL) in `services/auth-service/src/models/refresh_token.py`
- [ ] T034 [US1] Generate Alembic migration for `users` and `refresh_tokens` tables in `services/auth-service/alembic/versions/`
- [ ] T035 [P] [US1] Create `UserRepository` (get_by_username, get_by_id, create, update_active_status) in `services/auth-service/src/repositories/user_repository.py`
- [ ] T036 [P] [US1] Create `TokenRepository` (create_refresh_token, get_by_hash, revoke_token, revoke_all_for_user) in `services/auth-service/src/repositories/token_repository.py`
- [ ] T037 [US1] Implement `AuthService` (login: verify password → issue access+refresh tokens; logout: revoke token; refresh: roll refresh token; verify: decode JWT) in `services/auth-service/src/services/auth_service.py`
- [ ] T038 [P] [US1] Create Pydantic schemas (LoginRequest, LoginResponse, TokenResponse, UserIdentity) in `services/auth-service/src/schemas/auth.py`
- [ ] T039 [US1] Implement auth router (POST `/login`, `/logout`, `/refresh`, GET `/me`, internal POST `/internal/auth/verify`) in `services/auth-service/src/routers/auth_router.py`
- [ ] T040 [US1] Create first-boot admin seeder (reads `INITIAL_ADMIN_USERNAME` + `INITIAL_ADMIN_PASSWORD` env vars, creates admin account if no users exist) in `services/auth-service/src/core/seeder.py` — called from FastAPI lifespan
- [ ] T041 [US1] Bootstrap auth-service FastAPI app with CORS middleware, lifespan (DB init + seeder), and router registration in `services/auth-service/src/main.py`
- [ ] T042 [P] [US1] Implement login page UI (glassmorphism card, username/password form, error state, loading state) using shadcn/ui Form + Input in `frontend/src/app/(auth)/login/page.tsx`
- [ ] T043 [P] [US1] Implement auth API client (login POST, logout POST, refresh POST, getMe GET) in `frontend/src/lib/api/auth.ts`
- [ ] T044 [US1] Implement Next.js route protection middleware (redirect unauthenticated to `/login`, redirect admin to `/admin`, redirect regular users away from `/admin`) in `frontend/src/middleware.ts`

**Checkpoint**: User Story 1 fully functional — login, logout, token refresh, and route protection working independently.

---

## Phase 4: User Story 2 — InBody Scan Upload and Data Extraction (Priority: P1)

**Goal**: PDF upload, synchronous InBody metric extraction (returns result directly in the response), metric storage and retrieval.

**Independent Test**: Upload a fixture InBody PDF, receive extraction results in the upload response, verify all 24 standard metric keys are present with correct values.

### Tests for User Story 2 ⚠️ Write and verify these FAIL before implementing

- [ ] T045 [P] [US2] Unit test: `InBodyParser.parse(pdf_bytes)` extracts all 24 standard metric keys from fixture PDF with correct values in `services/scan-service/tests/unit/test_inbody_parser.py`
- [ ] T046 [P] [US2] Unit test: parser returns partial results (not empty) when optional fields are missing from PDF in `services/scan-service/tests/unit/test_inbody_parser.py`
- [ ] T047 [P] [US2] Unit test: parser raises `ExtractionError` (not silent failure) on non-InBody PDF in `services/scan-service/tests/unit/test_inbody_parser.py`
- [ ] T048 [P] [US2] Integration test: `POST /scans/upload` with valid PDF returns 202 + `scan_id` + `extraction_status: pending` in `services/scan-service/tests/integration/test_scan_router.py`
- [ ] T049 [P] [US2] Integration test: `POST /scans/upload` with same `scan_date` as existing scan returns 409 with correct error message in `services/scan-service/tests/integration/test_scan_router.py`
- [ ] T050 [P] [US2] Integration test: `GET /scans/{id}` after successful extraction returns all stored metrics in `services/scan-service/tests/integration/test_scan_router.py`
- [ ] T051 [P] [US2] Integration test: `DELETE /scans/{id}` removes scan; same ID returns 404 afterward in `services/scan-service/tests/integration/test_scan_router.py`

### Implementation for User Story 2

- [ ] T052 [P] [US2] Create `InBodyScan` SQLAlchemy model (id UUID PK, user_id UUID indexed, scan_date DATE, upload_date DATETIME, pdf_filename, pdf_storage_path, extraction_status ENUM, extraction_error TEXT nullable, raw_extraction_json TEXT nullable) in `services/scan-service/src/models/scan.py`
- [ ] T053 [P] [US2] Create `ScanMetric` SQLAlchemy model (id UUID PK, scan_id UUID indexed, user_id UUID indexed, metric_key VARCHAR, metric_value FLOAT, unit VARCHAR) in `services/scan-service/src/models/scan_metric.py`
- [ ] T054 [US2] Generate Alembic migration for `inbody_scans` and `scan_metrics` tables with unique constraint on `(user_id, scan_date)` in `services/scan-service/alembic/versions/`
- [ ] T055 [P] [US2] Create `ScanRepository` (create, get_by_id_for_user, list_for_user ordered by scan_date DESC, update_extraction_status, delete_for_user; enforce unique user+scan_date) in `services/scan-service/src/repositories/scan_repository.py`
- [ ] T056 [P] [US2] Create `ScanMetricRepository` (bulk_create, get_by_scan_id, get_by_user_and_metric_key) in `services/scan-service/src/repositories/metric_repository.py`
- [ ] T057 [US2] Implement `InBodyParser` using pdfplumber to extract all 24 standard metric keys (body_fat_percentage, skeletal_muscle_mass_kg, body_mass_index, total_body_water_l, visceral_fat_level, body_weight_kg, protein_kg, minerals_kg, body_fat_mass_kg, fat_free_mass_kg, segmental muscle/fat for 5 body regions, basal_metabolic_rate_kcal, intracellular/extracellular water, ecw_tbw_ratio) in `services/scan-service/src/parsers/inbody_parser.py`
- [ ] T058 [US2] Implement synchronous extraction handler (`async def extract_and_save`) — calls InBodyParser, bulk-saves ScanMetrics, updates scan status to success/failed, triggers profile auto-populate via user-service client; invoked directly inside `POST /scans/upload` in `services/scan-service/src/services/extraction_handler.py`
- [ ] T059 [P] [US2] Create Pydantic schemas (ScanUploadResponse, ScanListItem, ScanDetail, ScanStatusResponse, MetricItem) in `services/scan-service/src/schemas/scan.py`
- [ ] T060 [US2] Implement `ScanService` (upload: store PDF, create scan record, call extraction_handler synchronously, return completed scan with metrics; list; get; delete) in `services/scan-service/src/services/scan_service.py`
- [ ] T061 [US2] Implement scan router (POST `/upload` multipart, GET `/`, GET `/{id}`, GET `/{id}/status`, DELETE `/{id}`) with `get_current_user` dependency on all routes in `services/scan-service/src/routers/scan_router.py`
- [ ] T062 [US2] Bootstrap scan-service FastAPI app with DB init, `get_current_user` middleware, and `handler = Mangum(app)` for Vercel in `services/scan-service/src/main.py`
- [ ] T063 [P] [US2] Implement `ScanUpload` component (drag-and-drop PDF zone, loading spinner during upload, success/error state on response — no polling required) using shadcn/ui in `frontend/src/components/scans/ScanUpload.tsx`
- [ ] T064 [P] [US2] Implement `ScanCard` component (scan date, extraction status badge, metric count summary) in `frontend/src/components/scans/ScanCard.tsx`
- [ ] T065 [P] [US2] Implement scan API client (uploadScan, listScans, getScan, getScanStatus, deleteScan) in `frontend/src/lib/api/scans.ts`
- [ ] T066 [P] [US2] Create TanStack Query hooks (useScans, useUploadScan mutation with loading/error state, useDeleteScan) in `frontend/src/lib/hooks/useScans.ts`
- [ ] T067 [US2] Implement scans page (upload zone + scan list with status badges) in `frontend/src/app/(app)/scans/page.tsx`

**Checkpoint**: User Story 2 fully functional — upload, async extraction, status polling, and scan history all work independently.

---

## Phase 5: User Story 3 — Progress Dashboard (Priority: P2)

**Goal**: Side-by-side comparison of two most recent scans with metric delta indicators, empty states, and goal-aware direction labeling.

**Independent Test**: User with two scans sees correct delta values and directional indicators on dashboard; user with one scan sees single-scan state; user with no scans sees empty state.

### Tests for User Story 3 ⚠️ Write and verify these FAIL before implementing

- [ ] T068 [P] [US3] Unit test: `DeltaService.compute_deltas()` returns correct `delta`, `current`, `previous`, and `direction` for all metrics in `services/analytics-service/tests/unit/test_delta_service.py`
- [ ] T069 [P] [US3] Unit test: `direction` resolves to `improved` when body_fat_percentage decreases for goal `lose_body_fat`, and `declined` when it increases in `services/analytics-service/tests/unit/test_delta_service.py`
- [ ] T070 [P] [US3] Integration test: `GET /analytics/dashboard` with two scans returns correct delta structure with `current_scan_id`, `previous_scan_id`, and all metric deltas in `services/analytics-service/tests/integration/test_analytics_router.py`
- [ ] T071 [P] [US3] Integration test: `GET /analytics/dashboard` with zero scans returns 204 in `services/analytics-service/tests/integration/test_analytics_router.py`
- [ ] T072 [P] [US3] E2E test: dashboard page loads for user with two scans and shows at least 5 metric cards with delta values and direction arrows in `frontend/tests/e2e/test_dashboard.spec.ts`

### Implementation for User Story 3

- [ ] T073 [P] [US3] Create `DashboardCache` SQLAlchemy model (id UUID PK, user_id UUID UNIQUE, current_scan_id UUID, previous_scan_id UUID, delta_json TEXT, generated_at DATETIME) in `services/analytics-service/src/models/dashboard_cache.py`
- [ ] T074 [US3] Generate Alembic migration for `dashboard_cache` table in `services/analytics-service/alembic/versions/`
- [ ] T075 [P] [US3] Create internal scan-service HTTP client (get_latest_two_scans_for_user, get_scan_metrics) in `services/analytics-service/src/clients/scan_client.py`
- [ ] T076 [P] [US3] Create internal user-service HTTP client (get_active_goal_for_user) in `services/analytics-service/src/clients/user_client.py`
- [ ] T077 [US3] Implement `DeltaService` (fetch 2 latest scans via scan_client, fetch active goal via user_client, compute per-metric deltas, determine `direction` based on goal type, cache result) in `services/analytics-service/src/services/delta_service.py`
- [ ] T078 [P] [US3] Create Pydantic schemas (DashboardResponse, MetricDelta) in `services/analytics-service/src/schemas/dashboard.py`
- [ ] T079 [US3] Implement analytics router `GET /analytics/dashboard` endpoint in `services/analytics-service/src/routers/analytics_router.py`
- [ ] T080 [US3] Bootstrap analytics-service FastAPI app in `services/analytics-service/src/main.py`
- [ ] T081 [P] [US3] Implement `MetricDeltaCard` component (metric name, current value, previous value, delta with sign, directional arrow icon colored by direction: green/red/gray) in `frontend/src/components/dashboard/MetricDeltaCard.tsx`
- [ ] T082 [P] [US3] Implement `DashboardGrid` component (responsive grid of MetricDeltaCards, scan date header, empty/single-scan states) in `frontend/src/components/dashboard/DashboardGrid.tsx`
- [ ] T083 [P] [US3] Implement analytics API client (getDashboard) in `frontend/src/lib/api/analytics.ts`
- [ ] T084 [US3] Implement dashboard Server Component page (fetch dashboard data server-side, render DashboardGrid with Suspense boundary) in `frontend/src/app/(app)/dashboard/page.tsx`

**Checkpoint**: User Story 3 fully functional — dashboard comparison renders correctly for all scan count states.

---

## Phase 6: User Story 4 — Metrics Visualization via Graphs (Priority: P2)

**Goal**: Historical scan data rendered as three distinct chart types (line trend, donut composition, segmental bar) with interactive tooltips.

**Independent Test**: User with 3+ scans sees all chart types rendering with correct data; single-scan user sees placeholders for multi-scan charts and composition donut renders.

### Tests for User Story 4 ⚠️ Write and verify these FAIL before implementing

- [ ] T085 [P] [US4] Integration test: `GET /analytics/metrics` returns list of available metric keys with scan counts in `services/analytics-service/tests/integration/test_analytics_router.py`
- [ ] T086 [P] [US4] Integration test: `GET /analytics/metrics/body_fat_percentage/history` returns time-series with correct dates and values in `services/analytics-service/tests/integration/test_analytics_router.py`
- [ ] T087 [P] [US4] Unit test (Vitest): `transformToRechartsLine()` produces correct `[{date, value}]` shape for Recharts LineChart in `frontend/src/lib/utils/chartTransformers.test.ts`
- [ ] T088 [P] [US4] E2E test: metrics page with 3+ scans renders LineChart, DonutChart, and BarChart all visible and non-empty in `frontend/tests/e2e/test_metrics.spec.ts`

### Implementation for User Story 4

- [ ] T089 [US4] Implement `MetricsHistoryService` (list available metric keys for user from scan-service, get time-series for a specific metric key) in `services/analytics-service/src/services/metrics_service.py`
- [ ] T090 [US4] Add metrics endpoints to analytics router (`GET /analytics/metrics`, `GET /analytics/metrics/{metric_key}/history`) in `services/analytics-service/src/routers/analytics_router.py`
- [ ] T091 [P] [US4] Implement `TrendLineChart` component (Recharts LineChart with glassmorphism card wrapper, date x-axis, value y-axis, tooltip showing exact value + date) in `frontend/src/components/charts/TrendLineChart.tsx`
- [ ] T092 [P] [US4] Implement `CompositionDonutChart` component (Recharts PieChart/RadialBarChart showing fat mass %, muscle mass %, water % breakdown) in `frontend/src/components/charts/CompositionDonutChart.tsx`
- [ ] T093 [P] [US4] Implement `SegmentalBarChart` component (Recharts BarChart showing muscle/fat mass per body region: right arm, left arm, trunk, right leg, left leg) in `frontend/src/components/charts/SegmentalBarChart.tsx`
- [ ] T094 [P] [US4] Implement chart data transformer utilities (transformToRechartsLine, transformToRechartsDonut, transformToRechartsSegmental) in `frontend/src/lib/utils/chartTransformers.ts`
- [ ] T095 [P] [US4] Create TanStack Query hooks (useAvailableMetrics, useMetricHistory) in `frontend/src/lib/hooks/useMetrics.ts`
- [ ] T096 [US4] Implement metrics page with metric selector tabs, all three chart types, multi-scan placeholders for insufficient data in `frontend/src/app/(app)/metrics/page.tsx`

**Checkpoint**: User Story 4 fully functional — all chart types render with correct data and interactive tooltips.

---

## Phase 7: User Story 5 — User Profile and Health Information (Priority: P2)

**Goal**: Full user profile management including age, sex, height, dietary restrictions, health goals, and clinically-inconsistent-goal warnings.

**Independent Test**: Create profile, set "vegetarian" restriction and "lose_body_fat" goal, verify both persist. Set a BMI-conflicting goal and verify warning response is returned.

### Tests for User Story 5 ⚠️ Write and verify these FAIL before implementing

- [ ] T097 [P] [US5] Integration test: `GET /users/me/profile` returns null fields for new user, populated fields after update in `services/user-service/tests/integration/test_user_router.py`
- [ ] T098 [P] [US5] Integration test: `PUT /users/me/goals` deactivates previous goal (sets is_active=false) and creates new active goal in `services/user-service/tests/integration/test_user_router.py`
- [ ] T099 [P] [US5] Integration test: `PUT /users/me/goals` with `lose_body_fat` for user profile with BMI < 18.5 returns 200 with `warning` field populated in `services/user-service/tests/integration/test_user_router.py`
- [ ] T100 [P] [US5] Integration test: `POST /users/me/restrictions` with duplicate non-custom type returns 409 in `services/user-service/tests/integration/test_user_router.py`
- [ ] T101 [P] [US5] Integration test: `DELETE /users/me/restrictions/{id}` removes restriction; re-fetching list no longer contains it in `services/user-service/tests/integration/test_user_router.py`
- [ ] T102 [P] [US5] E2E test: profile page saves dietary restrictions and health goal; values persist after page reload in `frontend/tests/e2e/test_profile.spec.ts`

### Implementation for User Story 5

- [ ] T103 [P] [US5] Create `UserProfile` SQLAlchemy model (id UUID PK, user_id UUID UNIQUE indexed, age INT nullable, biological_sex ENUM nullable, height_cm FLOAT nullable, weight_kg FLOAT nullable, updated_at DATETIME) in `services/user-service/src/models/user_profile.py`
- [ ] T104 [P] [US5] Create `HealthGoal` SQLAlchemy model (id UUID PK, user_id UUID indexed, goal_type ENUM, is_active BOOL default true, created_at DATETIME; composite index on user_id + is_active) in `services/user-service/src/models/health_goal.py`
- [ ] T105 [P] [US5] Create `DietaryRestriction` SQLAlchemy model (id UUID PK, user_id UUID indexed, restriction_type ENUM, custom_value VARCHAR nullable, created_at DATETIME; unique constraint on user_id + restriction_type for non-custom types) in `services/user-service/src/models/dietary_restriction.py`
- [ ] T106 [US5] Generate Alembic migration for `user_profiles`, `health_goals`, `dietary_restrictions` tables in `services/user-service/alembic/versions/`
- [ ] T107 [P] [US5] Create `UserProfileRepository` (get_or_create_for_user, update, auto_populate_from_scan) in `services/user-service/src/repositories/profile_repository.py`
- [ ] T108 [P] [US5] Create `HealthGoalRepository` (get_active_for_user, create_and_deactivate_previous, list_for_user) in `services/user-service/src/repositories/goal_repository.py`
- [ ] T109 [P] [US5] Create `DietaryRestrictionRepository` (list_for_user, create, delete_for_user; enforce unique non-custom constraint) in `services/user-service/src/repositories/restriction_repository.py`
- [ ] T110 [US5] Implement `UserService` (profile CRUD; goal set with active-goal deactivation; goal conflict check: BMI < 18.5 + lose_body_fat, BMI > 35 + gain_muscle_mass → return warning; restriction management) in `services/user-service/src/services/user_service.py`
- [ ] T111 [P] [US5] Create Pydantic schemas (UserProfileResponse, UpdateProfileRequest, HealthGoalResponse, SetGoalRequest, SetGoalResponse with optional `warning`, DietaryRestrictionResponse, AddRestrictionRequest) in `services/user-service/src/schemas/`
- [ ] T112 [US5] Implement user router (GET/PUT `/users/me/profile`, GET/PUT `/users/me/goals`, GET/POST `/users/me/restrictions`, DELETE `/users/me/restrictions/{id}`) in `services/user-service/src/routers/user_router.py`
- [ ] T113 [US5] Bootstrap user-service FastAPI app in `services/user-service/src/main.py`
- [ ] T114 [P] [US5] Implement `ProfileForm` component (age, sex, height, weight fields; goal selector; dietary restriction multi-select with custom input; inline warning banner for goal conflicts) using shadcn/ui Form, Select, Badge in `frontend/src/components/profile/ProfileForm.tsx`
- [ ] T115 [P] [US5] Implement user API client (getProfile, updateProfile, getGoal, setGoal, getRestrictions, addRestriction, deleteRestriction) in `frontend/src/lib/api/users.ts`
- [ ] T116 [US5] Implement profile page (Server Component load, client-side ProfileForm with TanStack Query mutations, toast on save) in `frontend/src/app/(app)/profile/page.tsx`

**Checkpoint**: User Story 5 fully functional — profile, goals, restrictions, and conflict warnings all work independently.

---

## Phase 8: User Story 6 — AI-Powered Diet Recommendations (Priority: P2)

**Goal**: Async LLM diet recommendation generation with restriction compliance, full macro/micronutrient breakdown, USDA-backed values, and browsable history.

**Independent Test**: Vegetarian user requests diet recommendation; result excludes meat/fish, includes all 11 micronutrients, macros shown with % of daily value, history endpoint returns all past recommendations.

### Tests for User Story 6 ⚠️ Write and verify these FAIL before implementing

- [ ] T117 [P] [US6] Unit test: `DietPromptBuilder.build()` for vegetarian user includes "vegetarian" restriction and excludes PII (no names, no UUIDs) in `services/recommendation-service/tests/unit/test_diet_prompt_builder.py`
- [ ] T118 [P] [US6] Unit test: `DietPromptBuilder.build()` includes USDA nutritional context for at least 3 relevant foods in `services/recommendation-service/tests/unit/test_diet_prompt_builder.py`
- [ ] T119 [P] [US6] Unit test: USDA cache lookup returns correct `calories_per_100g` and `protein_g_per_100g` for a seeded food in `services/recommendation-service/tests/unit/test_usda_cache.py`
- [ ] T120 [P] [US6] Integration test: `POST /recommendations/diet/generate` with complete user profile returns 202 + `recommendation_id` + `status: pending` in `services/recommendation-service/tests/integration/test_diet_router.py`
- [ ] T121 [P] [US6] Integration test: `POST /recommendations/diet/generate` without active goal returns 400 in `services/recommendation-service/tests/integration/test_diet_router.py`
- [ ] T122 [P] [US6] Integration test: `GET /recommendations/diet/latest` after completed job returns response with `daily_targets`, `micronutrients` (min 6 nutrients), and `meal_suggestions` in `services/recommendation-service/tests/integration/test_diet_router.py`
- [ ] T123 [P] [US6] Integration test: `GET /recommendations/diet/history` returns list of past recommendations ordered by generated_at DESC in `services/recommendation-service/tests/integration/test_diet_router.py`
- [ ] T124 [P] [US6] E2E test: diet recommendations page generates plan, displays macros table and micronutrients with % daily value, history tab shows past recommendations in `frontend/tests/e2e/test_diet_recommendation.spec.ts`

### Implementation for User Story 6

- [ ] T125 [P] [US6] Create `DietRecommendation` SQLAlchemy model (id UUID PK, user_id UUID indexed, scan_id UUID, goal_type ENUM, generated_at DATETIME, daily_calories_kcal FLOAT, protein_g FLOAT, carbohydrates_g FLOAT, fat_g FLOAT, fiber_g FLOAT, micronutrients_json TEXT, meal_suggestions_json TEXT, dietary_restrictions_applied TEXT, llm_model_used VARCHAR, llm_prompt_version VARCHAR) in `services/recommendation-service/src/models/diet_recommendation.py`
- [ ] T126 [P] [US6] Create `NutritionalFood` SQLAlchemy model (id UUID PK, fdc_id INT UNIQUE, food_name VARCHAR, all macro fields per 100g, nutrients_json TEXT, boolean flags for restrictions: is_vegetarian, is_vegan, contains_eggs, contains_dairy, contains_gluten, contains_nuts, contains_shellfish, contains_fish, last_synced_at DATETIME) in `services/recommendation-service/src/models/nutritional_food.py`
- [ ] T127 [US6] Generate Alembic migration for `diet_recommendations` and `nutritional_foods` tables in `services/recommendation-service/alembic/versions/`
- [ ] T128 [P] [US6] Create `DietRecommendationRepository` (create, get_latest_for_user, list_for_user ordered by generated_at DESC, get_by_id_for_user) in `services/recommendation-service/src/repositories/diet_recommendation_repository.py`
- [ ] T129 [P] [US6] Create `NutritionalFoodRepository` (get_by_fdc_id, search_by_name, get_restriction_compliant_foods) in `services/recommendation-service/src/repositories/nutritional_food_repository.py`
- [ ] T130 [US6] Implement `LLMClient` abstract base class with `generate(prompt: str) -> str` method in `services/recommendation-service/src/llm/client.py`
- [ ] T131 [US6] Implement `GeminiClient` extending `LLMClient` using `google-generativeai` SDK (gemini-2.0-flash model, structured JSON output mode, retry on 429/503) in `services/recommendation-service/src/llm/gemini_client.py`
- [ ] T132 [US6] Implement diet prompt template v1 (constructs structured prompt from: scan metrics dict, goal_type, restriction list, USDA nutritional context subset; no PII included) in `services/recommendation-service/src/llm/prompt_templates/diet_v1.py`
- [ ] T133 [US6] Implement USDA FoodData Central sync script (fetch top 500 foods by nutrient completeness, parse macros + 11 micronutrients, classify restriction flags, upsert to NutritionalFood cache) in `services/recommendation-service/src/usda/sync_usda.py`
- [ ] T134 [US6] Implement `DietRecommendationService` (validate preconditions: active scan + active goal; build prompt using DietPromptBuilder; call GeminiClient; parse JSON response; validate all required nutrient fields present; save DietRecommendation) in `services/recommendation-service/src/services/diet_service.py`
- [ ] T135 [US6] Implement `POST /recommendations/diet/generate` as a synchronous async endpoint that calls `DietRecommendationService.generate()` directly and returns the completed recommendation in the response (no background task); add 60-second FastAPI route timeout guard in `services/recommendation-service/src/routers/diet_router.py`
- [ ] T136 [P] [US6] Create Pydantic schemas (DietGenerateResponse, DietStatusResponse, DietRecommendationDetail with nested DailyTargets and MicronutrientDetail, DietHistoryItem) in `services/recommendation-service/src/schemas/diet.py`
- [ ] T137 [US6] Implement diet recommendation router (POST `/recommendations/diet/generate`, GET `/recommendations/diet/status/{id}`, GET `/recommendations/diet/latest`, GET `/recommendations/diet/history`) in `services/recommendation-service/src/routers/diet_router.py`
- [ ] T138 [US6] Bootstrap recommendation-service FastAPI app with DB init, USDA cache sync on startup (if cache empty), all routers registered, and `handler = Mangum(app)` for Vercel in `services/recommendation-service/src/main.py`
- [ ] T139 [P] [US6] Implement `MacroNutrientTable` component (protein/carbs/fat/fiber with grams and % daily value progress bars) in `frontend/src/components/recommendations/MacroNutrientTable.tsx`
- [ ] T140 [P] [US6] Implement `MicroNutrientGrid` component (vitamin D, B12, C, A, E; iron, calcium, potassium, magnesium, zinc, sodium — each with target, unit, % daily value) in `frontend/src/components/recommendations/MicroNutrientGrid.tsx`
- [ ] T141 [P] [US6] Implement `MealSuggestionList` component (meal name, description, approx calories + protein per meal) in `frontend/src/components/recommendations/MealSuggestionList.tsx`
- [ ] T142 [P] [US6] Implement recommendation API client (generateDietRecommendation, getDietStatus, getLatestDietRecommendation, getDietHistory) in `frontend/src/lib/api/recommendations.ts`
- [ ] T143 [US6] Implement diet recommendations page (generate button → loading spinner during synchronous HTTP request → renders recommendation on success → error state with retry button on timeout/failure; history list tab shows past recommendations) in `frontend/src/app/(app)/recommendations/diet/page.tsx`

**Checkpoint**: User Story 6 fully functional — end-to-end diet recommendation generation with restriction compliance, full nutritional display, and browsable history.

---

## Phase 9: User Story 7 — AI-Powered Workout Recommendations (Priority: P3)

**Goal**: Async LLM workout plan generation aligned to user's goal, with weekly plan structure and browsable history.

**Independent Test**: User with "gain_muscle_mass" goal gets a plan emphasizing resistance training with sets/reps; "lose_body_fat" user gets cardio-focused plan. History endpoint returns all past plans.

### Tests for User Story 7 ⚠️ Write and verify these FAIL before implementing

- [ ] T144 [P] [US7] Unit test: workout prompt for `gain_muscle_mass` goal includes "resistance" / "strength" keywords; `lose_body_fat` includes "cardio" / "aerobic" keywords in `services/recommendation-service/tests/unit/test_workout_prompt_builder.py`
- [ ] T145 [P] [US7] Integration test: `POST /recommendations/workout/generate` returns 202 for user with active scan + goal in `services/recommendation-service/tests/integration/test_workout_router.py`
- [ ] T146 [P] [US7] Integration test: `GET /recommendations/workout/latest` returns `weekly_plan` with at least 3 day entries, each with `type` and `exercises` list in `services/recommendation-service/tests/integration/test_workout_router.py`
- [ ] T147 [P] [US7] E2E test: workout page displays weekly plan with exercises grouped by day in `frontend/tests/e2e/test_workout_recommendation.spec.ts`

### Implementation for User Story 7

- [ ] T148 [P] [US7] Create `WorkoutRecommendation` SQLAlchemy model (id UUID PK, user_id UUID indexed, scan_id UUID, goal_type ENUM, generated_at DATETIME, weekly_sessions INT, session_duration_min INT, weekly_plan_json TEXT, llm_model_used VARCHAR, llm_prompt_version VARCHAR) in `services/recommendation-service/src/models/workout_recommendation.py`
- [ ] T149 [US7] Generate Alembic migration for `workout_recommendations` table in `services/recommendation-service/alembic/versions/`
- [ ] T150 [P] [US7] Create `WorkoutRecommendationRepository` (create, get_latest_for_user, list_for_user ordered by generated_at DESC, get_by_id_for_user) in `services/recommendation-service/src/repositories/workout_recommendation_repository.py`
- [ ] T151 [US7] Implement workout prompt template v1 (constructs prompt from: scan metrics, goal_type, profile; no PII; instructs LLM to return structured 7-day plan JSON) in `services/recommendation-service/src/llm/prompt_templates/workout_v1.py`
- [ ] T152 [US7] Implement `WorkoutRecommendationService` (validate preconditions; build workout prompt; call GeminiClient; parse JSON response; validate weekly_plan structure; save WorkoutRecommendation) in `services/recommendation-service/src/services/workout_service.py`
- [ ] T153 [US7] Implement `POST /recommendations/workout/generate` as a synchronous async endpoint that calls `WorkoutRecommendationService.generate()` and returns the completed plan in the response; add 60-second timeout guard in `services/recommendation-service/src/routers/workout_router.py`
- [ ] T154 [P] [US7] Create Pydantic schemas (WorkoutGenerateResponse, WorkoutStatusResponse, WorkoutRecommendationDetail, WeeklyPlan, DayPlan, Exercise) in `services/recommendation-service/src/schemas/workout.py`
- [ ] T155 [US7] Add workout recommendation router (POST `/recommendations/workout/generate`, GET `/recommendations/workout/status/{id}`, GET `/recommendations/workout/latest`, GET `/recommendations/workout/history`) in `services/recommendation-service/src/routers/workout_router.py`
- [ ] T156 [P] [US7] Implement `WorkoutDayCard` component (day name, session type badge, exercises list with name + sets/reps or duration + intensity) in `frontend/src/components/recommendations/WorkoutDayCard.tsx`
- [ ] T157 [P] [US7] Implement workout API client functions (generateWorkoutRecommendation, getWorkoutStatus, getLatestWorkoutRecommendation, getWorkoutHistory) in `frontend/src/lib/api/recommendations.ts` (extend existing file)
- [ ] T158 [US7] Implement workout recommendations page (generate button → loading spinner during synchronous HTTP request → renders weekly plan grid on success → error state with retry button; history list tab) in `frontend/src/app/(app)/recommendations/workout/page.tsx`

**Checkpoint**: User Story 7 fully functional — workout plans generate, display correctly by goal type, and history is browsable.

---

## Phase 10: User Story 8 — Admin Portal: User Management (Priority: P3)

**Goal**: Admin-only portal for creating and managing user accounts with strict health-data isolation.

**Independent Test**: Regular user gets 403 on all admin endpoints; admin creates a new user; new user logs in; admin cannot see new user's health data via any endpoint.

### Tests for User Story 8 ⚠️ Write and verify these FAIL before implementing

- [ ] T159 [P] [US8] Integration test: regular user JWT receives 403 on `GET /admin/users` in `services/admin-service/tests/integration/test_admin_router.py`
- [ ] T160 [P] [US8] Integration test: `POST /admin/users` creates account; new user can login via auth-service in `services/admin-service/tests/integration/test_admin_router.py`
- [ ] T161 [P] [US8] Integration test: `GET /admin/users` response objects contain only `id`, `username`, `role`, `is_active`, `created_at` — no health-data fields in `services/admin-service/tests/integration/test_admin_router.py`
- [ ] T162 [P] [US8] Integration test: `PATCH /admin/users/{id}/status` with `is_active: false` prevents subsequent login in `services/admin-service/tests/integration/test_admin_router.py`
- [ ] T163 [P] [US8] E2E test: admin login redirects to `/admin` (not `/dashboard`); admin can see user list; admin cannot navigate to any user health page in `frontend/tests/e2e/test_admin.spec.ts`

### Implementation for User Story 8

- [ ] T164 [P] [US8] Create internal auth-service HTTP client (create_user, list_users, update_user_status, delete_user) in `services/admin-service/src/clients/auth_client.py`
- [ ] T165 [P] [US8] Create Pydantic schemas (AdminUserListItem, CreateUserRequest, CreateUserResponse, UpdateStatusRequest) in `services/admin-service/src/schemas/admin.py`
- [ ] T166 [US8] Implement `AdminService` (create user via auth_client; list users; update status; delete user; guard: cannot delete last admin; cannot delete own account) in `services/admin-service/src/services/admin_service.py`
- [ ] T167 [US8] Implement admin router (GET `/admin/users`, POST `/admin/users`, PATCH `/admin/users/{id}/status`, DELETE `/admin/users/{id}`) with `require_role("admin")` dependency on all routes in `services/admin-service/src/routers/admin_router.py`
- [ ] T168 [US8] Bootstrap admin-service FastAPI app in `services/admin-service/src/main.py`
- [ ] T169 [P] [US8] Implement `UserTable` component (sortable table of users: username, role badge, status badge, deactivate/delete action buttons) using shadcn/ui Table in `frontend/src/components/admin/UserTable.tsx`
- [ ] T170 [P] [US8] Implement `CreateUserForm` component (username + password fields, role selector, submit with loading state) using shadcn/ui Dialog + Form in `frontend/src/components/admin/CreateUserForm.tsx`
- [ ] T171 [P] [US8] Implement admin API client (listUsers, createUser, updateUserStatus, deleteUser) in `frontend/src/lib/api/admin.ts`
- [ ] T172 [US8] Implement admin portal page (user table, create user dialog, deactivate/delete actions with confirmation dialog) in `frontend/src/app/admin/page.tsx`

**Checkpoint**: All user stories are now independently functional and complete.

---

## Phase 11: Polish, Deployment & Cross-Cutting Concerns

**Purpose**: Navigation, UX polish, observability, security hardening, and Vercel deployment readiness.

### Vercel Deployment Preparation

- [ ] T173 [P] Implement `SupabaseStorageClient` in `services/scan-service/src/storage/supabase_storage.py` using `supabase-py` SDK — methods: `store_pdf(user_id, scan_id, pdf_bytes) -> storage_path` (uploads to `scan-pdfs` bucket) and `retrieve_pdf(storage_path) -> bytes`; used directly by ScanService with no local-file fallback needed
- [ ] T174 [P] Configure `next.config.ts` for Vercel: add `images.remotePatterns` for Supabase Storage domain; add `NEXT_PUBLIC_API_BASE_URL` env var consumed by all API client functions (defaults to empty string for same-origin calls on Vercel)
- [ ] T175 [P] Add CORS middleware to all 6 FastAPI services reading `ALLOWED_ORIGINS` env var (comma-separated); set `http://localhost:3000` for local dev and `https://{project}.vercel.app` for production; add to `.env.example`
- [ ] T176 [P] Verify `.env.example` contains all required Supabase keys (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_ANON_KEY`, `SUPABASE_STORAGE_BUCKET=scan-pdfs`) and `ALLOWED_ORIGINS` with inline documentation comments; confirm `.gitignore` excludes `.env`
- [ ] T177 [P] Create `docs/deployment.md`: step-by-step Vercel-only deployment guide — (1) create Supabase project + copy DATABASE_URLs, (2) create Vercel project from repo, (3) set all env vars in Vercel dashboard, (4) run `alembic upgrade head` per service, (5) verify via Vercel preview URL

### Navigation & UX

- [ ] T179 Implement shared app layout with glassmorphism sidebar navigation (links to dashboard, metrics, recommendations, profile, scans; active state highlighting; user display + logout button) in `frontend/src/components/layout/AppSidebar.tsx` and `frontend/src/app/(app)/layout.tsx`
- [ ] T180 [P] Implement skeleton loading components for dashboard, metrics, and recommendation pages in `frontend/src/components/ui/skeletons/`
- [ ] T181 [P] Implement `DisclaimerBanner` component (non-dismissible health disclaimer: "Not a medical device — consult a professional") shown on diet and workout recommendation pages in `frontend/src/components/recommendations/DisclaimerBanner.tsx`
- [ ] T182 [P] Implement React error boundary wrapping all major page sections; display graceful fallback UI on unexpected render errors in `frontend/src/components/ErrorBoundary.tsx`

### Observability & Security Hardening

- [ ] T183 [P] Add structured JSON logging to all FastAPI services: log request method, path, user_id (from JWT), response status, duration; never log PII or raw health metric values
- [ ] T184 [P] Audit all repository `SELECT` queries across all 5 DB services to confirm every query includes `WHERE user_id = :current_user_id` scope filter (security hardening per constitution Principle V)
- [ ] T185 [P] Audit all list endpoints to confirm pagination (`limit`/`offset`) is present and a maximum page size is enforced on every paginated route

### Infrastructure Finalization

- [ ] T185 Create `scripts/seed-usda-data.sh` that runs the USDA sync script (`python -m services.recommendation-service.src.usda.sync_usda`) to pre-populate the nutritional food cache; document in `quickstart.md` as a one-time setup step
- [ ] T186 Create `scripts/test-all-services.sh` that runs pytest for all 5 backend services sequentially and reports pass/fail per service
- [ ] T187 Run the full `quickstart.md` validation checklist against the locally running stack (`scripts/start-local.sh` + `next dev`) and resolve any failures before first Vercel deployment

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Phase 2 — BLOCKS all subsequent user stories (other services verify JWT issued by auth-service)
- **US2 (Phase 4)**: Depends on US1 completion (scan service requires valid JWT)
- **US3, US4, US5 (Phases 5–7)**: Depend on US1 + US2 completion (require scans to exist); can run in parallel with each other
- **US6 (Phase 8)**: Depends on US5 completion (requires user profile + goals + restrictions)
- **US7 (Phase 9)**: Depends on US5 completion; can run in parallel with US6
- **US8 (Phase 10)**: Depends on US1 completion only; can run in parallel with US2–US7
- **Polish (Phase 11)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: No story dependencies — start after Foundational
- **US2 (P1)**: Depends on US1 (JWT auth)
- **US3 (P2)**: Depends on US1 + US2
- **US4 (P2)**: Depends on US1 + US2; can run parallel to US3
- **US5 (P2)**: Depends on US1; can run parallel to US2/US3/US4
- **US6 (P2)**: Depends on US1 + US2 + US5
- **US7 (P3)**: Depends on US1 + US2 + US5; can run parallel to US6
- **US8 (P3)**: Depends on US1 only; can run parallel to US2–US7

### Within Each User Story

- Tests MUST be written and verified to FAIL before implementation begins
- Models → Repositories → Services → Routers (backend)
- API client → Hooks → Components → Page (frontend)
- Backend complete before frontend integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel within Phase 2
- US3, US4, and US5 can be developed in parallel once US1+US2 are complete
- US6 and US7 can be developed in parallel once US5 is complete
- US8 can be developed in parallel with all other stories once US1 is complete
- All test tasks marked [P] within a story can run in parallel
- All model tasks marked [P] within a story can run in parallel

---

## Implementation Strategy

### MVP (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1 (Login) → validate independently
4. Complete Phase 4: US2 (Scan upload + extraction) → validate independently
5. **STOP and VALIDATE**: Users can log in, upload scans, and see extracted metrics
6. Deploy/demo as MVP

### Incremental Delivery

1. Setup + Foundational → foundation ready
2. + US1 → secure login working
3. + US2 → scan upload + extraction working
4. + US3 + US4 + US5 (parallel) → dashboard, graphs, and profile working
5. + US6 + US7 (parallel) → diet and workout recommendations working
6. + US8 → admin portal working
7. + Polish → production-ready

### Parallel Team Strategy (3+ developers)

After US1 + US2 are complete:
- Developer A: US3 (dashboard) + US4 (metrics)
- Developer B: US5 (profile) → then US6 (diet recommendations)
- Developer C: US8 (admin portal) → then US7 (workout recommendations)

---

## Notes

- [P] tasks = different files, no blocking dependencies — safe to parallelize
- [Story] label maps task to spec.md user story for traceability
- Tests marked ⚠️ must FAIL before implementation — confirm failure before writing production code
- All test tasks are MANDATORY per project constitution Principle IV
- Commit after each completed task or logical group
- Stop at each Checkpoint to validate the story works independently
- Never skip the user_id scoping audit (T178) — data isolation is non-negotiable per constitution
