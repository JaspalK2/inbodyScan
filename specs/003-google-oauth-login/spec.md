# Feature Specification: Google OAuth Login & Sign-Up

**Feature Branch**: `003-google-oauth-login`
**Created**: 2026-04-02
**Status**: Draft
**Input**: User description: "As a user, needing to create an account with a username and password is not effective, I would like to be able to continue a login / sign up via google accounts. The user should be able to create an account with their google account, which can then be used in the future to sign in to the web app whenever they see fit."

## Clarifications

### Session 2026-04-02

- Q: When a user who previously registered with email/password tries Google sign-in with the same email, how should the system handle account linking? → A: Prompt to confirm — show "An account with this email exists. Link your Google account?" before merging.
- Q: How long should a Google-authenticated session remain valid before requiring re-authentication? → A: 30 days rolling — refreshes on each visit, expires after 30 days of inactivity.
- Q: When a user revokes the app's Google access, should the app detect and invalidate their active session? → A: Detect on next sign-in only — existing sessions remain valid until expiry; revocation takes effect only when the user attempts to sign in again.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — New User Signs Up via Google (Priority: P1)

A visitor arrives at the app with no existing account. Instead of filling in an email/password form, they click "Continue with Google," are redirected to Google's authorization screen, consent to sharing their profile, and land back on the app fully authenticated with a new account automatically created.

**Why this priority**: This is the core unlock of the feature. Without it, no Google-based identity exists in the system, so sign-in is impossible. It is the entry point for all new users who prefer Google.

**Independent Test**: Open the app without an account, click "Continue with Google," complete the Google consent flow, and confirm you land on the main app page with your Google name and email shown — all without ever typing a password.

**Acceptance Scenarios**:

1. **Given** a visitor with no account, **When** they click "Continue with Google" and approve the consent screen, **Then** a new user account is created and they are signed into the app.
2. **Given** a new user who has just signed up via Google, **When** they view their profile, **Then** their name and email match those from their Google account.
3. **Given** a visitor who cancels the Google consent screen, **When** they return to the app, **Then** they are shown the login page with no account created and no error crash.
4. **Given** a visitor whose Google email matches an existing password-based account, **When** they click "Continue with Google" and complete the consent flow, **Then** they are shown a prompt to confirm account linking; if confirmed, they are signed in with Google now linked; if declined, they are returned to the login page with no duplicate account created.

---

### User Story 2 — Existing User Signs In via Google (Priority: P1)

A user who has previously registered via Google returns to the app and signs in with one click on "Continue with Google," without entering any credentials.

**Why this priority**: Equal priority with sign-up — a sign-in flow that fails for returning users makes the whole feature useless after the first session.

**Independent Test**: Register via Google, log out, return, click "Continue with Google," and confirm you land on your existing account with all prior data intact.

**Acceptance Scenarios**:

1. **Given** a user with an existing Google-linked account, **When** they click "Continue with Google" and approve, **Then** they are signed in to their existing account and redirected to the main app.
2. **Given** a user whose Google session has expired, **When** they attempt to sign in, **Then** they are prompted to re-authenticate with Google before entering the app.

---

### User Story 3 — Secure Session Management (Priority: P2)

After signing in via Google, the user's session persists across page refreshes and browser restarts, and they can sign out cleanly at any time.

**Why this priority**: Without session persistence, the P1 flows break after the first page reload. It is foundational to usability but depends on P1 working first.

**Independent Test**: Sign in via Google, close and reopen the browser, navigate to the app, and confirm you remain signed in. Then sign out and confirm protected pages are no longer accessible.

**Acceptance Scenarios**:

1. **Given** a signed-in user, **When** they close and reopen the browser, **Then** they remain signed in.
2. **Given** a signed-in user, **When** they click "Sign Out," **Then** their session is invalidated and they are redirected to the login page.
3. **Given** a signed-out user, **When** they navigate directly to a protected route, **Then** they are redirected to the login page.

---

### Edge Cases

