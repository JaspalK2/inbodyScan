# Data Model: Google OAuth Login & Sign-Up

**Feature**: `003-google-oauth-login`
**Date**: 2026-04-02

---

## Modified Table: `auth_users`

Extends the existing table with two new columns to support Google OAuth identity.

| Column | Type | Nullable | Unique | Indexed | Notes |
|---|---|---|---|---|---|
| `id` | `VARCHAR(36)` | NO | YES (PK) | YES | UUID, unchanged |
| `username` | `VARCHAR(64)` | NO | YES | YES | Unchanged; auto-generated for Google users (`google_<sub[:8]>`) |
| `email` | `VARCHAR(255)` | NO | YES | YES | Unchanged |
| `hashed_password` | `VARCHAR(255)` | **YES** (was NO) | NO | NO | **Changed to nullable** — Google-only accounts have no password |
| `google_sub` | `VARCHAR(255)` | YES | YES | YES | **New column** — Google subject identifier (`sub` claim from ID token) |
| `is_admin` | `BOOLEAN` | NO | NO | NO | Unchanged |
| `is_active` | `BOOLEAN` | NO | NO | NO | Unchanged |
| `created_at` | `TIMESTAMPTZ` | NO | NO | NO | Unchanged |
| `updated_at` | `TIMESTAMPTZ` | NO | NO | NO | Unchanged |

### Migration Notes
- `hashed_password` must be altered from `NOT NULL` to `NULL` in Supabase via migration.
- `google_sub VARCHAR(255) UNIQUE NULLABLE` index added.
- Existing rows are unaffected (their `google_sub` will be NULL; `hashed_password` remains set).

---

## Existing Table: `refresh_tokens` (unchanged)

The existing refresh token table is reused without schema changes. Google-authenticated sessions issue a `refresh_token` with a 30-day expiry (controlled via `REFRESH_TOKEN_EXPIRE_DAYS=30` environment variable).

---

## New Table: `google_link_requests` (temporary, optional)

Used during the account-linking confirmation flow. Holds a short-lived state token for the duration of the "Link your Google account?" prompt.

| Column | Type | Nullable | Notes |
|---|---|---|---|
| `id` | `VARCHAR(36)` | NO | UUID, PK |
| `state_token` | `VARCHAR(64)` | NO | Random token shown to user; expires in 10 minutes |
| `email` | `VARCHAR(255)` | NO | The email whose existing account would be linked |
| `google_sub` | `VARCHAR(255)` | NO | The Google subject identifier pending linking |
| `google_name` | `VARCHAR(255)` | YES | Display name from Google profile |
| `expires_at` | `TIMESTAMPTZ` | NO | 10 minutes from creation |
| `created_at` | `TIMESTAMPTZ` | NO | server_default `now()` |

**Note**: This table is only populated when a Google email matches an existing password-based account (the linking flow). It is cleaned up when the link is confirmed, declined, or expired. It can alternatively be implemented as a short-lived in-memory token (e.g., Redis or JWT) — the developer may choose based on infrastructure; a DB table is the default here for simplicity.

---

## Entity Relationships

```
auth_users
  ├── id (PK)
  ├── google_sub (nullable, unique) ← populated after Google sign-in
  ├── hashed_password (nullable) ← null for Google-only accounts
  └── ...

refresh_tokens
  └── user_id (FK → auth_users.id)

google_link_requests (transient)
  └── (no FK — holds pre-link state; deleted on resolution)
```

---

## State Transitions: User Authentication Path

```
New visitor
  │
  ├─ [No account + Google sign-in]
  │    → auto-create auth_users (google_sub set, hashed_password null)
  │    → issue refresh_token + access_token
  │    → SIGNED IN
  │
  ├─ [Existing Google account + Google sign-in]
  │    → lookup by google_sub OR email
  │    → issue new refresh_token + access_token
  │    → SIGNED IN
  │
  ├─ [Existing password account + Google sign-in with same email]
  │    → create google_link_requests row
  │    → show "Link your Google account?" prompt
  │    ├─ [Confirmed] → set google_sub on auth_users, delete link_request
  │    │               → issue refresh_token + access_token → SIGNED IN
  │    └─ [Declined]  → delete link_request → return to login page
  │
  └─ [Existing password account + username/password sign-in]
       → unchanged existing flow → SIGNED IN
```
