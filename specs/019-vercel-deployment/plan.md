# Implementation Plan: Deploy App to Vercel

**Branch**: `019-vercel-deployment` | **Date**: 2026-04-06 | **Spec**: [spec.md](spec.md)

## Summary

Deploy the entire InBody Scan Analyzer — Next.js frontend + all 6 FastAPI backend services — to a single Vercel project using the existing `vercel.json` skeleton. Key changes: update `vercel.json` with `includeFiles` (so each Python function bundles its `requirements.txt` and the shared library), add a 30s `maxDuration` for the recommendation service, add health-check endpoints to all 6 services, write a `DEPLOYMENT.md` guide, and document production env vars.

**No CORS changes needed** — all traffic is same-origin in production (frontend and APIs live on the same Vercel domain). **`NEXT_PUBLIC_*_URL` = empty string in production** so API paths resolve to the same domain.

---

## Technical Context

| Concern | Detail |
|---------|--------|
| Frontend | Next.js 15, `@vercel/next` builder, root at `frontend/` |
| Backend | 6 × FastAPI + Mangum, `@vercel/python` builder |
| Python version | Vercel supports Python 3.9–3.12 (NOT 3.13); services must target 3.12 in `vercel.json` `functions` config |
| Shared library | `shared/python/db_utils/` — must be included in every Python function via `includeFiles` |
| Requirements | Each service has `requirements.txt` at service root; must be included via `includeFiles` per build |
| Function size limit | 250MB unzipped per function; recommendation-service (google-generativeai + groq) is at risk |
| Timeout | Default 10s; recommendation-service plan generation needs 30s (`maxDuration`) |
| Connection pooling | Each serverless invocation creates a new asyncpg connection; `statement_cache_size=0` already set for Supabase pgbouncer compatibility |
| Lifespan | All services use `Mangum(app, lifespan="off")` — correct for serverless |

---

## Constitution Check

| Principle | Gate | Status |
|-----------|------|--------|
| I. Extensibility | vercel.json and DEPLOYMENT.md are additive; no existing interfaces modified | ✅ |
| II. Algorithm Efficiency | No algorithm changes | ✅ |
| III. License Compliance | No new dependencies | ✅ |
| IV. Mandatory Tests | Health endpoint tests added; deployment smoke test documented in quickstart.md | ✅ |
| V. UI/UX Consistency | No UI changes | ✅ |
| Security | Secrets in Vercel env vars (encrypted); `.env.local` already in `.gitignore`; `DEPLOYMENT.md` explicitly warns against committing secrets | ✅ |

---

## File Structure

```
vercel.json                                  ← UPDATE: add includeFiles, maxDuration, Python version
DEPLOYMENT.md                                ← NEW: step-by-step deployment guide
frontend/.env.production                     ← NEW: documents NEXT_PUBLIC_*_URL="" for production

services/auth-service/src/main.py            ← ADD: GET /api/auth/health
services/user-service/src/main.py            ← ADD: GET /api/users/health
services/scan-service/src/main.py            ← ADD: GET /api/scans/health
services/analytics-service/src/main.py      ← ADD: GET /api/analytics/health
services/recommendation-service/src/main.py ← ADD: GET /api/recommendations/health
services/admin-service/src/main.py          ← ADD: GET /api/admin/health
```

---

## Phase 1: Update vercel.json

**Target file**: `/vercel.json`

Replace the existing minimal vercel.json with the full production config:

