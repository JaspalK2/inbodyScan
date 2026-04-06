# Implementation Plan: Google OAuth Login & Sign-Up

**Branch**: `003-google-oauth-login` | **Date**: 2026-04-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-google-oauth-login/spec.md`

---

## Summary

Add "Continue with Google" as an alternative authentication path on the login page. Google-issued ID tokens are verified server-side by the auth-service; the existing refresh-token + JWT session model is reused unchanged. New users get an account auto-created from their Google profile; existing users with a matching email are shown a confirmation prompt before their accounts are linked. The feature extends the existing `auth_users` table with two new nullable columns (`google_sub`, relaxed `hashed_password`) and adds two new endpoints (`POST /api/auth/google`, `POST /api/auth/google/confirm-link`).

---

## Technical Context

**Language/Version**: Python 3.13 (auth-service backend), TypeScript 5.x / Next.js 15 (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 async (existing); `google-auth` 2.37.0 (new, Apache 2.0); `@react-oauth/google` (new, Apache 2.0)
**Storage**: Supabase PostgreSQL — `auth_users` table extended; `google_link_requests` table added
**Testing**: pytest (backend integration + unit), Vitest + React Testing Library (frontend unit), Playwright (E2E)
**Target Platform**: Web (browser) + Vercel serverless (via Mangum)
**Project Type**: Web service (backend) + web application (frontend)
**Performance Goals**: Google sign-in completes in <30s for new users, <10s for returning users (SC-001/SC-002)
**Constraints**: Server-side token verification mandatory (FR-004); no client-trust of Google identity claims
**Scale/Scope**: Single-tenant per-user auth; no high-concurrency special handling needed

---

## Constitution Check

*GATE: Must pass before implementation. Re-checked after design.*

| Principle | Gate | Status |
|---|---|---|
| **I. Extensibility** | New auth path added via new endpoints — existing `/api/auth/login` unchanged. `google_sub` column is additive. Auth context extended with `googleLogin` method. | ✅ PASS |
| **II. Algorithm Efficiency** | `google_sub` lookup uses unique indexed column — O(1). Email deduplication uses indexed `email` column — O(1). No unbounded queries introduced. | ✅ PASS |
| **III. License Compliance** | `google-auth` (Apache 2.0), `@react-oauth/google` (Apache 2.0) — both permissive. Verified no GPL transitive deps. | ✅ PASS |
| **IV. Mandatory Tests** | Unit tests for token verification logic, integration tests for all new endpoints, E2E tests for all 3 user stories (P1 sign-up, P1 sign-in, P2 session). | ✅ REQUIRED — tasks will include tests |
| **V. UI/UX Consistency** | Google button uses the GIS pre-styled component which matches brand guidelines; placed below the existing form with a divider ("or"). Login page remains in existing `glass-card` design system. | ✅ PASS |
| **Security** | ID token verified server-side before any session is issued. `google_sub` lookup isolates per-user. No PII in logs. Link token expires in 10 minutes. | ✅ PASS |

---

## Project Structure

### Documentation (this feature)

```text
specs/003-google-oauth-login/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/
│   └── google-auth-api.md
└── tasks.md             ← Phase 2 output (/speckit.tasks)
```

### Source Code

```text
services/auth-service/src/
├── models/
│   ├── user.py              ← MODIFY: add google_sub column, make hashed_password nullable
│   └── google_link_request.py  ← NEW: GoogleLinkRequest model
├── schemas/
│   └── auth.py              ← MODIFY: add GoogleLoginRequest, GoogleLinkResponse, ConfirmLinkRequest
├── services/
│   └── auth_service.py      ← MODIFY: add get_user_by_google_sub, get_user_by_email, create_google_user, link_google_account
│   └── google_auth_service.py  ← NEW: verify_google_token, create_link_request, resolve_link_request
├── routers/
│   └── auth.py              ← MODIFY: add POST /google and POST /google/confirm-link endpoints
└── requirements.txt         ← MODIFY: add google-auth==2.37.0

