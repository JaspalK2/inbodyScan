# Implementation Plan: InBody Scan Health Web Application

**Branch**: `001-inbody-scan-webapp` | **Date**: 2026-03-31 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-inbody-scan-webapp/spec.md`

---

## Summary

A full-stack health web application that parses InBody scan PDFs, visualizes body composition trends, and generates personalized diet and workout recommendations via a cost-efficient LLM. The architecture is microservice-based (six FastAPI services + Traefik gateway), with SQLite per service now and a zero-code-change migration path to Supabase. The frontend is Next.js 15 + shadcn/ui with a user-selected design theme (see UI Theme Options below). All dependencies are MIT/Apache/BSD licensed per the project constitution.

---

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript 5.x / Node.js 20.x (frontend)
**Primary Dependencies**:
- Backend: FastAPI 0.134+, Mangum 0.17+ (ASGI adapter for Vercel), SQLAlchemy 2.0 async, Alembic, Pydantic v2, PyJWT, passlib[bcrypt], pdfplumber, google-generativeai SDK, httpx, supabase-py (storage)
- Frontend: Next.js 15, React 19, Tailwind CSS 3.x, shadcn/ui, Recharts 2.x, TanStack Query v5, React Hook Form, Zod
- Infrastructure: Docker Compose v2 (local dev only, optional), `vercel.json` (production routing)

**Storage**:
- All environments (local dev and production): Supabase PostgreSQL via `asyncpg` driver from day one — no SQLite, no migration required
- PDF files: Supabase Storage bucket `scan-pdfs` via `supabase-py` SDK in all environments

**Deployment Target**: Vercel only — frontend (Next.js) and all 6 FastAPI services deployed as Vercel serverless Python functions via the Mangum ASGI adapter. No Railway, Render, or other platform. Tested fully locally before every Vercel deployment. Local dev connects to Supabase directly (user provides API keys).

**Async strategy**: No Celery or Redis. PDF extraction (~2s) and LLM calls (~8s) are handled as synchronous async FastAPI requests. Both fit well within Vercel's 60-second function timeout (Pro) and 10-second limit (Hobby). The frontend shows a loading spinner during the HTTP request; on completion the result is rendered directly.

**Testing**: pytest + pytest-asyncio (backend), Vitest + React Testing Library (frontend unit), Playwright (E2E — runs against local stack before deployment)

**Target Platform**: Web application — modern desktop and mobile browsers; Vercel serverless deployment

**Project Type**: Microservice web application (6 FastAPI backends + Next.js frontend, all on Vercel)

**Performance Goals**: Dashboard load < 10s; PDF extraction < 30s; recommendation generation < 60s; auth/profile/analytics endpoints < 500ms p95

**Constraints**: < 500 users v1; LLM cost < $50/month; all dependencies MIT/Apache/BSD; no PII in LLM prompts; all operations within Vercel 60s function timeout; Supabase free tier limits (500 MB DB, 1 GB storage, 50k MAU) sufficient for v1

**Scale/Scope**: < 500 users, 6 microservices, ~15 UI screens

---

## UI Theme Options

> **ACTION REQUIRED**: Select one of the four themes below. Reply with the option letter (A, B, C, or D) or describe a custom preference. The theme is implemented via Tailwind CSS design tokens — only `tailwind.config.ts` and a CSS variables file change between options. No component code is affected.

All themes use shadcn/ui components (MIT), Tailwind CSS, and Inter or similar system font unless noted. All include dark/light mode support and WCAG AA contrast ratios.

---

### Option A: "Health Pro Dark" — Premium dark dashboard

Inspired by Whoop, Linear, and Vercel. Dense, professional, data-forward.

| Token | Value |
|-------|-------|
| Background | `#0F0F1A` (deep navy-black) |
| Card surface | `#1A1A2E` |
| Primary accent | `#00D4FF` (electric cyan) |
| Secondary accent | `#7C3AED` (violet) |
| Positive delta | `#22C55E` (green) |
| Negative delta | `#EF4444` (red) |
| Typography | Inter (sans-serif) |
| Border radius | 8px (subtle rounding) |

