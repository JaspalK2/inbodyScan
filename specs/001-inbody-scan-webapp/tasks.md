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

- [x] T001 Create full project directory structure: `services/{auth,user,scan,analytics,recommendation,admin}-service/`, `frontend/`, `shared/python/`, `scripts/` at repository root
- [x] T002 [P] Initialize each FastAPI service with `pyproject.toml` and `requirements.txt` (include `fastapi`, `mangum`, `sqlalchemy[asyncio]`, `asyncpg`, `alembic`, `pydantic[email]`, `pyjwt`, `passlib[bcrypt]`, `httpx`, `supabase`) for all 6 services under `services/`
- [x] T003 [P] Initialize Next.js 15 project with TypeScript, Tailwind CSS 3.x, and shadcn/ui in `frontend/` (`npx create-next-app@latest` with App Router + TypeScript + Tailwind)
- [x] T004 [P] Create `vercel.json` at repository root configuring: (a) Next.js framework build for `frontend/`, (b) Python serverless function rewrites routing `/api/auth/*` → `services/auth-service/src/main.py`, `/api/users/*` → `services/user-service/src/main.py`, `/api/scans/*` → `services/scan-service/src/main.py`, `/api/analytics/*` → `services/analytics-service/src/main.py`, `/api/recommendations/*` → `services/recommendation-service/src/main.py`, `/api/admin/*` → `services/admin-service/src/main.py`
- [x] T005 [P] Create `.env.example` with all required variables (with inline comments): `GOOGLE_API_KEY`, `USDA_API_KEY`, `JWT_SECRET_KEY`, `JWT_ALGORITHM=HS256`, `ACCESS_TOKEN_EXPIRE_MINUTES=15`, `REFRESH_TOKEN_EXPIRE_DAYS=7`, `INITIAL_ADMIN_USERNAME`, `INITIAL_ADMIN_PASSWORD`; per-service `DATABASE_URL=postgresql+asyncpg://postgres:[password]@[host]:5432/[db]`; `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_STORAGE_BUCKET=scan-pdfs`; `ALLOWED_ORIGINS=http://localhost:3000`
- [x] T006 [P] Create `shared/python/` as an installable package (`pyproject.toml`) containing `auth_utils/` (JWT encode/decode, get_current_user dependency) and `db_utils/` (async session factory with NullPool + uuid4 statement names for Supabase pgbouncer compatibility)
- [ ] T007 [P] Configure Alembic for each of the 5 database-owning services — skipped: tables created directly in Supabase via asyncpg migration scripts; Alembic setup deferred to future
- [x] T008 [P] Create local dev run script `scripts/start-local.sh` that launches all 6 FastAPI services with `uvicorn` on ports 8001–8006 and prints per-service URLs
- [ ] T009 [P] Configure linting and formatting: `ruff` + `mypy` for all Python services (shared `pyproject.toml` root config); ESLint + TypeScript strict mode for `frontend/`
- [x] T010 Configure glassmorphism design theme in `frontend/tailwind.config.ts` and `frontend/app/globals.css` (CSS variables + Tailwind base)
- [x] T011 [P] Install Geist font (MIT) and shadcn/ui chart components (Recharts-based) in `frontend/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared infrastructure patterns that ALL user stories depend on. No user story work can begin until this phase is complete.

- [x] T012 Create SQLAlchemy 2.0 async session factory in `shared/python/db_utils/session.py` — async engine with `NullPool` + UUID-based prepared statement names for Supabase pgbouncer transaction-mode compatibility, `AsyncSession` dependency for FastAPI route injection, reused across all 5 DB services
- [ ] T013 [P] Create `BaseModel` SQLAlchemy mixin (id UUID PK auto-generated, created_at UTC datetime, updated_at UTC auto-updated) in `shared/python/auth_utils/base_model.py`
- [x] T014 [P] Implement JWT access token encode/decode (HS256, configurable expiry) and refresh token utilities in `shared/python/auth_utils/` using PyJWT 2.x
- [x] T015 [P] Implement bcrypt password hashing (`hash_password`, `verify_password`) in `services/auth-service/src/services/auth_service.py`
- [x] T016 Implement `get_current_user_id` FastAPI dependency (extracts and validates JWT from `Authorization: Bearer` header, returns user_id) in `shared/python/auth_utils/dependencies.py` — used by all 5 non-auth services
- [x] T017 [P] Create `require_admin` FastAPI dependency in `services/admin-service/src/dependencies.py` (raises 403 if role ≠ admin)
- [ ] T018 [P] Implement base async HTTP client in `shared/python/http_client/base_client.py` using httpx: configurable base URL per service, automatic Bearer token injection for internal calls, structured error handling
- [x] T019 [P] Add `handler = Mangum(app)` entry point to each of the 6 FastAPI `main.py` files so Vercel can invoke the ASGI app as a serverless function; `mangum` added to each service's `requirements.txt`
- [ ] T020 [P] Configure pytest + pytest-asyncio for each service with `conftest.py` providing: async test client, isolated Supabase test schema for DB setup/teardown, and mock JWT token factory
- [ ] T021 [P] Configure Vitest for frontend in `frontend/vitest.config.ts` with jsdom environment and React Testing Library
- [ ] T022 Configure Playwright in `frontend/playwright.config.ts` with base URL `http://localhost:3000` and create `frontend/tests/e2e/` directory with shared fixture for authenticated sessions
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

