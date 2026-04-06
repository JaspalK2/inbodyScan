---
description: "Task list for Google OAuth Login & Sign-Up"
---

# Tasks: Google OAuth Login & Sign-Up

**Input**: Design documents from `/specs/003-google-oauth-login/`
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/ ✅

**Note**: Per project constitution Principle IV (Mandatory Test Coverage), test tasks are REQUIRED for this project. All user story phases include test tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US3)
- Exact file paths included in all task descriptions

## Path Conventions

- Backend service: `services/auth-service/src/`
- Frontend: `frontend/app/` and `frontend/lib/`
- Shared Python: `shared/python/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database schema, new dependencies, and environment configuration. No new project structure — this feature extends the existing auth-service and login page.

- [ ] T001 Run SQL migration from `specs/003-google-oauth-login/quickstart.md` against Supabase: ALTER `auth_users` to make `hashed_password` nullable, add `google_sub VARCHAR(255) UNIQUE` column with index, CREATE `google_link_requests` table with indexes
- [X] T002 [P] Add `google-auth==2.37.0` to `services/auth-service/requirements.txt` (Apache 2.0 — permitted per constitution Principle III)
- [X] T003 [P] Add `@react-oauth/google` to `frontend/package.json` (Apache 2.0 — permitted); run `npm install`
- [X] T004 [P] Add `NEXT_PUBLIC_GOOGLE_CLIENT_ID` to `frontend/.env.local` and `GOOGLE_CLIENT_ID` to `services/auth-service/.env` (values obtained from Google Cloud Console OAuth credentials)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: SQLAlchemy models, Pydantic schemas, and backend service functions that ALL three user stories depend on. No user story work can begin until this phase is complete.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T005 Update `services/auth-service/src/models/user.py`: change `hashed_password` `nullable=False` → `nullable=True`; add `google_sub: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)`
- [X] T006 Create `services/auth-service/src/models/google_link_request.py`: `GoogleLinkRequest` SQLAlchemy model with columns `id (PK)`, `state_token (unique, indexed)`, `email`, `google_sub`, `google_name (nullable)`, `expires_at`, `created_at (server_default now())`
- [X] T007 Add `from .models import google_link_request  # noqa` import to `services/auth-service/src/main.py` alongside existing model imports so SQLAlchemy metadata includes the new table
- [X] T008 [P] Add Pydantic schemas to `services/auth-service/src/schemas/auth.py`: `GoogleLoginRequest(id_token: str)`, `GoogleLinkResponse(link_token: str, email: str, google_name: str | None)`, `ConfirmLinkRequest(link_token: str)`, and extend `UserOut` with optional `google_sub: str | None = None`
- [X] T009 [P] Create `services/auth-service/src/services/google_auth_service.py` with three functions: `verify_google_token(id_token: str) -> dict` (calls `google.oauth2.id_token.verify_oauth2_token()` with `requests.Request()`, validates `aud == GOOGLE_CLIENT_ID` env var, raises `ValueError` on failure); `create_link_request(session, email, google_sub, google_name) -> str` (stores `GoogleLinkRequest` row with 10-min expiry, returns `state_token`); `resolve_link_request(session, state_token) -> GoogleLinkRequest | None` (fetches row where `state_token` matches and `expires_at > now()`, deletes it, returns it or None)
- [X] T010 Extend `services/auth-service/src/services/auth_service.py` with four new functions: `get_user_by_google_sub(session, sub: str) -> User | None`; `get_user_by_email(session, email: str) -> User | None`; `create_google_user(session, email: str, name: str, google_sub: str) -> User` (auto-generate `username = f"google_{sub[:8]}"`, `hashed_password=None`); `link_google_account(session, user_id: str, google_sub: str) -> User` (sets `google_sub` on existing user and commits)
- [X] T011 [P] Add TypeScript types and API client functions to `frontend/lib/api.ts`: add `GoogleLoginResponse` interface (`access_token?: string; token_type?: string; link_token?: string; email?: string; google_name?: string`); add `googleLogin(idToken: string): Promise<GoogleLoginResponse>` and `confirmGoogleLink(linkToken: string): Promise<{ access_token: string }>` to the `auth` object using the existing `request()` helper pointing to `"auth"` service at `/api/auth/google` and `/api/auth/google/confirm-link` respectively