- What happens when Google's authorization server is temporarily unavailable? → User sees a friendly error and can retry; no partial account state is left.
- What happens when the Google identity token has an invalid or expired signature? → The backend rejects authentication, and the user is returned to the login page with an error message.
- What happens when a user revokes the app's Google access from their Google account settings? → Existing active sessions continue until they naturally expire (30-day rolling); revocation is detected only on the user's next sign-in attempt, at which point the sign-in fails and the user is informed their Google access was revoked.
- What happens if a user registered with email/password first and later tries Google sign-in with the same email? → The system shows a confirmation prompt ("An account with this email exists. Link your Google account?"). If confirmed, the Google identity is linked to the existing account and no duplicate is created. If declined, the user is returned to the login page.
- What happens when the user denies the email/profile scope during consent? → Sign-in fails gracefully with a user-friendly explanation that profile access is required.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The login/sign-up page MUST display a "Continue with Google" button that initiates the Google OAuth authorization flow.
- **FR-002**: When a user successfully completes the Google OAuth flow for the first time, the system MUST automatically create a new user account using the verified name and email from their Google profile.
- **FR-003**: When a user successfully completes the Google OAuth flow and an account with the same email already exists (password-based), the system MUST show a confirmation prompt asking the user to link their Google account to the existing account. If confirmed, the Google identity is linked and the user is signed in; if declined, the user is returned to the login page. No duplicate account is ever created.
- **FR-004**: The system MUST verify the Google-issued identity token on the server before establishing a user session — client-supplied identity claims MUST NOT be trusted without server-side verification.
- **FR-005**: After successful Google sign-in, the system MUST issue a session credential that persists across page reloads.
- **FR-006**: The system MUST provide a "Sign Out" action that invalidates the active session and redirects the user to the login page.
- **FR-007**: Users MUST be redirected to the login page when accessing any protected route without a valid session.
- **FR-008**: The system MUST handle Google OAuth errors (user cancelled, network failure, invalid token) gracefully and display a user-friendly message without crashing.
- **FR-009**: User accounts created via Google MUST store the Google subject identifier so future sign-ins can match the same identity reliably, even if the user changes their Google email display name.
- **FR-010**: The existing email/password login flow MUST continue to work alongside Google sign-in — both paths must coexist on the login page.

### Key Entities

- **User**: Represents a registered app user. Key attributes: unique ID, email, display name, avatar URL, Google subject identifier, account creation timestamp, last sign-in timestamp.
- **Session**: An active authenticated context for a user. Attributes: session token, user ID, expiry time. Invalidated on sign-out.
- **Google Identity**: The verified identity claim returned by Google during the OAuth flow. Transient — used to create or look up a User; not stored beyond the subject identifier and email.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A new user can complete account creation and reach the main app in under 30 seconds from clicking "Continue with Google."
- **SC-002**: A returning user can sign in in under 10 seconds from clicking "Continue with Google" (assuming active Google session in the browser).
- **SC-003**: Zero duplicate accounts are created when the same Google identity initiates sign-up more than once.
- **SC-004**: 100% of authentication decisions are validated server-side — no user session is established based solely on client-supplied identity data.
- **SC-005**: After signing out, 100% of subsequent requests to protected routes are rejected until a new sign-in occurs.
- **SC-006**: Google sign-in works correctly on the latest two major versions of Chrome, Safari, Firefox, and Edge.
- **SC-007**: A signed-in user who visits the app within 30 days of their last activity remains signed in without re-authentication; after 30 days of inactivity the session is expired and they must sign in again.

---

## Assumptions

- The app already has a working email/password authentication system that will continue to operate alongside Google sign-in.
- Users are assumed to have an active Google account they are willing to use for app sign-in.
- Email is the primary identifier for deduplication — a Google account with the same email as an existing password-based account maps to that existing user record.
- The app is a web application accessible via a browser; mobile-native Google Sign-In SDK flows (Android/iOS) are out of scope for this feature.
- This implementation will target the current Google Identity Services (GIS) SDK, not the deprecated legacy Google Sign-In JS library (`gapi.auth2`).
- Users who sign up via Google are not required to set a password; password-based sign-in remains optional for them.
- Session duration is 30 days rolling — the session refreshes on each visit and expires only after 30 consecutive days of inactivity. This applies to sessions established via Google sign-in.
- A Google Cloud project and OAuth client credentials (Client ID) must be created and configured before implementation can begin.