- [x] T032 [P] [US1] Create `User` SQLAlchemy model (id UUID PK, username VARCHAR UNIQUE, hashed_password, is_admin BOOL, created_at) in `services/auth-service/src/models/user.py`
- [x] T033 [P] [US1] Create `RefreshToken` SQLAlchemy model (id UUID PK, user_id UUID indexed, token_hash VARCHAR UNIQUE, expires_at) in `services/auth-service/src/models/refresh_token.py`
- [ ] T034 [US1] Generate Alembic migration for `users` and `refresh_tokens` tables — skipped: tables created directly in Supabase
- [ ] T035 [P] [US1] Create `UserRepository` — skipped: repository pattern not used; service calls SQLAlchemy directly
- [ ] T036 [P] [US1] Create `TokenRepository` — skipped: repository pattern not used; service calls SQLAlchemy directly
- [x] T037 [US1] Implement `AuthService` (login: verify password → issue access+refresh tokens; logout: revoke token; refresh: roll refresh token) in `services/auth-service/src/services/auth_service.py`
- [x] T038 [P] [US1] Create Pydantic schemas (LoginRequest, LoginResponse, RegisterRequest, MeResponse) in `services/auth-service/src/schemas/auth.py`
- [x] T039 [US1] Implement auth router (POST `/api/auth/login`, `/api/auth/register`, `/api/auth/refresh`, `/api/auth/logout`, GET `/api/auth/me`) in `services/auth-service/src/routers/auth.py`
- [x] T040 [US1] Create first-boot admin seeder (reads `INITIAL_ADMIN_USERNAME` + `INITIAL_ADMIN_PASSWORD` env vars, creates admin account if no users exist) in `services/auth-service/src/core/seeder.py` — called from FastAPI lifespan
- [x] T041 [US1] Bootstrap auth-service FastAPI app with CORS middleware, lifespan (seeder), and router registration in `services/auth-service/src/main.py`
- [x] T042 [P] [US1] Implement login page UI (glassmorphism card, username/password form, error state, loading state) in `frontend/app/(auth)/login/page.tsx`
- [x] T043 [P] [US1] Implement auth API client (login, logout, refresh, register, getMe) in `frontend/lib/api.ts`
- [x] T044 [US1] Implement Next.js route protection middleware (redirect unauthenticated to `/login`, redirect admin to `/admin`, redirect regular users away from `/admin`) in `frontend/middleware.ts`

**Checkpoint**: User Story 1 fully functional — login, logout, token refresh, and route protection working independently.

---

## Phase 4: User Story 2 — InBody Scan Upload and Data Extraction (Priority: P1)

**Goal**: PDF upload, synchronous InBody metric extraction (returns result directly in the response), metric storage and retrieval.

**Independent Test**: Upload a fixture InBody PDF, receive extraction results in the upload response, verify all 24 standard metric keys are present with correct values.

### Tests for User Story 2 ⚠️ Write and verify these FAIL before implementing

- [ ] T045 [P] [US2] Unit test: `InBodyParser.parse(pdf_bytes)` extracts all 24 standard metric keys from fixture PDF with correct values in `services/scan-service/tests/unit/test_inbody_parser.py`
- [ ] T046 [P] [US2] Unit test: parser returns partial results (not empty) when optional fields are missing from PDF in `services/scan-service/tests/unit/test_inbody_parser.py`
- [ ] T047 [P] [US2] Unit test: parser raises `ExtractionError` (not silent failure) on non-InBody PDF in `services/scan-service/tests/unit/test_inbody_parser.py`
- [ ] T048 [P] [US2] Integration test: `POST /api/scans/upload` with valid PDF returns 201 + scan record + metrics in `services/scan-service/tests/integration/test_scan_router.py`
- [ ] T049 [P] [US2] Integration test: `POST /api/scans/upload` with same `scan_date` as existing scan returns 409 in `services/scan-service/tests/integration/test_scan_router.py`
- [ ] T050 [P] [US2] Integration test: `GET /api/scans/{id}` returns scan with all stored metrics in `services/scan-service/tests/integration/test_scan_router.py`
- [ ] T051 [P] [US2] Integration test: CSV upload auto-detects date from file and returns 201 in `services/scan-service/tests/integration/test_scan_router.py`

### Implementation for User Story 2

