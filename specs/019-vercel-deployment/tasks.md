# Tasks: Deploy App to Vercel

**Input**: Design documents from `/specs/019-vercel-deployment/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓, quickstart.md ✓

**Organization**: 4 independent phases. US1 (vercel.json + health endpoints) is the core deliverable. All health endpoint additions (Phase 3) are parallel across services. US2 (env var docs + DEPLOYMENT.md) is documentation-only.

---

## Phase 1: Setup

**Purpose**: Read current state of the two files being changed before writing.

- [X] T001 Read `/vercel.json` (existing root file) — confirm the current builds/routes structure before replacing
- [X] T002 [P] Read `frontend/app/(app)/recommendations/page.tsx` lines 1–15 to confirm no existing health import is present — no changes needed, just orientation

---

## Phase 2: Foundational — Update vercel.json (Blocking)

**Purpose**: The updated `vercel.json` is required before any Vercel deployment can succeed. Must be done first.

- [X] T003 Replace `/vercel.json` with the full production config from plan.md: add `"functions"` block specifying `"runtime": "python3.12"` and `maxDuration` per service (15s for most, 20s for scan, 30s for recommendation); update each `"builds"` entry to add `"config": { "includeFiles": ["services/<svc>/requirements.txt", "shared/**", "services/<svc>/src/**"] }`; keep all existing `"routes"` unchanged

**Checkpoint**: vercel.json complete → health endpoints and docs can proceed in parallel.

---

## Phase 3: User Story 1 — Health Check Endpoints (Priority: P1) 🎯 MVP

**Goal**: Every backend service exposes `GET /api/<service>/health` returning `{"status": "ok", "service": "<name>"}`. Used to verify deployment succeeded without requiring auth or data.

**Independent Test**: After deployment, `curl https://<vercel-url>/api/auth/health` returns `{"status":"ok"}`. Same for all 6 services.

### Tests for User Story 1

- [X] T004 [US1] Read `services/auth-service/src/main.py` lines 30–70 to confirm exact location to insert the health endpoint (after middleware setup, before include_router) — no changes yet

### Implementation for User Story 1

- [X] T005 [US1] In `services/auth-service/src/main.py`, add `@app.get("/api/auth/health")\nasync def health_auth(): return {"status": "ok", "service": "auth"}` after the `app.add_middleware(CORSMiddleware, ...)` call and before `app.include_router(auth_router)`
- [X] T006 [P] [US1] In `services/user-service/src/main.py`, add `@app.get("/api/users/health")\nasync def health_user(): return {"status": "ok", "service": "user"}` after the `app.add_middleware` call
- [X] T007 [P] [US1] In `services/scan-service/src/main.py`, add `@app.get("/api/scans/health")\nasync def health_scan(): return {"status": "ok", "service": "scan"}` after the `app.add_middleware` call
- [X] T008 [P] [US1] In `services/analytics-service/src/main.py`, add `@app.get("/api/analytics/health")\nasync def health_analytics(): return {"status": "ok", "service": "analytics"}` after the `app.add_middleware` call
- [X] T009 [P] [US1] In `services/recommendation-service/src/main.py`, add `@app.get("/api/recommendations/health")\nasync def health_rec(): return {"status": "ok", "service": "recommendation"}` after the `app.add_middleware` call
- [X] T010 [P] [US1] In `services/admin-service/src/main.py`, add `@app.get("/api/admin/health")\nasync def health_admin(): return {"status": "ok", "service": "admin"}` after the `app.add_middleware` call

**Checkpoint**: US1 complete — all 6 health endpoints present, vercel.json updated.

---

## Phase 4: User Story 2 — Deployment Docs & Env Var Reference (Priority: P1)

**Goal**: A developer (or the repo owner) can follow `DEPLOYMENT.md` from scratch to get the app live on Vercel without needing to ask for help.

**Independent Test**: Read `DEPLOYMENT.md` and follow it step-by-step on a fresh Vercel account; the app goes live at a public URL.

### Implementation for User Story 2

- [X] T011 [US2] Create `frontend/.env.production` documenting all 7 `NEXT_PUBLIC_*` production values: six service URLs set to empty string `""` (same-origin), and `NEXT_PUBLIC_GOOGLE_CLIENT_ID` set to the OAuth client ID from `.env.local`; add a comment block explaining why the URLs are empty
- [X] T012 [P] [US2] Create `DEPLOYMENT.md` at the repo root with: (1) Prerequisites section (Vercel account, GitHub repo public or Vercel connected), (2) Step 1 — connect GitHub repo to Vercel (manual, dashboard link), (3) Step 2 — env vars table listing all variables from data-model.md with their production values and which are secrets, (4) Step 3 — trigger redeploy, (5) Step 4 — health check verification commands from quickstart.md, (6) Step 5 — smoke test steps, (7) Troubleshooting table from quickstart.md, (8) Local dev note (unchanged, `.env.local` still used)

**Checkpoint**: US2 complete — deployment is fully documented.

---

## Phase 5: Polish & Validation

- [X] T013 Run `npx tsc --noEmit` in `frontend/` to confirm no TypeScript errors were introduced
- [X] T014 [P] Verify `vercel.json` is valid JSON by running `python3.13 -c "import json; json.load(open('vercel.json'))"` from repo root
- [X] T015 [P] Run `grep -r "health" services/*/src/main.py` to confirm all 6 health endpoints are present in their respective main.py files

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — T001 and T002 parallel
- **Foundational (Phase 2)**: Depends on T001 read — T003 sequential
- **US1 (Phase 3)**: T004 read → T005 → T006/T007/T008/T009/T010 all parallel (different files)
- **US2 (Phase 4)**: T011 and T012 parallel (different files); no dependency on US1
- **Polish (Phase 5)**: Depends on T003 (vercel.json), T005–T010 (health endpoints), T011–T012 (docs)

### Parallel Opportunities

```bash
# Phase 1 (parallel):
Task A: T001 Read vercel.json
Task B: T002 Read page.tsx (orientation)

# Phase 3 health endpoints (T006–T010 all parallel after T005):
Task A: T006 user-service health
Task B: T007 scan-service health
Task C: T008 analytics-service health
Task D: T009 recommendation-service health
Task E: T010 admin-service health

# Phase 4 docs (parallel):
Task A: T011 .env.production
Task B: T012 DEPLOYMENT.md

# Phase 5 validation (parallel):
Task A: T013 tsc check
Task B: T014 vercel.json JSON validation
Task C: T015 grep health endpoints
```

---

## Implementation Strategy

### MVP (US1 only — T001–T010)

1. T001: Read vercel.json
2. T003: Replace vercel.json with full production config
3. T004: Read auth-service main.py
4. T005–T010: Add health endpoints to all 6 services
5. **STOP and VALIDATE**: T014 (JSON valid) + T015 (grep confirms all 6 endpoints)

### Full Delivery

Add T011–T012 for deployment documentation, then T013–T015 for validation.

---

## Notes

- T003 is a **full replacement** of vercel.json — read T001 first to confirm the replacement is correct
- T005 must come before T006–T010 only to confirm the pattern works; they are otherwise independent
- The `NEXT_PUBLIC_*_URL = ""` (empty string) is the critical production setting — without it, all API calls will fail in production (they'd hit `undefined/api/auth/login`)
- One step (connecting GitHub to Vercel) CANNOT be done via code — it requires the Vercel dashboard and must be done manually by the repo owner
- The `frontend/.env.production` file is safe to commit (contains no secrets — only empty strings and the public Google OAuth client ID)