**Feel**: Serious, premium fitness tracker. Strong contrast for data readability at a glance.

---

### Option B: "Clean Wellness Light" — Clinical light mode

Inspired by Apple Health, Notion, and medical software. Approachable, trustworthy, minimal.

| Token | Value |
|-------|-------|
| Background | `#F8FAFC` (off-white) |
| Card surface | `#FFFFFF` with subtle shadow |
| Primary accent | `#6366F1` (indigo) |
| Secondary accent | `#10B981` (emerald) |
| Positive delta | `#10B981` |
| Negative delta | `#EF4444` |
| Typography | Inter (sans-serif) |
| Border radius | 12px (friendly rounding) |

**Feel**: Light, clean, medical credibility. Works well on bright screens.

---

### Option C: "Vibrant Sport" — Athletic, high-energy

Inspired by Strava, Garmin Connect, and MyFitnessPal. Bold, motivational, energetic.

| Token | Value |
|-------|-------|
| Background | `#111827` (dark gray) |
| Card surface | `#1F2937` |
| Primary accent | `#F97316` (energetic orange) |
| Secondary accent | `#22C55E` (athletic green) |
| Gradient header | `#F97316` → `#EF4444` (orange-red) |
| Typography | Plus Jakarta Sans (geometric, sporty) |
| Border radius | 6px (sharper, dynamic) |

**Feel**: Motivational, athletic. Charts feel like a sports app. Great for users who are fitness enthusiasts.

---

### Option D: "Modern Glassmorphism" — Cutting-edge SaaS aesthetic

Inspired by Supabase dashboard, Vercel, and premium SaaS products. Visually striking.