**Checkpoint**: Foundation ready — models exist, schemas defined, service functions implemented. Verify with `python -c "from services.auth_service import get_user_by_google_sub"` and `npx tsc --noEmit` before proceeding.

---

## Phase 3: User Story 1 — New User Signs Up via Google (Priority: P1) 🎯 MVP

**Goal**: A visitor with no account can click "Continue with Google," complete the Google consent flow, and land on the main app with a new account automatically created from their Google profile.

**Independent Test**: Open the app with no account → click "Continue with Google" → approve consent → confirm you land on `/dashboard` with Google name/email shown and a new `auth_users` row with `google_sub` set and `hashed_password` null.

### Tests for User Story 1 ⚠️ Write and verify these FAIL before implementing

- [X] T012 [P] [US1] Integration test: `POST /api/auth/google` with a valid (mocked) Google ID token for a brand-new email creates a new `auth_users` row with `google_sub` set and `hashed_password` null, and returns 201 + `access_token` + `refresh_token` cookie in `services/auth-service/tests/integration/test_google_auth.py`
- [X] T013 [P] [US1] Unit test: `google_auth_service.verify_google_token()` raises `ValueError` for an invalid token, returns decoded payload dict for a valid mocked token in `services/auth-service/tests/unit/test_google_auth_service.py`
- [X] T014 [P] [US1] Unit test: `auth_service.create_google_user()` creates a user with `hashed_password=None`, `google_sub` set, and auto-generated username matching `google_<sub[:8]>` in `services/auth-service/tests/unit/test_auth_service_google.py`
- [X] T015 [P] [US1] E2E test: new user Google sign-up flow completes and lands on dashboard in `frontend/tests/e2e/test_google_login.spec.ts`

### Implementation for User Story 1

- [X] T016 [US1] Add `POST /api/auth/google` endpoint to `services/auth-service/src/routers/auth.py`: accept `GoogleLoginRequest`; call `verify_google_token()`; look up user by `google_sub`, then by `email`; if no existing user → call `create_google_user()` → issue tokens → return 201; if existing Google user → issue tokens → return 200; if existing password user (same email) → call `create_link_request()` → return 202 with `GoogleLinkResponse` (no session issued yet)
- [X] T017 [US1] Add `GoogleOAuthProvider` wrapper in `frontend/app/layout.tsx` (or just `frontend/app/login/page.tsx`) passing `clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID}` so the GIS script loads on the login page
- [X] T018 [US1] Update `frontend/lib/auth-context.tsx`: add `googleLogin(idToken: string): Promise<{ needsLink: boolean; linkToken?: string; email?: string; googleName?: string }>` method that calls `api.auth.googleLogin(idToken)`, and if `access_token` returned, calls `setAccessToken()` + `auth.me()` + `setUser()`; if `link_token` returned, returns `{ needsLink: true, ... }`
- [X] T019 [US1] Update `frontend/app/login/page.tsx`: add a visual divider ("— or —"), add `useGoogleLogin` hook from `@react-oauth/google` (using the `implicit` flow with `onSuccess` receiving `tokenResponse`; or use `GoogleLogin` component returning `credentialResponse.credential`); on credential received → call `auth.googleLogin(credential)` → if success, `router.push("/dashboard")`; if `needsLink`, show the linking modal (state: `linkPending`)

**Checkpoint**: US1 functional — new user can sign up via Google end-to-end.

---

## Phase 4: User Story 2 — Existing User Signs In via Google (Priority: P1)

**Goal**: A user who already registered via Google can click "Continue with Google" and be signed in to their existing account with all prior data intact.

**Independent Test**: Register via Google (US1) → log out → click "Continue with Google" again → confirm signed into the same account (same user `id` as the first session).

### Tests for User Story 2 ⚠️ Write and verify these FAIL before implementing

- [X] T020 [P] [US2] Integration test: `POST /api/auth/google` with a valid mocked ID token for an email whose `auth_users` row already has `google_sub` set returns 200 + `access_token` + refresh cookie, and does NOT create a new `auth_users` row in `services/auth-service/tests/integration/test_google_auth.py`
- [X] T021 [P] [US2] Integration test: `GET /api/auth/me` using the access token from T020 returns the correct existing user profile (same `id`) in `services/auth-service/tests/integration/test_google_auth.py`
- [X] T022 [P] [US2] E2E test: returning Google user signs in and lands on existing account (data persists from prior session) in `frontend/tests/e2e/test_google_login.spec.ts`

### Implementation for User Story 2

