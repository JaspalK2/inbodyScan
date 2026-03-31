# Research: InBody Scan Health Web Application

**Branch**: `001-inbody-scan-webapp` | **Date**: 2026-03-31
**Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

---

## Architecture Decision: Microservice Layout

**Decision**: Six FastAPI microservices behind a Traefik API gateway, orchestrated with Docker Compose.

**Rationale**: The user explicitly requested microservice architecture. Each service owns its own SQLite database, which maps cleanly to Supabase schemas during migration. Docker Compose provides a single-command local dev environment. Traefik handles routing with zero-config service discovery via Docker labels.

**Services**:

| Service | Port | Responsibility | Database |
|---------|------|----------------|----------|
| auth-service | 8001 | Login, JWT issue/verify, password | auth.db |
| user-service | 8002 | Profile, health goals, dietary restrictions | user.db |
| scan-service | 8003 | PDF upload, InBody metric extraction | scan.db |
| analytics-service | 8004 | Dashboard deltas, historical aggregation | analytics.db |
| recommendation-service | 8005 | LLM diet + workout plan generation | recommendation.db |
| admin-service | 8006 | Admin account management (delegates to auth-service) | — |

**Alternatives considered**: Modular monolith — simpler but does not satisfy the explicit requirement and creates coupling that makes future feature extraction harder.

---

## Backend Framework

**Decision**: FastAPI 0.134+ (Python 3.12)

**License**: MIT ✅

**Rationale**: Fastest Python async web framework (15,000–20,000 req/s), async-first via ASGI, automatic OpenAPI docs per service, native Pydantic v2 integration. 38% Python developer adoption (JetBrains 2025). Surpassed Flask in GitHub stars December 2025.

**Alternatives considered**: Flask (synchronous, requires Celery bolt-on for async), Django (monolithic ORM, overkill for microservices).

---

## ORM & Database

**Decision**: SQLAlchemy 2.0 async (`aiosqlite` driver for SQLite, `asyncpg` for Supabase)

**License**: MIT ✅

**Rationale**: Single ORM codebase runs on both SQLite and PostgreSQL with a connection string swap. Alembic handles migrations for both. No code changes required when migrating to Supabase.

**Migration path**:
- Dev: `sqlite+aiosqlite:///data/service.db`
- Production (Supabase): `postgresql+asyncpg://user:pass@host/db`

**Alternatives considered**: Tortoise ORM (less mature), raw asyncpg (no migration tooling).

---

## Authentication

**Decision**: PyJWT 2.x + passlib[bcrypt]

**Licenses**: MIT ✅ / BSD ✅

**Rationale**: PyJWT is actively maintained; FastAPI team deprecated python-jose recommendation in 2025. bcrypt is the current industry standard for password hashing. JWT tokens are stateless — ideal for microservice auth where each service independently verifies the token without calling auth-service on every request.

**Token strategy**: Short-lived access tokens (15 min) + long-lived refresh tokens (7 days) stored in httpOnly cookies.

**Alternatives considered**: python-jose (MIT but unmaintained), Authlib joserfc (more complex).

---

## PDF Parsing

**Decision**: pdfplumber (MIT)

**License**: MIT ✅

**Rationale**: InBody scan PDFs are structured table documents. pdfplumber's coordinate-based table extraction preserves cell boundaries and numeric values reliably. pypdf is faster (24ms vs ~100ms) but produces spacing artifacts in tables, requiring fragile post-processing.

**Extraction strategy**: Parse known InBody field positions → normalize to a `{metric_key: value}` dictionary → store raw extraction JSON for reprocessing if the parser is updated.

**Alternatives considered**: pypdf (faster but table artifacts), PyMuPDF (license complexity), Tesseract OCR (overkill for born-digital PDFs).

---

## LLM Provider

**Decision**: Google Gemini 2.0 Flash (via `google-generativeai` SDK)

**SDK License**: Apache 2.0 ✅