- [x] T052 [P] [US2] Create `InBodyScan` SQLAlchemy model (id UUID PK, user_id UUID indexed, scan_date DATE UNIQUE per user, storage_path, created_at) in `services/scan-service/src/models/scan.py`
- [x] T053 [P] [US2] Create `ScanMetric` SQLAlchemy model (id UUID PK, scan_id UUID FK, metric_key VARCHAR, metric_value FLOAT, created_at) in `services/scan-service/src/models/metric.py`
- [ ] T054 [US2] Generate Alembic migration — skipped: tables created directly in Supabase
- [ ] T055 [P] [US2] Create `ScanRepository` — skipped: repository pattern not used
- [ ] T056 [P] [US2] Create `ScanMetricRepository` — skipped: repository pattern not used
- [x] T057 [US2] Implement `InBodyParser` using pdfplumber to extract all 24 standard metric keys in `services/scan-service/src/services/pdf_extractor.py`
- [x] T058 [US2] Implement CSV extractor with full InBody CSV format support: 14-digit timestamps, lb→kg/kJ→kcal conversions, BOM handling, tabular and key-value layouts in `services/scan-service/src/services/csv_extractor.py`
- [x] T059 [P] [US2] Create Pydantic schemas (ScanOut, ScanWithMetrics, MetricOut) in `services/scan-service/src/schemas/scan.py`
- [x] T060 [US2] Implement scan service (create_scan, save_metrics, get_scan_by_id, get_scans_for_user, scan_date_exists) in `services/scan-service/src/services/scan_service.py`
- [x] T061 [US2] Implement scan router (POST `/api/scans/upload`, POST `/api/scans/upload-csv`, GET `/api/scans/`, GET `/api/scans/{id}`, GET `/api/scans/{id}/download-url`) in `services/scan-service/src/routers/scans.py`
- [x] T062 [US2] Bootstrap scan-service FastAPI app with CORS, lifespan, and `handler = Mangum(app)` in `services/scan-service/src/main.py`
- [x] T063 [P] [US2] Implement scan upload component (PDF drag-and-drop + CSV upload, loading state, success/error feedback) in `frontend/app/(app)/scans/page.tsx`
- [x] T064 [P] [US2] Implement scan card/list component (scan date, metric count) in `frontend/app/(app)/scans/page.tsx`
- [x] T065 [P] [US2] Implement scan API client (upload, uploadCsv, list, get, downloadUrl) in `frontend/lib/api.ts`
- [x] T066 [P] [US2] Create TanStack Query hooks for scans using `@tanstack/react-query` in recommendations and dashboard pages
- [x] T067 [US2] Implement scans page (upload zone + scan history list) in `frontend/app/(app)/scans/page.tsx`

**Checkpoint**: User Story 2 fully functional — upload, async extraction, status polling, and scan history all work independently.

---

## Phase 5: User Story 3 — Progress Dashboard (Priority: P2)

**Goal**: Side-by-side comparison of two most recent scans with metric delta indicators, empty states, and goal-aware direction labeling.

**Independent Test**: User with two scans sees correct delta values and directional indicators on dashboard; user with one scan sees single-scan state; user with no scans sees empty state.

### Tests for User Story 3 ⚠️ Write and verify these FAIL before implementing

- [ ] T068 [P] [US3] Unit test: `DeltaService.compute_deltas()` returns correct `delta`, `current`, `previous`, and `direction` for all metrics in `services/analytics-service/tests/unit/test_delta_service.py`
- [ ] T069 [P] [US3] Unit test: `direction` resolves to `improved` when body_fat_percentage decreases for goal `lose_body_fat`, and `declined` when it increases in `services/analytics-service/tests/unit/test_delta_service.py`
- [ ] T070 [P] [US3] Integration test: `GET /api/analytics/dashboard` with two scans returns correct delta structure in `services/analytics-service/tests/integration/test_analytics_router.py`
- [ ] T071 [P] [US3] Integration test: `GET /api/analytics/dashboard` with zero scans returns 204 in `services/analytics-service/tests/integration/test_analytics_router.py`
- [ ] T072 [P] [US3] E2E test: dashboard page loads for user with two scans and shows metric cards with delta values in `frontend/tests/e2e/test_dashboard.spec.ts`

### Implementation for User Story 3

- [x] T073 [P] [US3] Create `AnalyticsDashboardCache` SQLAlchemy model (id UUID PK, user_id UUID UNIQUE, dashboard_json TEXT, generated_at DATETIME) in `services/analytics-service/src/models/dashboard_cache.py`
- [ ] T074 [US3] Generate Alembic migration — skipped: table created directly in Supabase
- [ ] T075 [P] [US3] Create internal scan-service HTTP client — not needed: analytics-service queries scan DB directly via shared session
- [ ] T076 [P] [US3] Create internal user-service HTTP client — not needed: analytics-service queries user DB directly via shared session
- [x] T077 [US3] Implement dashboard service (fetch 2 latest scans + metrics, compute per-metric deltas, determine direction based on goal type) in `services/analytics-service/src/services/analytics_service.py`
- [x] T078 [P] [US3] Create Pydantic schemas (DashboardOut, MetricDelta, ScanSummary) in `services/analytics-service/src/schemas/analytics.py`
- [x] T079 [US3] Implement analytics router `GET /api/analytics/dashboard` endpoint in `services/analytics-service/src/routers/analytics.py`
- [x] T080 [US3] Bootstrap analytics-service FastAPI app in `services/analytics-service/src/main.py`
- [x] T081 [P] [US3] Implement metric delta card component (metric name, current/previous value, delta with sign, directional arrow colored by direction) in `frontend/app/(app)/dashboard/page.tsx`
- [x] T082 [P] [US3] Implement dashboard grid (responsive grid of delta cards, scan date header, empty/single-scan states) in `frontend/app/(app)/dashboard/page.tsx`
- [x] T083 [P] [US3] Implement analytics API client (getDashboard) in `frontend/lib/api.ts`
- [x] T084 [US3] Implement dashboard page with TanStack Query, metric delta cards, and all scan states in `frontend/app/(app)/dashboard/page.tsx`