No new backend code required — the `POST /api/auth/google` endpoint implemented in T016 already handles this path (existing `google_sub` match → issue tokens → 200). Verify the lookup-by-`google_sub`-first logic is correct.

- [X] T023 [US2] Verify `POST /api/auth/google` in `services/auth-service/src/routers/auth.py` correctly prioritises `google_sub` lookup over email lookup (so a user who changed their Google email is still matched to their existing account by `sub`) — add a code comment explaining the lookup priority order

**Checkpoint**: US2 functional — returning Google user signs in to existing account.

---

## Phase 5: User Story 2 (continued) — Account Linking Confirmation Flow (Priority: P1)

**Goal**: When a user who registered with email/password tries Google sign-in with the same email, they see a confirmation prompt and can choose to link or decline.

**Independent Test**: Register with email/password using `test@example.com` → sign out → click "Continue with Google" with the same email → confirm the linking prompt appears → click Confirm → signed in to the original account with `google_sub` now set.

### Tests for Account Linking Flow ⚠️ Write and verify these FAIL before implementing

- [X] T024 [P] [US2] Integration test: `POST /api/auth/google` with a mocked token whose email matches an existing password-based account (no `google_sub`) returns 202 + `link_token` and does NOT issue a session in `services/auth-service/tests/integration/test_google_auth.py`
- [X] T025 [P] [US2] Integration test: `POST /api/auth/google/confirm-link` with a valid `link_token` sets `google_sub` on the existing `auth_users` row and returns 200 + `access_token` + refresh cookie in `services/auth-service/tests/integration/test_google_auth.py`
- [X] T026 [P] [US2] Integration test: `POST /api/auth/google/confirm-link` with an expired or unknown `link_token` returns 410 Gone in `services/auth-service/tests/integration/test_google_auth.py`
- [X] T027 [P] [US2] Unit test: `google_auth_service.resolve_link_request()` returns `None` for an expired row (mock `expires_at` in the past) in `services/auth-service/tests/unit/test_google_auth_service.py`

### Implementation for Account Linking

- [X] T028 [US2] Add `POST /api/auth/google/confirm-link` endpoint to `services/auth-service/src/routers/auth.py`: accept `ConfirmLinkRequest(link_token)`; call `resolve_link_request(session, link_token)`; if None → 410 Gone; call `link_google_account(session, existing_user.email, google_sub)` to set `google_sub`; issue tokens (same as login) → return 200
- [X] T029 [US2] Add `confirmGoogleLink(linkToken: string)` method to `frontend/lib/auth-context.tsx`: calls `api.auth.confirmGoogleLink(linkToken)`, sets access token, fetches `me`, updates user state
- [X] T030 [US2] Add linking confirmation modal to `frontend/app/login/page.tsx`: conditionally rendered when `linkPending` state is true; shows "An account with this email exists. Link your Google account?" with the Google display name; "Confirm" button calls `auth.confirmGoogleLink(linkToken)` then `router.push("/dashboard")`; "Cancel" button clears `linkPending` state and returns to login form

**Checkpoint**: Full account-linking flow functional — prompt appears, confirm links and signs in, cancel returns to login.

---

## Phase 6: User Story 3 — Secure Session Management (Priority: P2)

**Goal**: Google-authenticated sessions persist across browser restarts (30-day rolling), and sign-out cleanly invalidates the session and blocks protected routes.

**Independent Test**: Sign in via Google → close and reopen browser → confirm still signed in. Sign out → navigate to `/dashboard` → confirm redirected to login.

### Tests for User Story 3 ⚠️ Write and verify these FAIL before implementing

- [X] T031 [P] [US3] Integration test: after `POST /api/auth/google` the refresh cookie `max_age` is `2592000` (30 days in seconds) in `services/auth-service/tests/integration/test_google_auth.py`
- [X] T032 [P] [US3] Integration test: `POST /api/auth/logout` after a Google sign-in revokes the refresh token and returns 200; a subsequent `POST /api/auth/refresh` with the old cookie returns 401 in `services/auth-service/tests/integration/test_google_auth.py`
- [X] T033 [P] [US3] E2E test: sign in via Google → close/reopen browser → still signed in (session persists via refresh cookie) in `frontend/tests/e2e/test_google_login.spec.ts`
- [X] T034 [P] [US3] E2E test: sign out via Google session → navigate to `/dashboard` → redirected to `/login` in `frontend/tests/e2e/test_google_login.spec.ts`