```json
{
  "version": 2,
  "functions": {
    "services/auth-service/src/main.py": { "runtime": "python3.12", "maxDuration": 15 },
    "services/user-service/src/main.py": { "runtime": "python3.12", "maxDuration": 15 },
    "services/scan-service/src/main.py": { "runtime": "python3.12", "maxDuration": 20 },
    "services/analytics-service/src/main.py": { "runtime": "python3.12", "maxDuration": 15 },
    "services/recommendation-service/src/main.py": { "runtime": "python3.12", "maxDuration": 30 },
    "services/admin-service/src/main.py": { "runtime": "python3.12", "maxDuration": 15 }
  },
  "builds": [
    {
      "src": "services/auth-service/src/main.py",
      "use": "@vercel/python",
      "config": {
        "includeFiles": ["services/auth-service/requirements.txt", "shared/**", "services/auth-service/src/**"]
      }
    },
    {
      "src": "services/user-service/src/main.py",
      "use": "@vercel/python",
      "config": {
        "includeFiles": ["services/user-service/requirements.txt", "shared/**", "services/user-service/src/**"]
      }
    },
    {
      "src": "services/scan-service/src/main.py",
      "use": "@vercel/python",
      "config": {
        "includeFiles": ["services/scan-service/requirements.txt", "shared/**", "services/scan-service/src/**"]
      }
    },
    {
      "src": "services/analytics-service/src/main.py",
      "use": "@vercel/python",
      "config": {
        "includeFiles": ["services/analytics-service/requirements.txt", "shared/**", "services/analytics-service/src/**"]
      }
    },
    {
      "src": "services/recommendation-service/src/main.py",
      "use": "@vercel/python",
      "config": {
        "includeFiles": ["services/recommendation-service/requirements.txt", "shared/**", "services/recommendation-service/src/**"]
      }
    },
    {
      "src": "services/admin-service/src/main.py",
      "use": "@vercel/python",
      "config": {
        "includeFiles": ["services/admin-service/requirements.txt", "shared/**", "services/admin-service/src/**"]
      }
    },
    {
      "src": "frontend/package.json",
      "use": "@vercel/next"
    }
  ],
  "routes": [
    { "src": "/api/auth/(.*)", "dest": "services/auth-service/src/main.py" },
    { "src": "/api/users/(.*)", "dest": "services/user-service/src/main.py" },
    { "src": "/api/scans/(.*)", "dest": "services/scan-service/src/main.py" },
    { "src": "/api/analytics/(.*)", "dest": "services/analytics-service/src/main.py" },
    { "src": "/api/recommendations/(.*)", "dest": "services/recommendation-service/src/main.py" },
    { "src": "/api/admin/(.*)", "dest": "services/admin-service/src/main.py" },
    { "src": "/(.*)", "dest": "frontend" }
  ]
}
```

**Note on Python version**: Vercel supports Python 3.9, 3.10, 3.11, 3.12. The services use Python 3.13 locally but `python3.12` is specified for Vercel. The code is compatible with 3.12 (no 3.13-specific syntax used).

---

## Phase 2: Add Health-Check Endpoints

Add to each service's `main.py` after the existing middleware setup and before `include_router` calls:

```python
@app.get("/api/<service>/health")
async def health():
    return {"status": "ok", "service": "<service-name>"}
```

Specific endpoints per service:
- auth-service: `GET /api/auth/health`
- user-service: `GET /api/users/health`
- scan-service: `GET /api/scans/health`
- analytics-service: `GET /api/analytics/health`
- recommendation-service: `GET /api/recommendations/health`
- admin-service: `GET /api/admin/health`

---

## Phase 3: Production env var documentation

**`frontend/.env.production`** (committed to repo — contains only public/empty values, no secrets):
```
# Production: all API calls are same-origin (Vercel monorepo)
# Set these to empty string in Vercel Dashboard → Environment Variables
NEXT_PUBLIC_AUTH_URL=
NEXT_PUBLIC_USER_URL=
NEXT_PUBLIC_SCAN_URL=
NEXT_PUBLIC_ANALYTICS_URL=
NEXT_PUBLIC_RECOMMENDATION_URL=
NEXT_PUBLIC_ADMIN_URL=
# Set this to the actual OAuth client ID
NEXT_PUBLIC_GOOGLE_CLIENT_ID=926220032336-17hu7aigdasv00f7m40g802k2rru7vpr.apps.googleusercontent.com
```

---

## Phase 4: DEPLOYMENT.md

Write `DEPLOYMENT.md` at the repo root with:
1. Prerequisites (Vercel account, GitHub repo connected)
2. Step-by-step: connect repo, set env vars (listing all required), redeploy
3. Health check verification commands
4. Smoke test steps (register, login, upload scan, generate plan)
5. Local dev (unchanged — use `.env.local`)

---

## Complexity Tracking

| Item | Complexity | Justification |
|------|-----------|---------------|
| vercel.json update | Low | Additive config; existing structure already correct |
| Health endpoints (×6) | Low | One-liner per service, no auth required |
| DEPLOYMENT.md | Low | Documentation only |
| Python 3.12 vs 3.13 | Low risk | Code uses no 3.13-specific features |
| Recommendation-service function size | Medium risk | google-generativeai + groq may approach 250MB limit; monitor build output |

---

## Rollback Plan

If the Vercel deployment fails or has issues:
- All local development remains unchanged (`localhost:800X` services)
- Revert `vercel.json` to the previous version using `git revert`
- The `DEPLOYMENT.md` and health endpoints are purely additive and cause no issues if present without Vercel
