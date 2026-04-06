# Quickstart: Google OAuth Login & Sign-Up

**Feature**: `003-google-oauth-login`
**Date**: 2026-04-02

---

## Prerequisites

1. **Google Cloud Project**: Create (or reuse) a project at [console.cloud.google.com](https://console.cloud.google.com).
2. **OAuth Client ID**: Under APIs & Services → Credentials, create a new OAuth 2.0 Client ID of type "Web application."
   - Add Authorized JavaScript origins: `http://localhost:3000` (dev), your production domain.
   - Add Authorized redirect URIs: not required for the GIS One Tap / popup flow, but add `http://localhost:3000` as origin.
3. **Copy Client ID**: You'll need it as `NEXT_PUBLIC_GOOGLE_CLIENT_ID` (frontend) and `GOOGLE_CLIENT_ID` (backend).

---

## Database Migration

Run the following SQL against your Supabase database to prepare the schema:

```sql
-- 1. Make hashed_password nullable (Google-only accounts have no password)
ALTER TABLE auth_users
  ALTER COLUMN hashed_password DROP NOT NULL;

-- 2. Add Google subject identifier column
ALTER TABLE auth_users
  ADD COLUMN IF NOT EXISTS google_sub VARCHAR(255) UNIQUE;

CREATE INDEX IF NOT EXISTS idx_auth_users_google_sub ON auth_users(google_sub);

-- 3. Create transient link-request table
CREATE TABLE IF NOT EXISTS google_link_requests (
  id           VARCHAR(36)  PRIMARY KEY,
  state_token  VARCHAR(64)  NOT NULL UNIQUE,
  email        VARCHAR(255) NOT NULL,
  google_sub   VARCHAR(255) NOT NULL,
  google_name  VARCHAR(255),
  expires_at   TIMESTAMPTZ  NOT NULL,
  created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_google_link_requests_state_token
  ON google_link_requests(state_token);
CREATE INDEX IF NOT EXISTS idx_google_link_requests_expires_at
  ON google_link_requests(expires_at);
```

---

## Environment Variables

### Frontend (`frontend/.env.local`)

```
NEXT_PUBLIC_GOOGLE_CLIENT_ID=<your-google-client-id>.apps.googleusercontent.com
```

### Auth Service (`services/auth-service/.env`)

```
GOOGLE_CLIENT_ID=<your-google-client-id>.apps.googleusercontent.com
REFRESH_TOKEN_EXPIRE_DAYS=30   # for Google sessions; password sessions keep 7
```

---

## New Dependencies

### Frontend

```bash
npm install @react-oauth/google
# License: Apache 2.0 ✅
```

### Auth Service

```bash
pip install google-auth==2.37.0
# License: Apache 2.0 ✅
# Add to services/auth-service/requirements.txt
```

---

## Validation Scenarios

Run these manually after implementation to confirm the feature works end-to-end.

### Scenario 1: New user signs up via Google
1. Open the app with no existing account.
2. Click "Continue with Google."
3. Complete Google consent.
4. **Expected**: Land on `/dashboard`; user profile shows Google name and email; a new row in `auth_users` with `google_sub` set and `hashed_password` null.

### Scenario 2: Returning Google user signs in
1. Sign out from the account created in Scenario 1.
2. Click "Continue with Google."
3. **Expected**: Signed back into the same account (same `id`); no new row created.

### Scenario 3: Account linking prompt
1. Register a new account via username/password using email `test@example.com`.
2. Sign out.
3. Click "Continue with Google" using a Google account with email `test@example.com`.
4. **Expected**: See prompt "An account with this email exists. Link your Google account?" with Confirm/Cancel.

### Scenario 4: Account linking confirmed
1. Continue from Scenario 3, click "Confirm."
2. **Expected**: Signed in; the existing `auth_users` row now has `google_sub` set; password login still works for this account.

### Scenario 5: Account linking declined
1. Continue from Scenario 3, click "Cancel."
2. **Expected**: Returned to login page; no `google_sub` set on the existing account; no new account created.

### Scenario 6: Google consent cancelled
1. Click "Continue with Google."
2. Click "Cancel" on the Google consent screen.
3. **Expected**: Returned to login page; no account created; no error crash.

### Scenario 7: Session persistence
1. Sign in via Google.
2. Close and reopen the browser.
3. Navigate to `http://localhost:3000/dashboard`.
4. **Expected**: Still signed in; no re-authentication prompt.

### Scenario 8: Session expiry protection
1. Sign in via Google.
2. Manually delete the `refresh_token` cookie (DevTools → Application → Cookies).
3. Reload the page.
4. **Expected**: Redirected to login page.

### Scenario 9: Existing password login unchanged
1. Register via username/password.
2. Sign out.
3. Sign in again with username/password.
4. **Expected**: Normal login; "Continue with Google" button visible but not required.
