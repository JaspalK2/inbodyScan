# Research: Google OAuth Login & Sign-Up

**Feature**: `003-google-oauth-login`
**Date**: 2026-04-02

---

## Decision 1: Google Identity Library Choice

**Decision**: Use Google Identity Services (GIS) — specifically the `@react-oauth/google` React wrapper (Apache 2.0) which wraps the `accounts.google.com/gsi/client` script.

**Rationale**: The legacy `gapi.auth2` library is deprecated and will stop working. GIS is the current Google-supported approach and uses FedCM where available for improved privacy. `@react-oauth/google` (Apache 2.0) provides a React hook and component that abstracts the GIS script loading and callback wiring — eliminating manual `<script>` injection.

**Alternatives considered**:
- Raw GIS script (`accounts.google.com/gsi/client`) — works but requires manual React integration; `@react-oauth/google` does this cleanly with no added cost.
- NextAuth.js — broad OAuth library supporting many providers; overkill given the existing custom JWT/refresh-token auth system; would require replacing or duplicating the current session model. Rejected.

**License**: `@react-oauth/google` — Apache 2.0 ✅

---

## Decision 2: Backend Token Verification Library

**Decision**: Use `google-auth-library` Python package (`google-auth`, MIT license) for server-side ID token verification.

**Rationale**: The official Google-supported library for verifying ID tokens in Python. It fetches Google's public keys, validates the JWT signature, checks `aud` (must match the Google Client ID), `iss`, and `exp`. This is the approach recommended by Google's documentation.

**Alternatives considered**:
- Manual JWT verification with `pyjwt` + fetching Google's JWKS endpoint manually — possible but fragile; Google rotates keys and the caching must be handled correctly. Using the official library is safer and maintained.

**License**: `google-auth` — Apache 2.0 ✅

---

## Decision 3: Account Linking Strategy (Email-Based Deduplication)

**Decision**: On Google sign-in, look up existing `auth_users` by email. If a password-based account exists with that email, show a confirmation prompt. If confirmed, store the Google `sub` on the existing user record and proceed. If the email is new, auto-create the account.

**Rationale**: Email is the safest deduplication key for Google accounts because Google guarantees email uniqueness within Google Workspace. The confirmation prompt (per clarification Q1) prevents silent account takeover.

**Alternatives considered**:
- Auto-link silently — rejected (security risk: Google account silently gains access to password-protected account without user consent).
- Reject Google sign-in if email already exists — rejected (bad UX; forces users to remember which method they used).

---

## Decision 4: Session Model — No Changes to Existing Refresh Token Architecture

**Decision**: Reuse the existing `refresh_token` + short-lived JWT access token architecture. Extend `REFRESH_TOKEN_EXPIRE_DAYS` env var to 30 for Google-authenticated sessions. The Google sign-in endpoint issues the same `refresh_token` cookie + `access_token` JWT pair as the existing `/api/auth/login` endpoint.

**Rationale**: The existing session model (httponly refresh cookie + short-lived JWT) is already well-designed. Adding Google sign-in as a new authentication *path* that terminates in the same session issuance keeps the rest of the system unchanged. No new session table needed.

**Note**: The 30-day session duration (per clarification Q2) can be controlled by setting `REFRESH_TOKEN_EXPIRE_DAYS=30` for Google sign-in tokens. The existing 7-day value for password login sessions may remain or be unified — this is an implementation decision for the developer.

---

## Decision 5: `auth_users` Schema Changes

**Decision**: Add two nullable columns to the existing `auth_users` table:
- `google_sub` (`VARCHAR(255)`, unique, nullable, indexed) — stores the Google subject identifier for users who sign in via Google.
- `hashed_password` — relax to nullable to support Google-only users who have no password.

**Rationale**: `google_sub` enables reliable re-identification even if the user changes their Google account email. Making `hashed_password` nullable supports accounts created purely via Google. Existing password accounts are unaffected (their `hashed_password` column remains non-null; `google_sub` is null).

---

## Decision 6: New Backend Endpoint

**Decision**: Add `POST /api/auth/google` to the auth-service router. Accepts `{ id_token: string }` from the frontend (the raw Google-issued credential), verifies it server-side, and returns the same `TokenResponse` (access_token) + sets refresh cookie as existing login.

**Rationale**: Mirrors the existing `/api/auth/login` contract exactly. Keeps the frontend auth-context integration minimal — `googleLogin(idToken)` replaces `login(username, password)` for the Google path.

---

## License Audit

| Package | License | Verdict |
|---|---|---|
| `@react-oauth/google` | Apache 2.0 | ✅ Permitted |
| `google-auth` (Python) | Apache 2.0 | ✅ Permitted |

No GPL/LGPL/AGPL transitive dependencies introduced. Both packages have clean permissive dependency chains.