**Checkpoint**: User Story 3 fully functional — dashboard comparison renders correctly for all scan count states.

---

## Phase 6: User Story 4 — Metrics Visualization via Graphs (Priority: P2)

**Goal**: Historical scan data rendered as three distinct chart types (line trend, donut composition, segmental bar) with interactive tooltips.

**Independent Test**: User with 3+ scans sees all chart types rendering with correct data; single-scan user sees placeholders for multi-scan charts and composition donut renders.

### Tests for User Story 4 ⚠️ Write and verify these FAIL before implementing

- [ ] T085 [P] [US4] Integration test: `GET /api/analytics/metrics` returns list of available metric keys in `services/analytics-service/tests/integration/test_analytics_router.py`
- [ ] T086 [P] [US4] Integration test: `GET /api/analytics/metrics/body_fat_percentage/history` returns time-series in `services/analytics-service/tests/integration/test_analytics_router.py`
- [ ] T087 [P] [US4] Unit test (Vitest): chart transformer utilities produce correct shapes for Recharts in `frontend/lib/utils/chartTransformers.test.ts`
- [ ] T088 [P] [US4] E2E test: metrics page with 3+ scans renders all chart types in `frontend/tests/e2e/test_metrics.spec.ts`

### Implementation for User Story 4

- [x] T089 [US4] Implement metrics history service (list metric keys, get time-series per metric) in `services/analytics-service/src/services/analytics_service.py`
- [x] T090 [US4] Add metrics endpoints (`GET /api/analytics/metrics`, `GET /api/analytics/metrics/{metric_key}/history`) to analytics router
- [x] T091 [P] [US4] Implement `TrendLineChart` component (Recharts LineChart, glassmorphism card, date x-axis, tooltip) in `frontend/app/(app)/metrics/page.tsx`
- [x] T092 [P] [US4] Implement `CompositionDonutChart` component (Recharts PieChart showing fat/muscle/water breakdown) in `frontend/app/(app)/metrics/page.tsx`
- [x] T093 [P] [US4] Implement `SegmentalBarChart` component (Recharts BarChart for muscle/fat per body region) in `frontend/app/(app)/metrics/page.tsx`
- [x] T094 [P] [US4] Implement chart data transformers in `frontend/lib/chartTransformers.ts`
- [x] T095 [P] [US4] Implement analytics API client (getDashboard, getMetrics, getMetricHistory) in `frontend/lib/api.ts`
- [x] T096 [US4] Implement metrics page with metric selector tabs, all three chart types, and insufficient-data placeholders in `frontend/app/(app)/metrics/page.tsx`

**Checkpoint**: User Story 4 fully functional — all chart types render with correct data and interactive tooltips.

---

## Phase 7: User Story 5 — User Profile and Health Information (Priority: P2)

**Goal**: Full user profile management including age, sex, height, dietary restrictions, health goals, and clinically-inconsistent-goal warnings.

**Independent Test**: Create profile, set "vegetarian" restriction and "lose_body_fat" goal, verify both persist. Set a BMI-conflicting goal and verify warning response is returned.

### Tests for User Story 5 ⚠️ Write and verify these FAIL before implementing

- [ ] T097 [P] [US5] Integration test: `GET /api/users/me/profile` returns null fields for new user, populated fields after update in `services/user-service/tests/integration/test_user_router.py`
- [ ] T098 [P] [US5] Integration test: `PUT /api/users/me/goals` deactivates previous goal and creates new active goal in `services/user-service/tests/integration/test_user_router.py`
- [ ] T099 [P] [US5] Integration test: goal conflict check returns warning when BMI < 18.5 + lose_body_fat goal in `services/user-service/tests/integration/test_user_router.py`
- [ ] T100 [P] [US5] Integration test: duplicate dietary restriction returns 409 in `services/user-service/tests/integration/test_user_router.py`
- [ ] T101 [P] [US5] Integration test: `DELETE /api/users/me/restrictions/{id}` removes restriction in `services/user-service/tests/integration/test_user_router.py`
- [ ] T102 [P] [US5] E2E test: profile page saves restrictions and goal; values persist after page reload in `frontend/tests/e2e/test_profile.spec.ts`

### Implementation for User Story 5

- [x] T103 [P] [US5] Create `UserProfile` SQLAlchemy model (user_id UUID PK, age, gender, height_cm, weight_kg, updated_at) in `services/user-service/src/models/user_profile.py`
- [x] T104 [P] [US5] Create `HealthGoal` SQLAlchemy model (id UUID PK, user_id UUID indexed, goal_type VARCHAR, is_active BOOL, created_at) in `services/user-service/src/models/health_goal.py`
- [x] T105 [P] [US5] Create `DietaryRestriction` SQLAlchemy model (id UUID PK, user_id UUID indexed, restriction VARCHAR) in `services/user-service/src/models/dietary_restriction.py`
- [ ] T106 [US5] Generate Alembic migration — skipped: tables created directly in Supabase
- [ ] T107-T109 [US5] Repositories — skipped: repository pattern not used; service calls SQLAlchemy directly
- [x] T110 [US5] Implement `UserService` (profile CRUD; goal set with deactivation; restriction management) in `services/user-service/src/services/user_service.py`
- [x] T111 [P] [US5] Create Pydantic schemas (ProfileOut, ProfileUpdate, GoalOut, GoalCreate, RestrictionOut, RestrictionCreate) in `services/user-service/src/schemas/user.py`
- [x] T112 [US5] Implement user router (GET/PUT `/api/users/me/profile`, GET/PUT `/api/users/me/goal`, GET/POST `/api/users/me/restrictions`, DELETE `/api/users/me/restrictions/{id}`) in `services/user-service/src/routers/users.py`
- [x] T113 [US5] Bootstrap user-service FastAPI app in `services/user-service/src/main.py`
- [x] T114 [P] [US5] Implement profile form component (age, gender, height, weight, goal selector, dietary restrictions multi-select) in `frontend/app/(app)/profile/page.tsx`
- [x] T115 [P] [US5] Implement user API client (getProfile, updateProfile, getGoal, setGoal, getRestrictions, addRestriction, deleteRestriction) in `frontend/lib/api.ts`
- [x] T116 [US5] Implement profile page with TanStack Query mutations and toast notifications in `frontend/app/(app)/profile/page.tsx`

