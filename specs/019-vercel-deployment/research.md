# Research: Deploy App to Vercel

**Branch**: `019-vercel-deployment`  
**Date**: 2026-04-06

---

## Decision 1: Unified Vercel Deployment (Frontend + All 6 Backends on One Project)

**Decision**: Deploy everything — Next.js frontend and all 6 FastAPI services — to a single Vercel project using the existing `vercel.json` at the repo root, which already defines `@vercel/python` builds and route rules.

**Rationale**: A `vercel.json` already exists at the repo root with `@vercel/python` builds for all 6 services and a `@vercel/next` build for the frontend. Routes map `/api/auth/*` → auth service, `/api/users/*` → user service, etc., and `/*` → frontend. All services already have `mangum` installed for the ASGI adapter. This means:
- No separate backend hosting platform (Railway/Render/Fly) is needed
- All API calls are same-origin (no CORS issues at all in production)
- One GitHub → Vercel connection deploys everything

**Key finding**: Since all services and the frontend live under the same Vercel domain (`https://<project>.vercel.app`), the `NEXT_PUBLIC_*_URL` environment variables should be set to **empty string `""`** in production. The frontend already constructs URLs as `${NEXT_PUBLIC_AUTH_URL}/api/auth/login` — with an empty base URL, this becomes `/api/auth/login` which resolves to the same origin, hitting the Vercel route correctly.

**Alternatives considered**:
- Separate Railway/Render for backends: unnecessary overhead given the existing `vercel.json`
- Keeping `NEXT_PUBLIC_*_URL` as the Vercel domain: works but empty string is cleaner and avoids hardcoding the domain

---

## Decision 2: `requirements.txt` Placement for Vercel Python Runtime

**Decision**: Each service needs a `requirements.txt` symlink or copy at `services/<service>/src/requirements.txt` OR the `vercel.json` must specify `includeFiles` to pull in the parent directory's `requirements.txt`.

**Rationale**: Vercel's `@vercel/python` builder resolves `requirements.txt` relative to the source file path (`services/<service>/src/main.py`). The actual `requirements.txt` files are one level up at `services/<service>/requirements.txt`. The vercel.json must be updated to add `config: { includeFiles: ["services/<service>/requirements.txt", "shared/**"] }` per build, OR each source file must be updated to reference a `requirements.txt` in the correct location.

**Simplest fix**: In `vercel.json`, add a `config.includeFiles` to each build entry pointing to its requirements.txt and the shared library.

**Alternatives considered**:
- Moving `main.py` to the service root: would break existing import paths
- Using a single root `requirements.txt`: would include all packages for every function, exceeding Vercel's 50MB serverless function limit; rejected

---

## Decision 3: Shared Library Access in Vercel Serverless

**Decision**: Each service does `sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))` to add the repo root to the Python path so `from shared.python.db_utils.session import ...` works. This path traversal (`__file__/../../../`) must also resolve correctly in the Vercel serverless environment.

**Rationale**: Vercel's Python runtime preserves the directory structure of included files relative to the repository root when `includeFiles` is used. Adding `"shared/**"` to `includeFiles` for each build ensures the shared library is packaged with each function.

---

## Decision 4: CORS — No Changes Needed for Production

**Decision**: No CORS changes are required for the Vercel deployment. All requests are same-origin.

**Rationale**: Since both frontend and all backends live under the same Vercel domain, the browser sends requests to the same origin (e.g. `https://inbody-analyzer.vercel.app/api/auth/login`). Same-origin requests do not trigger CORS preflight. The `ALLOWED_ORIGINS` env var on each service defaults to `http://localhost:3000` which is fine for local dev; it has no effect on same-origin production requests.

**Note**: If the project is ever split to separate domains (e.g. frontend on one domain, APIs on another), CORS will need updating. For now, no change.

---

## Decision 5: Environment Variables Required on Vercel

**Decision**: The following environment variables must be set in the Vercel project dashboard (Settings → Environment Variables):

### Frontend (Next.js)

| Variable | Production Value |
|----------|----------------|
| `NEXT_PUBLIC_AUTH_URL` | `` (empty string) |
| `NEXT_PUBLIC_USER_URL` | `` (empty string) |
| `NEXT_PUBLIC_SCAN_URL` | `` (empty string) |
| `NEXT_PUBLIC_ANALYTICS_URL` | `` (empty string) |
| `NEXT_PUBLIC_RECOMMENDATION_URL` | `` (empty string) |
| `NEXT_PUBLIC_ADMIN_URL` | `` (empty string) |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | `926220032336-17hu7aigdasv00f7m40g802k2rru7vpr.apps.googleusercontent.com` |

### Backend Services (all 6)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Supabase PostgreSQL connection string (async: `postgresql+asyncpg://...`) |
| `JWT_SECRET` | JWT signing secret (strong random string, same across all services) |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase service role key |
| `GEMINI_API_KEY` | Google Gemini API key (recommendation-service only) |
| `SUPABASE_STORAGE_BUCKET` | Supabase storage bucket name (scan-service only) |

---

## Decision 6: Async Event Loop — `lifespan="off"` Already Set

**Decision**: No changes needed for async compatibility. All services already pass `lifespan="off"` to `Mangum(app, lifespan="off")`.

**Rationale**: Vercel serverless functions do not support long-running ASGI lifespan events (startup/shutdown). The `lifespan="off"` setting on Mangum disables these events, which is already correctly set in all services. The `asynccontextmanager` lifespan functions still execute but are bypassed by Mangum — any critical startup logic (like `_seed_admin()` in auth-service) must be verified to be safe to skip on cold starts.

---

## Decision 7: Vercel Function Size Limit

**Decision**: The recommendation-service may approach Vercel's 250MB unzipped function size limit due to `google-generativeai` and its dependencies. This must be monitored during the first deployment.

**Mitigation**: If size is exceeded, the recommendation-service can be deployed to Railway as a free persistent service while the other 5 services remain on Vercel. This requires setting `NEXT_PUBLIC_RECOMMENDATION_URL` to the Railway URL instead of empty string.

---

## Decision 8: `vercel.json` Update Required

**Decision**: The existing `vercel.json` needs updates to:
1. Add `config.includeFiles` to each Python build to pull in `requirements.txt` and the shared library
2. Set `maxDuration` for slower functions (recommendation-service may need up to 30s for plan generation)
3. Add `functions` configuration for Python runtime version

**Current vercel.json** is a good starting point but missing these runtime configurations.