frontend/
├── app/login/
│   └── page.tsx             ← MODIFY: add GoogleOAuthProvider wrapper, "Continue with Google" button, linking modal
├── lib/
│   ├── api.ts               ← MODIFY: add googleLogin(), confirmGoogleLink() to auth object
│   └── auth-context.tsx     ← MODIFY: add googleLogin() and confirmGoogleLink() to context
└── package.json             ← MODIFY: add @react-oauth/google

shared/
└── (no changes)
```

---

## Complexity Tracking

No constitution violations. All design choices are additive and reuse existing infrastructure.

---

## Implementation Approach

### Phase A: Database & Backend Models

1. Run migration SQL from `quickstart.md` against Supabase (adds `google_sub` to `auth_users`, relaxes `hashed_password`, creates `google_link_requests`).
2. Update `services/auth-service/src/models/user.py`:
   - `hashed_password`: change `nullable=False` → `nullable=True`
   - Add `google_sub: Mapped[str | None]` with `unique=True, nullable=True, index=True`
3. Create `services/auth-service/src/models/google_link_request.py` with `GoogleLinkRequest` SQLAlchemy model.
4. Add `google-auth==2.37.0` to `requirements.txt`.

### Phase B: Backend Service & Endpoints

5. Create `services/auth-service/src/services/google_auth_service.py`:
   - `verify_google_token(id_token: str) -> dict` — calls `google.oauth2.id_token.verify_oauth2_token()`, validates `aud` == `GOOGLE_CLIENT_ID`. Returns decoded payload or raises.
   - `create_link_request(session, email, google_sub, google_name) -> str` — stores a `GoogleLinkRequest` row with 10-minute expiry. Returns `state_token`.
   - `resolve_link_request(session, state_token) -> GoogleLinkRequest | None` — fetches and deletes the row if valid and non-expired.
6. Extend `services/auth-service/src/services/auth_service.py`:
   - `get_user_by_google_sub(session, sub) -> User | None`
   - `get_user_by_email(session, email) -> User | None`
   - `create_google_user(session, email, name, google_sub) -> User` — auto-generates username as `google_<sub[:8]>`, `hashed_password=None`.
   - `link_google_account(session, user_id, google_sub) -> User` — sets `google_sub` on existing user.
7. Update `services/auth-service/src/schemas/auth.py` — add `GoogleLoginRequest`, `GoogleLinkResponse`, `ConfirmLinkRequest`, extend `UserOut` with optional `google_sub`.
8. Update `services/auth-service/src/routers/auth.py` — add `POST /api/auth/google` and `POST /api/auth/google/confirm-link` (per contract in `contracts/google-auth-api.md`).

### Phase C: Frontend Integration

9. Add `@react-oauth/google` to `frontend/package.json`.
10. Wrap the app (or just the login page) with `<GoogleOAuthProvider clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID}>`.
11. Add `googleLogin(idToken)` and `confirmGoogleLink(linkToken)` to `frontend/lib/api.ts`.
12. Add `googleLogin()` and `confirmGoogleLink()` to `frontend/lib/auth-context.tsx`.
13. Update `frontend/app/login/page.tsx`:
    - Add `useGoogleLogin` hook (redirect flow) or `GoogleLogin` component from `@react-oauth/google`.
    - On credential received → call `auth.googleLogin(credential)` → if `access_token` returned, sign in normally. If `link_token` returned, show the linking confirmation modal.
    - **Linking modal**: "An account with this email exists. Link your Google account?" with Confirm/Cancel. Confirm → calls `auth.confirmGoogleLink(linkToken)`.

### Phase D: Tests

14. Backend unit tests: `verify_google_token` with valid/invalid/expired tokens (mock Google's public key response).
15. Backend integration tests: all 4 new endpoint scenarios (new user, existing Google user, conflict → 202, confirm-link, expired link token).
16. Backend integration test: data isolation — `google_sub` lookup only returns the owning user's record.
17. Frontend unit tests: login page renders Google button; googleLogin sets auth context; linking modal shows/hides correctly.
18. E2E tests: new user sign-up, returning user sign-in, session persistence (SC-001/SC-002/SC-003).

---

## Quickstart Reference

See [quickstart.md](quickstart.md) for:
- Google Cloud project setup
- SQL migration
- Environment variable configuration
- 9 manual validation scenarios