**Checkpoint**: User Story 5 fully functional — profile, goals, restrictions, and conflict warnings all work independently.

---

## Phase 8: User Story 6 — AI-Powered Diet Recommendations (Priority: P2)

**Goal**: Async LLM diet recommendation generation with restriction compliance, full macro/micronutrient breakdown, USDA-backed values, and browsable history.

**Independent Test**: Vegetarian user requests diet recommendation; result excludes meat/fish, includes all 11 micronutrients, macros shown with % of daily value, history endpoint returns all past recommendations.

### Tests for User Story 6 ⚠️ Write and verify these FAIL before implementing

- [ ] T117 [P] [US6] Unit test: `PromptBuilder.build_diet_prompt()` for vegetarian user includes restriction and excludes PII in `services/recommendation-service/tests/unit/test_prompt_builder.py`
- [ ] T118 [P] [US6] Unit test: prompt builder includes USDA nutritional context in `services/recommendation-service/tests/unit/test_prompt_builder.py`
- [ ] T119 [P] [US6] Unit test: `MacroCalculator.calculate()` returns correct targets for given body composition + goal in `services/recommendation-service/tests/unit/test_macro_calculator.py`
- [ ] T120 [P] [US6] Integration test: `POST /api/recommendations/diet/generate` returns 201 + recommendation in `services/recommendation-service/tests/integration/test_recommendations_router.py`
- [ ] T121 [P] [US6] Integration test: diet generation without active scan returns 400 in `services/recommendation-service/tests/integration/test_recommendations_router.py`
- [ ] T122 [P] [US6] Integration test: `GET /api/recommendations/diet` returns list of past recommendations in `services/recommendation-service/tests/integration/test_recommendations_router.py`
- [ ] T123 [P] [US6] Integration test: `GET /api/recommendations/food/search?q=chicken` returns USDA food results in `services/recommendation-service/tests/integration/test_recommendations_router.py`
- [ ] T124 [P] [US6] E2E test: recommendations page generates diet plan, displays macro targets, USDA food search works in `frontend/tests/e2e/test_recommendations.spec.ts`

### Implementation for User Story 6

- [x] T125 [P] [US6] Create `DietRecommendation` SQLAlchemy model (id UUID PK, user_id UUID indexed, scan_id UUID, goal_type VARCHAR, llm_response TEXT, structured_plan TEXT, edited_plan TEXT nullable, created_at DATETIME) in `services/recommendation-service/src/models/diet_recommendation.py`
- [x] T126 [P] [US6] Create `NutritionalFood` SQLAlchemy model (id UUID PK, fdc_id INT UNIQUE, food_name VARCHAR, macro fields per 100g, nutrients_json TEXT) in `services/recommendation-service/src/models/nutritional_food.py`
- [ ] T127 [US6] Generate Alembic migration — skipped: tables created directly in Supabase
- [ ] T128-T129 [US6] Repositories — skipped: repository pattern not used
- [x] T130 [US6] Implement `LLMClient` abstract base class with `generate(prompt: str) -> str` in `services/recommendation-service/src/llm/gemini_client.py`
- [x] T131 [US6] Implement `GeminiClient` using `google-generativeai` SDK (gemini-2.0-flash, JSON mode, markdown-fence stripping fix) in `services/recommendation-service/src/llm/gemini_client.py`
- [x] T132 [US6] Implement diet and workout prompt builders in `services/recommendation-service/src/services/prompt_builder.py`
- [x] T133 [US6] Implement USDA FoodData Central food search (async httpx calls to public API, no local cache needed) in `services/recommendation-service/src/services/food_search.py`
- [x] T134 [US6] Implement `MacroCalculator` using Mifflin-St Jeor BMR formula, goal-based TDEE multiplier, macro split in `services/recommendation-service/src/services/macro_calculator.py`
- [x] T135 [US6] Implement `POST /api/recommendations/diet/generate` synchronous endpoint returning completed recommendation in `services/recommendation-service/src/routers/recommendations.py`
- [x] T136 [P] [US6] Create complete recommendation schemas (MacroRequest/Out, FoodResultOut, DietRecommendationOut with edited_plan, GenerateDietRequest) in `services/recommendation-service/src/schemas/recommendation.py`
- [x] T137 [US6] Implement diet endpoints (POST `/diet/generate`, PATCH `/diet/{id}`, GET `/diet`) in `services/recommendation-service/src/routers/recommendations.py`
- [x] T138 [US6] Bootstrap recommendation-service FastAPI app with all model imports and `handler = Mangum(app)` in `services/recommendation-service/src/main.py`
- [x] T139 [P] [US6] Implement macro targets display (stat cards for protein/carbs/fat/calories) in `frontend/app/(app)/recommendations/page.tsx`
- [x] T140 [P] [US6] Implement USDA food search with debounced input, food result cards, quantity scaling, and macro preview in `frontend/app/(app)/recommendations/page.tsx`
- [x] T141 [P] [US6] Implement macro progress sidebar (progress bars showing current meal vs daily targets) in `frontend/app/(app)/recommendations/page.tsx`
- [x] T142 [P] [US6] Implement complete recommendations API client (all diet, food, meal, day-plan, split, workout functions) in `frontend/lib/api.ts`
- [x] T143 [US6] Implement unified 4-tab recommendations page (Diet, Food & Meals, Day Planner, Workout) in `frontend/app/(app)/recommendations/page.tsx`

