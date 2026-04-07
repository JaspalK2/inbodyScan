# Implementation Plan: Auth Display Name & Onboarding

**Branch**: `022-auth-name-onboarding` | **Date**: 2026-04-06 | **Spec**: specs/022-auth-name-onboarding/spec.md

## Summary

Add email/password registration to the login page (redirecting new users to Profile), fix the nav to show the user's real name from their profile, auto-populate first/last name from Google display name on first sign-in, and show a dismissible onboarding banner for authenticated users who have no name set yet.

## Technical Context

**Language/Version**: Python 3.13 (auth-service), TypeScript 5.x / Next.js 15 (frontend)
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0 async (backend); React 18, TanStack Query v5, Tailwind CSS, shadcn/ui (frontend)
**Storage**: Supabase PostgreSQL — no schema changes required
**Testing**: No new test files required (utility function is simple enough to validate in smoke tests)
**Target Platform**: Vercel (frontend), Railway/Fly (backend services)
**Project Type**: Web application (frontend + microservices backend)
**Performance Goals**: Nav name loads via TanStack Query deduplication — zero extra network calls
**Constraints**: sessionStorage for onboarding banner dismiss (clears on tab close, per spec)
**Scale/Scope**: Affects all authenticated users; additive changes only

## Constitution Check

- ✅ No new services or databases introduced
- ✅ No schema migrations (all columns already exist)
- ✅ Changes are additive and backward-compatible
- ✅ Existing users unaffected (name display falls back to username)

## Project Structure

### Documentation (this feature)

```text
specs/022-auth-name-onboarding/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── auth-register.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (affected files)

```text
services/
└── auth-service/
    └── src/
        └── routers/
            └── auth.py                         # Add email duplicate check to /register

frontend/
├── lib/
│   ├── parse-google-name.ts                    # NEW: parseGoogleName() utility
│   └── auth-context.tsx                        # Add register(); Google name auto-populate
├── components/
│   ├── nav.tsx                                 # Show first_name/last_name from profile query
│   └── onboarding-banner.tsx                   # NEW: dismissible banner (sessionStorage)
└── app/
    ├── (app)/
    │   └── layout.tsx                          # Include OnboardingBanner above content
    └── login/
        └── page.tsx                            # Sign In / Create Account toggle
```

## Implementation Notes

### 1. Email Duplicate Check (`auth.py`)
The existing `register` endpoint only checks username uniqueness. `get_user_by_email` already exists in `auth_service.py`. Add a call before creating the user; raise `HTTP 409 {"detail": "Email already registered"}` if found.

### 2. Nav Name Display (`nav.tsx`)
Add `useQuery(["profile"], userApi.getProfile)` directly in the Nav component. Display `${profile.first_name} ${profile.last_name ?? ""}`.trim()` or fall back to `user.username`. TanStack Query deduplicates — zero extra network calls when profile is already warm from other pages.

### 3. Google Name Auto-Populate (`auth-context.tsx`)
After successful Google login, if `googleName` is available from the response AND the fetched profile has no `first_name`, call `userApi.updateProfile({ first_name, last_name })` with the parsed name. Parsing via `parseGoogleName()`.

### 4. Name Parsing Utility (`parse-google-name.ts`)
Split on first space only. Single-word → `firstName` only, `lastName: null`. Empty string → no-op (caller skips the patch call).

### 5. Onboarding Banner (`onboarding-banner.tsx`)
Show when: authenticated AND `profile.first_name` is null/empty AND `sessionStorage["onboarding_dismissed"] !== "true"`. Dismiss sets sessionStorage key. Rendered in `app/(app)/layout.tsx` above main content.

### 6. Registration Form (`login/page.tsx`)
Toggle between "Sign In" and "Create Account" views. Registration form: username, email, password fields. On success: call `register()` from auth context, then `router.push("/profile")`. Inline errors for "Username already taken" (409) and "Email already registered" (409).

### 7. `register()` in Auth Context (`auth-context.tsx`)
Calls `POST /api/auth/register`, then immediately calls `POST /api/auth/login` to establish a session (register does not return a token). Sets user in context on success.
