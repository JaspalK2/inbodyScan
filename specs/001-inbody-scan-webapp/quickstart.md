# Quickstart: InBody Scan Health Web Application

**Branch**: `001-inbody-scan-webapp` | **Date**: 2026-03-31

---

## Prerequisites

| Tool | Required Version | Check Command |
|------|-----------------|---------------|
| Docker Desktop | 4.x+ | `docker --version` |
| Docker Compose | v2.x (included with Docker Desktop) | `docker compose version` |
| Node.js | 20.x or 22.x | `node --version` |
| Python | 3.12+ | `python3 --version` |
| Git | any recent | `git --version` |

---

## Repository Structure

```text
inbodyScan-Analyzer/
├── services/
│   ├── auth-service/          # FastAPI — JWT auth, user accounts
│   ├── user-service/          # FastAPI — profiles, goals, restrictions
│   ├── scan-service/          # FastAPI — PDF upload, InBody extraction
│   ├── analytics-service/     # FastAPI — dashboard, metrics history
│   ├── recommendation-service/# FastAPI — LLM diet + workout plans
│   └── admin-service/         # FastAPI — admin account management
├── frontend/                  # Next.js 15 — web UI
├── gateway/                   # Traefik config
├── shared/
│   ├── python/                # Shared Pydantic models, JWT utils
│   └── typescript/            # Shared TypeScript types
├── docker-compose.yml         # Full stack orchestration
├── docker-compose.dev.yml     # Development overrides (hot reload)
└── .env.example               # Required environment variables
```

---

## 1. Clone and Configure

```bash
git clone <repo-url> inbodyScan-Analyzer
cd inbodyScan-Analyzer
cp .env.example .env
```

Edit `.env` and fill in:
```bash
# LLM
GOOGLE_API_KEY=your_gemini_api_key_here

# USDA FoodData Central
USDA_API_KEY=your_usda_fdc_api_key_here   # Free: https://fdc.nal.usda.gov/api-guide/

# JWT
JWT_SECRET_KEY=generate_a_long_random_string_here   # min 32 chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Service ports (defaults shown — change only if conflicts)
AUTH_SERVICE_PORT=8001
USER_SERVICE_PORT=8002
SCAN_SERVICE_PORT=8003
ANALYTICS_SERVICE_PORT=8004
RECOMMENDATION_SERVICE_PORT=8005
ADMIN_SERVICE_PORT=8006
FRONTEND_PORT=3000

# Redis (for Celery task queue)
REDIS_URL=redis://redis:6379/0

# Admin account (created on first boot)
INITIAL_ADMIN_USERNAME=admin
INITIAL_ADMIN_PASSWORD=ChangeMe123!
```

---

## 2. Start the Full Stack

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

This starts:
- Traefik gateway (port 80 / 443)
- Redis (internal, port 6379)
- All 6 FastAPI microservices with hot reload
- Next.js frontend with hot reload
- Celery workers for async PDF processing and LLM tasks

First boot takes ~3 minutes (Docker image builds). Subsequent starts take ~15 seconds.

---

## 3. Verify Services Are Running

```bash
# Check all containers are healthy
docker compose ps

# Expected output — all services STATUS = "healthy"
# auth-service        running (healthy)
# user-service        running (healthy)
# scan-service        running (healthy)
# analytics-service   running (healthy)
# recommendation-service  running (healthy)
# admin-service       running (healthy)
# frontend            running (healthy)
# redis               running (healthy)
# traefik             running (healthy)
```

---

## 4. Access the Application

| Interface | URL |
|-----------|-----|
| Web application | http://localhost |
| Traefik dashboard | http://localhost:8080 |
| Auth service API docs | http://localhost:8001/docs |
| User service API docs | http://localhost:8002/docs |
| Scan service API docs | http://localhost:8003/docs |
| Analytics service API docs | http://localhost:8004/docs |
| Recommendation service API docs | http://localhost:8005/docs |
| Admin service API docs | http://localhost:8006/docs |

---

## 5. First Login

On first boot, an admin account is created from `INITIAL_ADMIN_USERNAME` and `INITIAL_ADMIN_PASSWORD`.

1. Open http://localhost
2. Login with the admin credentials
3. Use the Admin Portal to create your first regular user account
4. Log out, log back in as the regular user
5. Upload an InBody scan PDF to begin

---

## 6. Running Tests

### Backend (all services)
```bash
# Run all service tests
docker compose run --rm auth-service pytest tests/ -v
docker compose run --rm user-service pytest tests/ -v
docker compose run --rm scan-service pytest tests/ -v
docker compose run --rm analytics-service pytest tests/ -v
docker compose run --rm recommendation-service pytest tests/ -v
docker compose run --rm admin-service pytest tests/ -v

# Or run all at once with a helper script
./scripts/test-all-services.sh
```

### Frontend
```bash
cd frontend
npm run test          # Vitest unit tests
npm run test:e2e      # Playwright E2E (requires full stack running)
```

---

## 7. Running Migrations

Database migrations are run automatically on service startup. To run manually:

```bash
docker compose run --rm auth-service alembic upgrade head
docker compose run --rm user-service alembic upgrade head
docker compose run --rm scan-service alembic upgrade head
docker compose run --rm analytics-service alembic upgrade head
docker compose run --rm recommendation-service alembic upgrade head
```

---

## 8. Migrating to Supabase

When ready to switch from SQLite to Supabase:

1. Create a Supabase project at supabase.com.
2. Obtain the PostgreSQL connection string for each service's schema.
3. In `.env`, update each service's `DATABASE_URL`:
   ```bash
   AUTH_DATABASE_URL=postgresql+asyncpg://user:pass@host.supabase.co:5432/postgres
   USER_DATABASE_URL=postgresql+asyncpg://user:pass@host.supabase.co:5432/postgres
   # ... (each service can use the same Postgres instance with different schemas)
   ```
4. Run `alembic upgrade head` for each service.
5. No application code changes are required.

---

## 9. Common Development Commands

```bash
# View logs for a specific service
docker compose logs -f auth-service

# Restart a single service (e.g., after config change)
docker compose restart recommendation-service

# Open a shell in a service container
docker compose exec scan-service bash

# Stop all services
docker compose down

# Stop and wipe databases (start fresh)
docker compose down -v
```

---

## 10. Validating the Quickstart

Run through this checklist to confirm the full stack is working:

- [ ] All containers report `healthy` in `docker compose ps`
- [ ] Login page is accessible at http://localhost
- [ ] Admin login works with `INITIAL_ADMIN_USERNAME` credentials
- [ ] Admin can create a new user from the admin portal
- [ ] New user can log in and see an empty dashboard
- [ ] New user can complete their profile (age, height, goal)
- [ ] New user can upload an InBody scan PDF (use a test PDF from `tests/fixtures/`)
- [ ] Dashboard shows scan metrics after upload completes
- [ ] Diet recommendation generates without errors
- [ ] All service API docs load at `/docs` paths
- [ ] `./scripts/test-all-services.sh` passes with no failures