**Checkpoint**: User Story 6 fully functional — end-to-end diet recommendation generation with restriction compliance, full nutritional display, and browsable history.

---

## Phase 9: User Story 7 — AI-Powered Workout Recommendations (Priority: P3)

**Goal**: Async LLM workout plan generation aligned to user's goal, with weekly plan structure and browsable history.

**Independent Test**: User with "gain_muscle_mass" goal gets a plan emphasizing resistance training with sets/reps; "lose_body_fat" user gets cardio-focused plan. History endpoint returns all past plans.

### Tests for User Story 7 ⚠️ Write and verify these FAIL before implementing

- [ ] T144 [P] [US7] Unit test: workout prompt for `gain_muscle_mass` includes "resistance"/"strength" keywords in `services/recommendation-service/tests/unit/test_prompt_builder.py`
- [ ] T145 [P] [US7] Integration test: `POST /api/recommendations/workout/generate` returns 201 for user with active scan in `services/recommendation-service/tests/integration/test_recommendations_router.py`
- [ ] T146 [P] [US7] Integration test: `GET /api/recommendations/workout` returns list of past workout recommendations in `services/recommendation-service/tests/integration/test_recommendations_router.py`
- [ ] T147 [P] [US7] E2E test: workout tab displays weekly plan with exercises grouped by day in `frontend/tests/e2e/test_recommendations.spec.ts`

### Implementation for User Story 7

- [x] T148 [P] [US7] Create `WorkoutRecommendation` SQLAlchemy model (id UUID PK, user_id UUID indexed, scan_id UUID, goal_type VARCHAR, llm_response TEXT, structured_plan TEXT, edited_plan TEXT nullable, created_at DATETIME) in `services/recommendation-service/src/models/workout_recommendation.py`
- [ ] T149 [US7] Generate Alembic migration — skipped: table created directly in Supabase
- [ ] T150 [P] [US7] Create `WorkoutRecommendationRepository` — skipped: repository pattern not used
- [x] T151 [US7] Implement workout prompt builder (constructs structured prompt from scan metrics + goal_type; instructs LLM to return structured 7-day plan JSON) in `services/recommendation-service/src/services/prompt_builder.py`
- [x] T152 [US7] Implement workout recommendation service (validate preconditions, build prompt, call GeminiClient, parse JSON, save) in `services/recommendation-service/src/services/recommendation_service.py`
- [x] T153 [US7] Implement `POST /api/recommendations/workout/generate` synchronous endpoint returning completed plan in `services/recommendation-service/src/routers/recommendations.py`
- [x] T154 [P] [US7] Create workout recommendation schemas (GenerateWorkoutRequest, WorkoutRecommendationOut with edited_plan) in `services/recommendation-service/src/schemas/recommendation.py`
- [x] T155 [US7] Add workout endpoints (POST `/workout/generate`, PATCH `/workout/{id}`, GET `/workout`) to recommendations router
- [x] T156 [P] [US7] Implement workout day card component (day label, exercises list with sets/reps/weight/intensity) in `frontend/app/(app)/recommendations/page.tsx`
- [x] T157 [P] [US7] Implement workout API client (generateWorkout, editWorkoutPlan, listWorkout) in `frontend/lib/api.ts`
- [x] T158 [US7] Implement workout tab on unified recommendations page (AI generate, editable plan accordion, workout history) in `frontend/app/(app)/recommendations/page.tsx`

**Checkpoint**: User Story 7 fully functional — workout plans generate, display correctly by goal type, and history is browsable.

---

## Phase 10: User Story 8 — Admin Portal: User Management (Priority: P3)

**Goal**: Admin-only portal for creating and managing user accounts with strict health-data isolation.

**Independent Test**: Regular user gets 403 on all admin endpoints; admin creates a new user; new user logs in; admin cannot see new user's health data via any endpoint.

### Tests for User Story 8 ⚠️ Write and verify these FAIL before implementing

