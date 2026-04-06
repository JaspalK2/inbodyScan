# Feature Specification: Deploy App to Vercel (Frontend + Backend Services)

**Feature Branch**: `019-vercel-deployment`  
**Created**: 2026-04-06  
**Status**: Draft  
**Input**: "I want this to now be deployed in Vercel so you can test it remotely and make bug fixes"

> **Important note**: Claude Code cannot browse live URLs or interact with deployed applications — it operates solely on local files. Vercel deployment allows *you* and your users to access the app live. Bug fixes will continue to happen through local code changes here.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Frontend Accessible at a Public Vercel URL (Priority: P1) 🎯 MVP

The Next.js frontend is deployed to Vercel and accessible at a stable public URL (e.g. `inbody-analyzer.vercel.app`). Any visitor with the link can open the app in their browser without running anything locally.

**Why this priority**: This is the minimum viable deployment goal. Once the frontend is live, the full experience is available for demonstration and manual testing.

**Independent Test**: Open the Vercel URL in a browser. The app loads, the login page appears, and no CORS or "failed to fetch" errors appear in the console (assuming backend services are also reachable).

**Acceptance Scenarios**:

1. **Given** the `019-vercel-deployment` branch is pushed to GitHub, **When** Vercel's automatic build runs, **Then** the build succeeds and a live URL is produced.
2. **Given** the live URL is opened in a browser, **When** the page loads, **Then** the app's login/home page renders without blank screens or uncaught JavaScript errors.
3. **Given** the Vercel project has the six `NEXT_PUBLIC_*_URL` environment variables set to the hosted backend URLs, **When** a user logs in, **Then** API calls succeed and data loads correctly.
4. **Given** a new commit is pushed to the main branch, **When** Vercel's CI/CD pipeline runs, **Then** a new deployment is automatically published within 5 minutes.

---

### User Story 2 — Backend Services Deployed and Reachable (Priority: P1)

Each of the six Python FastAPI backend services (auth, user, scan, analytics, recommendation, admin) is deployed to a hosting platform and reachable from the Vercel-deployed frontend. The six `NEXT_PUBLIC_*_URL` environment variables in Vercel point to the live service endpoints.

**Why this priority**: The frontend is non-functional without reachable backend services. Both must be live for any end-to-end testing.

**Independent Test**: From the Vercel-deployed frontend, complete the full login flow. A successful login (JWT token returned) confirms the auth service is live and reachable. Generate a diet plan to confirm the recommendation service is live.

**Acceptance Scenarios**:

1. **Given** all six backend services are deployed, **When** the Vercel frontend calls any backend endpoint, **Then** the response arrives with no CORS errors and no network failures.
2. **Given** the Supabase PostgreSQL database is accessible from the deployed backends, **When** a user logs in, **Then** their account data is retrieved correctly.
3. **Given** a backend service restarts, **When** the frontend makes a request within 10 seconds, **Then** the service responds (auto-restart or zero-downtime deployment).

---

### Edge Cases

- What if the build fails due to missing environment variables? → Vercel build must fail visibly with a clear error; partial deployments must not go live.
- What if a backend service is unreachable? → The frontend should show a user-friendly error, not a blank screen or raw network error.
- What if environment variables contain trailing slashes or incorrect URLs? → The app should degrade gracefully (show error pages) rather than crash silently.
- What about secret management? → Backend service secrets (JWT secret, Supabase credentials, Gemini API key) must be stored as encrypted environment variables, not hardcoded in code or committed to the repository.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Next.js frontend MUST be deployable to Vercel from the `frontend/` subdirectory of the repository (monorepo configuration).
- **FR-002**: The Vercel project MUST have six environment variables configured: `NEXT_PUBLIC_AUTH_URL`, `NEXT_PUBLIC_USER_URL`, `NEXT_PUBLIC_SCAN_URL`, `NEXT_PUBLIC_ANALYTICS_URL`, `NEXT_PUBLIC_RECOMMENDATION_URL`, `NEXT_PUBLIC_ADMIN_URL`, each pointing to the live backend service base URL.
- **FR-003**: Each of the six Python FastAPI backend services MUST be deployed to a publicly-accessible hosting environment.
- **FR-004**: Each deployed backend service MUST have its required environment variables set (database URL, JWT secret, Supabase credentials, API keys) as encrypted secrets on the hosting platform.
- **FR-005**: Each backend service MUST have CORS configured to allow requests from the Vercel frontend domain (and `localhost` for local development).
- **FR-006**: New commits pushed to the main branch MUST trigger an automatic Vercel redeploy of the frontend.
- **FR-007**: The repository MUST contain a `vercel.json` configuration file in the `frontend/` directory (or root) that specifies the correct build root and output directory for the Next.js app.
- **FR-008**: The deployment MUST NOT expose any secrets (database passwords, JWT signing keys, API keys) in the frontend bundle or public repository.

### Key Entities

- **Vercel Project**: Linked to the GitHub repository; builds and serves the Next.js frontend.
- **Backend Service**: One of six FastAPI services (auth/user/scan/analytics/recommendation/admin); each deployed independently to a hosting platform.
- **Environment Variable**: A named secret or configuration value set on Vercel or the backend hosting platform; never hardcoded in source.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Vercel frontend URL loads the app in under 3 seconds on a standard broadband connection.
- **SC-002**: A complete login-to-dashboard flow (login → scan list → recommendations) completes end-to-end without errors when accessed via the Vercel URL.
- **SC-003**: A new commit pushed to main results in an updated live deployment within 5 minutes.
- **SC-004**: Zero secrets are present in the committed codebase or the Vercel build output (verified by `git grep` for known secret patterns).
- **SC-005**: All six backend services respond with HTTP 200 to a health-check request within 2 seconds of the frontend calling them.

## Assumptions

- The GitHub repository is already connected to Vercel (or the user will connect it via the Vercel dashboard — this is a one-time manual step that cannot be automated from within the codebase).
- The recommended backend hosting platform for the Python FastAPI services is **Railway** (free tier available, supports Python 3.13, persistent services, simple env var management) — other platforms (Render, Fly.io) are equally valid.
- The Supabase PostgreSQL database is already running and accessible; no database migration is needed for deployment.
- The six backend services already have `mangum` installed (confirmed — it is in `requirements.txt`) which enables serverless/ASGI deployment if needed.
- Backend services already read configuration from environment variables (via `pydantic-settings`); no code changes are needed for this.
- CORS is currently configured for `localhost` only and must be updated to also allow the Vercel domain.
- The `frontend/` directory is the Next.js root; a `vercel.json` must specify this as the project root for monorepo support.
- Claude Code cannot access the live Vercel URL or remotely interact with the deployed app — deployment verification must be done manually by the user.