**Rationale**: Cheapest model tier with sufficient reasoning quality for structured dietary and workout recommendations. 1M token context window (vs Claude Haiku's 200k) is advantageous for including full nutritional datasets in prompts. Outperforms GPT-3.5-turbo on structured output tasks.

**Cost estimate** (500 users, 2 recommendation requests/month each): < $5/month at current Gemini Flash pricing.

**Prompt strategy**: Recommendations are generated from a structured prompt template that includes the user's scan metrics, profile, dietary restrictions, health goal, and a curated subset of USDA FoodData Central nutritional data. No raw PII (names, IDs) is included in prompts per the constitution's security requirement.

**Alternatives considered**:
- Claude Haiku 4.5 (MIT SDK, excellent quality, ~2× more expensive than Gemini Flash)
- GPT-5 mini (cheapest raw pricing, but no long-context window advantage)

**Note**: The LLM provider is abstracted behind a `LLMClient` interface in the recommendation service. Switching providers requires only changing the concrete implementation — not the service API.

---

## Nutritional Data Source

**Decision**: USDA FoodData Central API (public domain)

**License**: U.S. government public domain — no restrictions ✅

**Rationale**: 600,000+ foods with complete macro and micronutrient data. Free, unlimited for registered API keys. Rate limit of 1,000 req/hour is more than sufficient for <500 users. Nutritional data can be pre-cached locally (SQLite table) to reduce API calls and ensure recommendations remain available offline.

**Caching strategy**: Background job pre-fetches and stores nutritional data for the 500 most common foods. LLM prompts reference cached data by food name. API is called only for less common foods on demand.

**Alternatives considered**: Nutritionix (paid production tier), Edamam (paid), Open Food Facts (crowdsourced, reliability concerns for health app).

---

## API Gateway

**Decision**: `vercel.json` routing (production) + direct service ports (local dev)

**License**: N/A (Vercel platform config)

**Rationale**: Vercel is the sole deployment target. `vercel.json` rewrites route incoming requests to the correct FastAPI serverless function by path prefix — zero additional infrastructure required. In local development, each FastAPI service runs on its own port (`uvicorn --port 800X`) and the frontend points to each service directly via `NEXT_PUBLIC_{SERVICE}_URL` env vars.

**Production routing rules** (in `vercel.json`):
- `/api/auth/*` → auth-service (`services/auth-service/src/main.py`)
- `/api/users/*` → user-service
- `/api/scans/*` → scan-service
- `/api/analytics/*` → analytics-service
- `/api/recommendations/*` → recommendation-service
- `/api/admin/*` → admin-service
- `/*` → Next.js frontend

**Alternatives considered**: Traefik (Docker-native, ideal for container deployments; not needed since we deploy to Vercel), Nginx (same issue).

---

## Async Task Processing

**Decision**: No async queue — synchronous async FastAPI request/response

**Rationale**: Vercel serverless functions do not support long-running background workers (no Celery, no Redis broker). PDF extraction completes in ~2 seconds; LLM recommendation generation completes in ~8 seconds. Both fit comfortably within Vercel's 60-second function timeout (Pro plan). Operations are implemented as standard `async def` FastAPI endpoints — the HTTP request simply takes 2–10 seconds and the frontend shows a loading spinner during that time. On completion, the response is returned directly with the result.

**UX impact**: Instead of a job-polling pattern, the frontend awaits the HTTP response with a loading state. If the function times out (>60s), a standard HTTP 504 is returned and the frontend shows an error with a retry button. This is simpler, more reliable, and requires no additional infrastructure.

**Alternatives considered**: Celery + Redis (cannot run on Vercel), Vercel Background Functions (Pro feature, adds complexity, not needed given operation durations).

---

## Frontend Framework

**Decision**: Next.js 15 (App Router) + TypeScript 5.x

**License**: MIT ✅

**Rationale**: Industry-leading React framework. App Router enables Server Components for fast initial load (health data fetched server-side) and Client Components for interactive charts and forms. Built-in image optimization, route protection via middleware, and strong TypeScript integration.

**Alternatives considered**: Next.js 16 (very recent, fewer community examples), Remix (smaller ecosystem), SvelteKit (less React ecosystem compatibility with shadcn/ui).

---

## UI Component Library

**Decision**: shadcn/ui (Radix UI + Tailwind CSS 3.x)

**License**: MIT ✅

**Rationale**: Components are copied into the project — no library version lock-in. Built on Radix UI primitives (fully accessible). Tailwind CSS integration means design tokens (colors, spacing, typography) are defined in `tailwind.config.ts` and propagate everywhere. The `shadcn/ui` chart components (built on Recharts) provide all chart types needed: line, bar, area, pie/donut.

**Alternatives considered**: Material-UI (heavier bundle, different aesthetic), Headless UI (requires more styling work from scratch).

---

## Data Visualization

**Decision**: Recharts 2.x via shadcn/ui chart components

**License**: MIT ✅

**Chart types used**:
- **Line chart**: Body fat %, skeletal muscle mass trend over time
- **Area chart**: Total body water, BMI trend
- **Bar chart**: Segmental muscle/fat analysis per body region
- **Radial/donut chart**: Body composition breakdown (fat vs muscle vs water %)
- **Comparison cards**: Current vs previous scan delta with directional indicators

**Alternatives considered**: Tremor (built on Recharts, MIT, but adds bundle weight; shadcn/ui charts cover the same territory), Chart.js (requires wrapper, less idiomatic with React).

---

## Client Data Fetching

**Decision**: TanStack Query v5 + Next.js Server Components (hybrid)

**License**: MIT ✅

**Pattern**:
- Server Components: Initial page load data (dashboard, profile) — no client JS cost
- TanStack Query: Mutations (upload scan, generate recommendation), infinite lists (scan history), optimistic updates (profile edits), background sync

**Alternatives considered**: SWR (simpler but less powerful for complex dashboards), pure Server Components (cannot handle real-time mutations or background sync).

---

## Testing Stack

**Decision**: pytest + pytest-asyncio (backend), Vitest + React Testing Library (frontend), Playwright (E2E)

**Licenses**: MIT ✅ (all three)

**Per constitution Principle IV**: Tests are MANDATORY. All service endpoints, PDF extraction flows, LLM prompt builders, and data access patterns require tests. E2E tests cover all P1 and P2 user stories.

---

## UI Design Theme

**Decision**: PENDING USER SELECTION — four options presented in plan.md

The color palette is configured entirely via Tailwind CSS design tokens in `tailwind.config.ts`. Selecting a theme requires no component code changes — only the token values differ.

---

## Supabase Migration Path

When ready to migrate from SQLite to Supabase:

1. Provision a Supabase project; obtain the PostgreSQL connection string.
2. For each service, change `DATABASE_URL` in the environment from `sqlite+aiosqlite:///data/service.db` to `postgresql+asyncpg://...`.
3. Run `alembic upgrade head` against the Supabase database to apply all existing migrations.
4. Supabase RLS (Row Level Security) policies can optionally replace the application-level user-scoped filtering — though the application-level filters are retained as a defense-in-depth measure per the constitution's security rules.
5. No SQLAlchemy model code changes are required.