- [ ] T159 [P] [US8] Integration test: regular user JWT receives 403 on `GET /api/admin/users` in `services/admin-service/tests/integration/test_admin_router.py`
- [ ] T160 [P] [US8] Integration test: `POST /api/admin/users` creates account; new user can login via auth-service in `services/admin-service/tests/integration/test_admin_router.py`
- [ ] T161 [P] [US8] Integration test: `GET /api/admin/users` response objects contain only safe fields — no health-data fields in `services/admin-service/tests/integration/test_admin_router.py`
- [ ] T162 [P] [US8] Integration test: `PATCH /api/admin/users/{id}` with `is_active: false` prevents subsequent login in `services/admin-service/tests/integration/test_admin_router.py`
- [ ] T163 [P] [US8] E2E test: admin login redirects to `/admin`; admin can see user list in `frontend/tests/e2e/test_admin.spec.ts`

### Implementation for User Story 8

- [x] T164 [P] [US8] Create internal auth-service HTTP client (create_user, list_users, update_user, delete_user) in `services/admin-service/src/services/admin_service.py`
- [x] T165 [P] [US8] Create Pydantic schemas (UserOut, CreateUserRequest, UpdateUserRequest) in `services/admin-service/src/schemas/admin.py`
- [x] T166 [US8] Implement `AdminService` (proxy calls to auth-service; guards: cannot delete last admin or own account) in `services/admin-service/src/services/admin_service.py`
- [x] T167 [US8] Implement admin router (GET `/api/admin/users`, POST `/api/admin/users`, PATCH `/api/admin/users/{id}`, DELETE `/api/admin/users/{id}`) with `require_admin` dependency in `services/admin-service/src/routers/admin.py`
- [x] T168 [US8] Bootstrap admin-service FastAPI app in `services/admin-service/src/main.py`
- [x] T169 [P] [US8] Implement user management table (username, role badge, active status, deactivate/delete actions) in `frontend/app/admin/page.tsx`
- [x] T170 [P] [US8] Implement create user form (username, password, is_admin toggle, submit with loading) in `frontend/app/admin/page.tsx`
- [x] T171 [P] [US8] Implement admin API client (listUsers, createUser, updateUser, deleteUser) in `frontend/lib/api.ts`
- [x] T172 [US8] Implement admin portal page (user table, create user dialog, confirmation modals) in `frontend/app/admin/page.tsx`

**Checkpoint**: All user stories are now independently functional and complete.

---

## Phase 11: Polish, Deployment & Cross-Cutting Concerns

**Purpose**: Navigation, UX polish, observability, security hardening, and Vercel deployment readiness.

### Vercel Deployment Preparation

- [x] T173 [P] Implement `SupabaseStorageClient` in `services/scan-service/src/storage/supabase_storage.py` — methods: `upload_pdf(user_id, scan_date, pdf_bytes) -> path`, `upload_csv(user_id, scan_date, csv_bytes) -> path`, `get_signed_url(path) -> url`; `scan-pdfs` bucket created in Supabase
- [ ] T174 [P] Configure `next.config.ts` for Vercel: add `images.remotePatterns` for Supabase Storage domain; configure `NEXT_PUBLIC_*` env vars
- [x] T175 [P] Add CORS middleware to all 6 FastAPI services reading `ALLOWED_ORIGINS` env var; configured in all `main.py` files
- [x] T176 [P] `.env.example` contains all required Supabase keys and `ALLOWED_ORIGINS`; `.gitignore` excludes `.env`
- [ ] T177 [P] Create `docs/deployment.md`: step-by-step Vercel-only deployment guide

### Navigation & UX

- [x] T179 Implement shared app layout with glassmorphism sidebar navigation (links to dashboard, metrics, recommendations, profile, scans; active state highlighting; logout button) in `frontend/app/(app)/layout.tsx`
- [ ] T180 [P] Implement skeleton loading components for dashboard, metrics, and recommendation pages in `frontend/components/ui/skeletons/`
- [ ] T181 [P] Implement `DisclaimerBanner` component (health disclaimer: "Not a medical device — consult a professional") on diet and workout recommendation pages
- [ ] T182 [P] Implement React error boundary wrapping all major page sections in `frontend/components/ErrorBoundary.tsx`

### Observability & Security Hardening

- [ ] T183 [P] Add structured JSON logging to all FastAPI services: log request method, path, user_id (from JWT), response status, duration; never log PII or raw health metric values
- [ ] T184 [P] Audit all repository `SELECT` queries across all 5 DB services to confirm every query includes `WHERE user_id = :current_user_id` scope filter (security hardening per constitution Principle V)
- [ ] T185 [P] Audit all list endpoints to confirm pagination (`limit`/`offset`) is present and a maximum page size is enforced on every paginated route

### Infrastructure Finalization

- [ ] T185 Create `scripts/seed-usda-data.sh` that runs the USDA sync script (`python -m services.recommendation-service.src.usda.sync_usda`) to pre-populate the nutritional food cache; document in `quickstart.md` as a one-time setup step
- [ ] T186 Create `scripts/test-all-services.sh` that runs pytest for all 5 backend services sequentially and reports pass/fail per service
- [ ] T187 Run the full `quickstart.md` validation checklist against the locally running stack (`scripts/start-local.sh` + `next dev`) and resolve any failures before first Vercel deployment

---

---

## Phase 12: Extended Features (Beyond Original Spec) ✅ All Completed

**Purpose**: Features added during development that exceeded the original spec — custom meal planning, workout split management, plan editing, and infrastructure bug fixes.

