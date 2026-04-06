# API Contract: Google OAuth Endpoints

**Feature**: `003-google-oauth-login`
**Service**: `auth-service`
**Base path**: `/api/auth`

---

## POST `/api/auth/google`

Verifies a Google-issued ID token server-side. On success, creates or retrieves the user account and issues the standard session credentials (access token + refresh cookie). On email conflict with an existing password account, returns a `link_token` for the confirmation flow instead.

### Request

```json
{
  "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6..."
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `id_token` | `string` | YES | Raw Google ID token returned by the GIS client-side library (`credential` field from the `CredentialResponse`) |

### Responses

**201 Created** — New account created and signed in:
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```
Also sets `Set-Cookie: refresh_token=<value>; HttpOnly; Secure; SameSite=Strict; Max-Age=2592000`

**200 OK** — Existing Google account signed in:
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```
Also sets refresh cookie (same as above).

**202 Accepted** — Email matches an existing password-based account; confirmation required:
```json
{
  "link_token": "<opaque-token>",
  "email": "user@example.com",
  "google_name": "Jane Smith"
}
```
No session is established yet. Frontend must show the linking confirmation UI.

**400 Bad Request** — Missing or malformed `id_token`.

**401 Unauthorized** — Google token failed server-side verification (expired, wrong audience, invalid signature):
```json
{ "detail": "Google token verification failed" }
```

**403 Forbidden** — User account is disabled:
```json
{ "detail": "Account disabled" }
```

---

## POST `/api/auth/google/confirm-link`

Completes the account-linking flow after the user confirms. Accepts the `link_token` issued by `POST /api/auth/google` when a conflict was detected.

### Request

```json
{
  "link_token": "<opaque-token>"
}
```

### Responses

**200 OK** — Google identity linked; session issued:
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```
Also sets refresh cookie.

**400 Bad Request** — `link_token` missing.

**404 Not Found** — `link_token` not found or already used.

**410 Gone** — `link_token` expired (10-minute TTL):
```json
{ "detail": "Link request expired. Please sign in with Google again." }
```

---

## Existing Endpoints (unchanged)

All existing endpoints remain unchanged:

| Endpoint | Notes |
|---|---|
| `POST /api/auth/login` | Username/password login — unchanged |
| `POST /api/auth/register` | Username/password registration — unchanged |
| `POST /api/auth/refresh` | Refresh token exchange — unchanged |
| `POST /api/auth/logout` | Session invalidation — unchanged |
| `GET /api/auth/me` | Current user profile — unchanged, now may return `google_sub` if added to `UserOut` |

---

## Frontend API Client Additions (`frontend/lib/api.ts`)

```typescript
// New types
interface GoogleLoginResponse {
  access_token?: string;
  token_type?: string;
  link_token?: string;
  email?: string;
  google_name?: string;
}

// New functions on `auth` object
googleLogin: (idToken: string) => Promise<GoogleLoginResponse>
confirmGoogleLink: (linkToken: string) => Promise<{ access_token: string }>
```