### Implementation for User Story 3

The existing refresh-token architecture already handles session persistence and revocation. The only change is the cookie `max_age` for Google-authenticated sessions.

- [X] T035 [US3] Update `services/auth-service/src/routers/auth.py` `POST /api/auth/google` endpoint: set refresh cookie with `max_age=GOOGLE_REFRESH_COOKIE_MAX_AGE` where `GOOGLE_REFRESH_COOKIE_MAX_AGE = 30 * 24 * 60 * 60` (2592000 seconds) — defined as a module-level constant, separate from the existing 7-day `COOKIE_MAX_AGE` used by password login
- [X] T036 [US3] Set `REFRESH_TOKEN_EXPIRE_DAYS=30` in `services/auth-service/.env` (or manage Google sessions via the same constant) and verify `store_refresh_token()` uses this value so the DB expiry matches the cookie expiry

**Checkpoint**: US3 fully functional — all 3 user stories independently working.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, UI consistency, data isolation validation, and quickstart scenario verification.

- [X] T037 [P] Add graceful error UI to `frontend/app/login/page.tsx` for Google sign-in failures: if `googleLogin()` throws (network error, Google unavailable), display the same error-box component used for password login failures (`"Google sign-in failed. Please try again."`)
- [X] T038 [P] Add loading state to the Google button in `frontend/app/login/page.tsx`: disable the button and show a spinner while `googleLogin()` or `confirmGoogleLink()` is pending (prevent double-submission)
- [X] T039 [P] Integration test: data isolation — `POST /api/auth/google` with User A's Google token cannot access User B's data; `GET /api/auth/me` returns only the authenticated user's record in `services/auth-service/tests/integration/test_google_auth.py`
- [X] T040 [P] Integration test: `POST /api/auth/google` with a Google token whose `aud` claim does not match `GOOGLE_CLIENT_ID` returns 401 (wrong-audience attack prevention) in `services/auth-service/tests/unit/test_google_auth_service.py`
- [X] T041 [P] Verify no PII is logged: add a check that `verify_google_token()` in `services/auth-service/src/services/google_auth_service.py` does not log the raw `id_token` or user email at any log level — add a code comment noting this is a constitution requirement
- [ ] T042 Run all 9 quickstart.md validation scenarios against the locally running stack and fix any failures before marking this feature complete

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — T002, T003, T004 can run in parallel with T001
- **Foundational (Phase 2)**: Depends on Phase 1 (DB schema must exist before models) — BLOCKS all user stories; T008, T009, T011 can run in parallel with T005
- **US1 (Phase 3)**: Depends on Foundational — MVP; T012–T015 (tests) can run in parallel with each other and alongside T016 setup
- **US2 sign-in (Phase 4)**: Depends on Foundational only; can start in parallel with US1 (different concern: existing user lookup)
- **US2 linking (Phase 5)**: Depends on US1 endpoint being wired (T016) for the 202 path; T024–T027 can run in parallel
- **US3 (Phase 6)**: Depends on Foundational only; session management reuses existing infrastructure
- **Polish (Phase 7)**: Depends on all user stories complete

### Within Each User Story

- Tests MUST be written and verified to FAIL before implementation
- Schemas before service → service before endpoint → endpoint before frontend
- Backend complete before frontend integration
- `npx tsc --noEmit` must pass after every frontend change

### Parallel Opportunities

- T002, T003, T004 (Phase 1) can all run in parallel
- T008, T009, T011 (Phase 2) can run in parallel with each other after T005/T006 complete
- US1 (Phase 3) and US2 sign-in (Phase 4) can be developed in parallel after Foundational
- US3 (Phase 6) can be developed in parallel with US1/US2
- All test tasks within a phase marked [P] can run in parallel

---

## Implementation Strategy

### MVP (User Story 1 Only)

Implement Phases 1–3. This gives:
- Database schema ready
- Backend: `verify_google_token` + `create_google_user` + `POST /api/auth/google` (new-user path)
- Frontend: Google button on login page + session established on success

This is fully demonstrable: a brand-new user can sign up via Google with no username/password form.

### Full Feature (User Stories 1–3)

Add Phases 4–6 for existing-user sign-in, account linking, and 30-day session persistence. These are additive and do not require changes to the MVP code.

### Polish

Phase 7 can run any time after all stories are complete and before the branch is merged.