### Infrastructure Fixes

- [x] T200 Fix `DuplicatePreparedStatementError` from Supabase pgbouncer transaction mode: add `NullPool` + `prepared_statement_name_func: lambda: f"__asyncpg_{uuid4()}__"` to `shared/python/db_utils/session.py`
- [x] T201 Remove `Base.metadata.create_all` from all 5 service lifespan functions — tables managed in Supabase directly; `create_all` caused `DuplicatePreparedStatementError` on startup via sync dialect path
- [x] T202 Fix Gemini 2.0 Flash JSON wrapping: add `_strip_markdown()` in `services/recommendation-service/src/llm/gemini_client.py` to strip ` ```json ``` ` fences before parsing

### InBody CSV Support

- [x] T203 Implement full InBody CSV extractor supporting real-device export format: 14-digit compact timestamps (`YYYYMMDDHHmmss`), lb→kg (×0.453592) and kJ→kcal (÷4.184) unit conversions, BOM stripping, `-` null handling, tabular and key-value layouts in `services/scan-service/src/services/csv_extractor.py`
- [x] T204 Add `POST /api/scans/upload-csv` endpoint with optional `scan_date` form field — resolves date from: form field → CSV-embedded date → today in `services/scan-service/src/routers/scans.py`
- [x] T205 Add `upload_csv()` to Supabase storage client storing CSV files at `scans/{user_id}/{scan_date}.csv` in `services/scan-service/src/storage/supabase_storage.py`

### Custom Meal System

- [x] T206 Create `CustomMeal` and `CustomMealItem` SQLAlchemy models with CASCADE delete in `services/recommendation-service/src/models/custom_meal.py`
- [x] T207 Implement meal CRUD service (create_custom_meal, get_custom_meals, get_custom_meal, get_meal_items, update_custom_meal, delete_custom_meal) in `services/recommendation-service/src/services/meal_service.py`
- [x] T208 Add meal endpoints (POST/GET/PATCH/DELETE `/api/recommendations/meals`, GET `/api/recommendations/meals/{id}`) to recommendations router
- [x] T209 Implement food search tab (debounced USDA search, add-to-current-meal with quantity scaling, macro progress bars vs targets, save current meal as named custom meal) in `frontend/app/(app)/recommendations/page.tsx`
- [x] T210 Implement saved meals list with delete capability in `frontend/app/(app)/recommendations/page.tsx`

### Day Planner

- [x] T211 Create `DayPlan` and `DayPlanEntry` SQLAlchemy models (plan_date, meal_slot, macro totals, items_snapshot JSON) in `services/recommendation-service/src/models/day_plan.py`
- [x] T212 Implement day plan CRUD service (create_day_plan, get_day_plans, get_day_plan, get_day_plan_entries, delete_day_plan) in `services/recommendation-service/src/services/meal_service.py`
- [x] T213 Add day-plan endpoints (POST/GET/DELETE `/api/recommendations/day-plans`) to recommendations router
- [x] T214 Implement day planner tab (date + name input, meal slot selectors from saved meals, running macro totals vs daily targets, saved plans list) in `frontend/app/(app)/recommendations/page.tsx`

### Workout Split Builder

- [x] T215 Create `WorkoutSplit`, `WorkoutSplitDay`, and `WorkoutExercise` SQLAlchemy models with CASCADE delete in `services/recommendation-service/src/models/workout_split.py`
- [x] T216 Implement evidence-based workout quality scoring algorithm (5 dimensions: muscle coverage 25pts, weekly volume 30pts, push/pull balance 20pts, cardio 15pts, training frequency 10pts) returning 0–100 score with label, feedback list, covered/missing muscle groups in `services/recommendation-service/src/services/workout_scorer.py`
- [x] T217 Implement split CRUD service with automatic scoring on create/retrieve in `services/recommendation-service/src/services/split_service.py`
- [x] T218 Add split endpoints (POST/GET/DELETE `/api/recommendations/splits`, GET `/api/recommendations/splits/{id}`, POST `/api/recommendations/splits/score`) to recommendations router
- [x] T219 Implement workout split builder UI (7-day week, exercise input with sets/reps/weight/rest/notes, live quality score preview debounced 700ms, muscle coverage feedback) in `frontend/app/(app)/recommendations/page.tsx`
- [x] T220 Implement saved splits list with quality score badges in `frontend/app/(app)/recommendations/page.tsx`

### Editable LLM Plans

- [x] T221 Add `edited_plan TEXT nullable` column to `diet_recommendations` and `workout_recommendations` tables in Supabase
- [x] T222 Add `edited_plan: Mapped[str | None]` field to `DietRecommendation` and `WorkoutRecommendation` SQLAlchemy models
- [x] T223 Implement `PATCH /api/recommendations/diet/{id}` endpoint to save user-edited plan JSON in recommendations router
- [x] T224 Implement `PATCH /api/recommendations/workout/{id}` endpoint to save user-edited workout plan JSON in recommendations router
- [x] T225 Implement editable diet plan accordion (per-day macro deviation indicator, inline text edit, save button) in `frontend/app/(app)/recommendations/page.tsx`
- [x] T226 Implement editable workout plan (weekly plan display, inline edit mode, save button) in `frontend/app/(app)/recommendations/page.tsx`

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