| Token | Value |
|-------|-------|
| Background | `#0D1117` → `#1A0A2E` gradient |
| Card surface | `rgba(255,255,255,0.05)` + backdrop-blur |
| Primary accent | `#A855F7` (purple) |
| Secondary accent | `#06B6D4` (cyan) |
| Glow effects | Subtle purple halo on active cards |
| Typography | Geist (Vercel's font, MIT) |
| Border radius | 10px with 1px semi-transparent borders |

**Feel**: Very modern, "wow factor". Premium tech product aesthetic. Slightly higher implementation complexity for the glassmorphism effects.

---

**Current selection**: ✅ **Option D — Modern Glassmorphism** (confirmed 2026-03-31)

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Extensibility | Each service exposes a versioned REST interface. LLM client is behind an interface (`LLMClient`) abstraction. Database layer uses SQLAlchemy repository pattern, swappable per service. New services added by adding a new Docker service + Traefik rule — zero changes to existing services. | ✅ PASS |
| II. Algorithm Efficiency | Dashboard delta computation is O(n) where n = number of metric keys (bounded ~25). Chart aggregation queries use indexed `user_id + scan_date` scans. Time-series queries are paginated. PDF extraction is async (Celery worker). LLM calls are async and non-blocking. | ✅ PASS |
| III. License Compliance | Full dependency audit below — all MIT/Apache/BSD. USDA FoodData Central is U.S. public domain. Gemini Flash API terms reviewed — usage for production app is permitted. | ✅ PASS |
| IV. Test Coverage | All service endpoints have pytest tests. PDF extraction has unit tests with fixture PDFs. LLM prompt builders have unit tests with mocked LLM responses. E2E tests cover all P1 + P2 user stories. Frontend components have Vitest tests. | ✅ PASS (required in all task generation) |
| V. UI/UX Consistency | Single design token file (`tailwind.config.ts`) drives all colors, typography, spacing. shadcn/ui provides the shared component library. Chart styling uses a single Recharts theme config. Theme is one of four pre-approved token sets. | ✅ PASS |

**License Audit** (key dependencies):

| Package | License | Verified |
|---------|---------|---------|
| FastAPI | MIT | ✅ |
| SQLAlchemy | MIT | ✅ |
| Alembic | MIT | ✅ |
| Pydantic v2 | MIT | ✅ |
| PyJWT | MIT | ✅ |
| passlib | BSD | ✅ |
| pdfplumber | MIT | ✅ |
| google-generativeai | Apache 2.0 | ✅ |
| Mangum | MIT | ✅ |
| httpx | BSD | ✅ |
| pytest | MIT | ✅ |
| pytest-asyncio | Apache 2.0 | ✅ |
| Next.js | MIT | ✅ |
| React | MIT | ✅ |
| Tailwind CSS | MIT | ✅ |
| shadcn/ui | MIT | ✅ |
| Recharts | MIT | ✅ |
| TanStack Query | MIT | ✅ |
| React Hook Form | MIT | ✅ |
| Zod | MIT | ✅ |
| supabase-py | MIT | ✅ |
| USDA FoodData Central | Public domain | ✅ |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-inbody-scan-webapp/
├── plan.md              # This file
├── research.md          # Phase 0 — tech stack decisions
├── data-model.md        # Phase 1 — entity definitions per service
├── quickstart.md        # Phase 1 — local dev setup
├── contracts/
│   └── api-contracts.md # Phase 1 — REST API contracts (all services)
└── tasks.md             # Phase 2 — generated by /speckit.tasks
```

### Source Code (repository root)

```text
inbodyScan-Analyzer/
│
├── services/
│   ├── auth-service/
│   │   ├── src/
│   │   │   ├── models/          # SQLAlchemy models (User, RefreshToken)
│   │   │   ├── repositories/    # DB access layer (UserRepository, TokenRepository)
│   │   │   ├── services/        # Business logic (AuthService)
│   │   │   ├── routers/         # FastAPI route handlers
│   │   │   ├── schemas/         # Pydantic request/response schemas
│   │   │   ├── core/            # JWT utils, password hashing, config
│   │   │   └── main.py          # FastAPI app entry point
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   └── integration/
│   │   ├── alembic/             # DB migrations
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── user-service/
│   │   ├── src/
│   │   │   ├── models/          # UserProfile, HealthGoal, DietaryRestriction
│   │   │   ├── repositories/
│   │   │   ├── services/
│   │   │   ├── routers/
│   │   │   ├── schemas/
│   │   │   └── main.py
│   │   ├── tests/
│   │   ├── alembic/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── scan-service/
│   │   ├── src/
│   │   │   ├── models/          # InBodyScan, ScanMetric
│   │   │   ├── repositories/
│   │   │   ├── services/
│   │   │   ├── parsers/         # InBody PDF extraction logic
│   │   │   ├── workers/         # Celery tasks for async extraction
│   │   │   ├── routers/
│   │   │   ├── schemas/
│   │   │   └── main.py
│   │   ├── tests/
│   │   │   ├── unit/
│   │   │   ├── integration/
│   │   │   └── fixtures/        # Sample InBody PDF files for testing
│   │   ├── alembic/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── analytics-service/
│   │   ├── src/
│   │   │   ├── models/          # DashboardCache
│   │   │   ├── repositories/
│   │   │   ├── services/        # Delta computation, trend aggregation
│   │   │   ├── clients/         # Internal HTTP clients for scan-service
│   │   │   ├── routers/
│   │   │   ├── schemas/
│   │   │   └── main.py
│   │   ├── tests/
│   │   ├── alembic/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── recommendation-service/
│   │   ├── src/
│   │   │   ├── models/          # DietRecommendation, WorkoutRecommendation, NutritionalFood
│   │   │   ├── repositories/
│   │   │   ├── services/
│   │   │   ├── llm/
│   │   │   │   ├── client.py          # LLMClient interface (abstract)
│   │   │   │   ├── gemini_client.py   # Gemini Flash implementation
│   │   │   │   └── prompt_templates/  # Versioned prompt templates
│   │   │   ├── usda/            # USDA FDC cache sync + lookup
│   │   │   ├── workers/         # Celery tasks for async LLM generation
│   │   │   ├── routers/
│   │   │   ├── schemas/
│   │   │   └── main.py
│   │   ├── tests/
│   │   ├── alembic/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── admin-service/
│       ├── src/
│       │   ├── clients/         # Internal HTTP client for auth-service
│       │   ├── routers/
│       │   ├── schemas/
│       │   └── main.py
│       ├── tests/
│       ├── Dockerfile
│       └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js 15 App Router pages
│   │   │   ├── (auth)/
│   │   │   │   └── login/
│   │   │   ├── (app)/
│   │   │   │   ├── dashboard/
│   │   │   │   ├── metrics/
│   │   │   │   ├── recommendations/
│   │   │   │   │   ├── diet/
│   │   │   │   │   └── workout/
│   │   │   │   ├── profile/
│   │   │   │   └── scans/
│   │   │   └── admin/
│   │   ├── components/
│   │   │   ├── ui/              # shadcn/ui components (copied in)
│   │   │   ├── charts/          # Recharts wrappers with theme tokens
│   │   │   ├── dashboard/       # Dashboard-specific components
│   │   │   ├── scans/           # Scan upload, scan card, metric table
│   │   │   ├── recommendations/ # Diet plan card, workout plan card
│   │   │   └── layout/          # Nav, sidebar, header
│   │   ├── lib/
│   │   │   ├── api/             # Typed API client functions
│   │   │   ├── hooks/           # TanStack Query hooks
│   │   │   └── utils/           # Formatters, validators
│   │   ├── types/               # Shared TypeScript types (mirrors API schemas)
│   │   └── styles/
│   │       ├── globals.css      # Tailwind base + CSS variables (theme tokens)
│   │       └── theme.css        # Selected theme token values
│   ├── tests/
│   │   ├── unit/                # Vitest component tests
│   │   └── e2e/                 # Playwright E2E tests
│   ├── tailwind.config.ts       # Design token definitions
│   ├── next.config.ts
│   ├── package.json
│   └── Dockerfile
│
├── shared/
│   └── python/
│       ├── auth_utils/          # JWT verification shared across services
│       └── http_client/         # Typed internal service client base
│
├── gateway/
│   └── traefik.yml              # Traefik static config
│
├── docker-compose.yml           # Production orchestration
├── docker-compose.dev.yml       # Dev overrides (volume mounts, hot reload)
├── .env.example
└── scripts/
    ├── test-all-services.sh
    └── seed-usda-data.sh        # Pre-fetch USDA nutritional cache
```

**Structure Decision**: Option 2 (web application) with multi-service expansion. Six FastAPI services each in `services/{name}/` with their own Dockerfile, requirements, and database. Frontend in `frontend/`. Shared Python utilities in `shared/python/`. Infrastructure config in `gateway/`. This structure allows each service to be developed, tested, and deployed independently while maintaining clear boundaries.

---

## Complexity Tracking

| Complexity Item | Why Needed | Simpler Alternative Rejected Because |
|-----------------|------------|-------------------------------------|
| 6 microservices instead of 1 monolith | User explicitly requested microservice architecture; each service needs isolated DB for Supabase migration path | Monolith easier to build but doesn't satisfy the stated architecture requirement and creates tight coupling as new features are added |
| Celery + Redis async queue | PDF extraction (1–3s) and LLM calls (3–10s) would block HTTP requests and risk client timeouts | Synchronous processing would cause frequent 504 timeout errors for users uploading scans or requesting recommendations |
| LLMClient interface abstraction | Allows switching from Gemini to any other provider (Haiku, GPT) with one file change | Direct Gemini SDK calls would create tight coupling; switching providers would require finding and replacing all call sites |
| Repository pattern per service | Decouples DB queries from business logic; essential for Supabase migration (only repository layer changes) | Active Record / direct SQLAlchemy session calls in routes work fine for monoliths but make testing and DB-swapping harder in microservices |

---

## Phase 0: Research — Complete

See [research.md](research.md) for all decisions and rationale.

**All NEEDS CLARIFICATION items resolved**:

| Item | Resolution |
|------|------------|
| Backend framework | FastAPI 0.134+ (MIT) |
| ORM | SQLAlchemy 2.0 async + Alembic |
| Auth library | PyJWT 2.x + passlib[bcrypt] |
| PDF parsing | pdfplumber (MIT) |
| LLM provider | Gemini 2.0 Flash (Apache 2.0 SDK) |
| Nutritional dataset | USDA FoodData Central (public domain) |
| API gateway | Traefik 3.x (MIT) |
| Async tasks | Celery + Redis |
| Frontend framework | Next.js 15 + TypeScript 5.x |
| UI component library | shadcn/ui (MIT) |
| Charts | Recharts 2.x via shadcn/ui charts |
| Data fetching | TanStack Query v5 (hybrid with Server Components) |
| Testing | pytest / Vitest / Playwright |
| UI theme | ✅ Option D — Modern Glassmorphism (dark gradient + glassmorphism cards + purple/cyan) |

---

## Phase 1: Design — Complete

| Artifact | Status | Path |
|----------|--------|------|
| Data model | ✅ | [data-model.md](data-model.md) |
| API contracts | ✅ | [contracts/api-contracts.md](contracts/api-contracts.md) |
| Quickstart | ✅ | [quickstart.md](quickstart.md) |

### Key Design Decisions

**Service boundaries**: Auth service is the single source of truth for identities. All other services receive `user_id` from the JWT and call auth-service's internal `/internal/auth/verify` endpoint only on startup health checks — not on every request (JWT is verified locally using the shared secret, stateless).

**Data isolation enforcement**: Every SQL query in every service includes `WHERE user_id = :current_user_id`. There is no code path that returns all users' data. This is tested explicitly in integration tests (constitution Principle VII compliance).

**LLM prompt safety**: The `RecommendationService` constructs prompts from a template. It includes: normalized body metrics (no names/IDs), goal type (enum string), dietary restriction list (enum strings), and USDA-cached nutritional context. No names, usernames, ages as identifiers, or database IDs are included in the prompt.

**SQLite → Supabase migration**: Each service has its own `DATABASE_URL` environment variable. Changing the URL from `sqlite+aiosqlite` to `postgresql+asyncpg` and running `alembic upgrade head` is the complete migration. No ORM code changes.

---

## Deployment Architecture (Vercel Only)

Everything runs on Vercel. No other cloud platform is used at any point. The application is always fully tested locally before deploying.

| Layer | Platform | Notes |
|-------|----------|-------|
| Frontend (Next.js 15) | **Vercel** | Native, zero-config deployment. `git push` to `main` triggers deploy. |
| Backend APIs (6 FastAPI services) | **Vercel** | Each FastAPI app wrapped with `Mangum` ASGI adapter, deployed as Vercel Python serverless functions. Routed via `vercel.json`. |
| Database (all environments) | **Supabase PostgreSQL** | Used from day one in local dev and production. User provides Supabase project URL + anon key. `DATABASE_URL=postgresql+asyncpg://...` in `.env`. |
| PDF file storage (all environments) | **Supabase Storage** | `scan-pdfs` bucket via `supabase-py` SDK. Used from day one. |

**How FastAPI runs on Vercel**:

Each FastAPI service is exposed as a Vercel Python serverless function using `Mangum`:
```python
# services/auth-service/src/main.py
from mangum import Mangum
app = FastAPI(...)
handler = Mangum(app)  # Vercel calls handler(event, context)
```

`vercel.json` at the repository root routes incoming requests:
```json
{
  "rewrites": [
    { "source": "/api/auth/(.*)", "destination": "/services/auth-service/src/main.py" },
    { "source": "/api/users/(.*)", "destination": "/services/user-service/src/main.py" },
    ...
  ]
}
```

**No Celery, no Redis**: PDF extraction and LLM calls are synchronous async operations. Both complete in well under 60 seconds (Vercel Pro limit). The frontend displays a loading state during the HTTP request; when the response arrives, results render immediately — no polling required.

**Local development workflow**:
1. Create a Supabase project (free tier); copy `DATABASE_URL`, `SUPABASE_URL`, and `SUPABASE_SERVICE_ROLE_KEY` into `.env`
2. Run `alembic upgrade head` for each service to create tables in Supabase
3. Run each service with `scripts/start-local.sh` (uvicorn on ports 8001–8006)
4. Run frontend with `npm run dev`
5. Run all tests; run Playwright E2E tests against the local stack
6. Deploy to Vercel only after all tests pass — set the same env vars in Vercel dashboard

## Next Step

Tasks generated — see [tasks.md](tasks.md). Run `/speckit.implement` to begin implementation.
