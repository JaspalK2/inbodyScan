# Tasks: Auth Display Name & Onboarding

**Input**: Design documents from `/specs/022-auth-name-onboarding/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: No new project structure needed — all work modifies existing files or adds small new files.

- [X] T001 Verify `frontend/lib/auth-context.tsx` exports `register` function slot (read file to understand current shape before modifying)
- [X] T002 Verify `services/auth-service/src/routers/auth.py` register endpoint (read current implementation before modifying)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend email-duplicate check and frontend name-parsing utility — both are prerequisites for user story work.

- [X] T003 Add email uniqueness check to `POST /api/auth/register` in `services/auth-service/src/routers/auth.py`: call `get_user_by_email` before creating the user; raise `HTTP 409 {"detail": "Email already registered"}` if found
- [X] T004 [P] Create `frontend/lib/parse-google-name.ts`: export `function parseGoogleName(fullName: string): { firstName: string; lastName: string | null }` — split on first space; single-word → firstName only, lastName null; empty string → firstName "", lastName null

**Checkpoint**: Backend rejects duplicate emails; `parseGoogleName` utility is available.

---

## Phase 3: User Story 1 — Create Account via Email/Password (Priority: P1) 🎯 MVP

**Goal**: New users can register from the login page and are redirected to the Profile tab on success.

**Independent Test**: Go to `/login`, click "Create Account", fill username/email/password, submit → redirected to `/profile`. Try duplicate username → inline error. Try duplicate email → inline error.

### Implementation for User Story 1

- [X] T005 [US1] Add `register(username, email, password)` function to `frontend/lib/auth-context.tsx`: calls `POST /api/auth/register` then `POST /api/auth/login` to establish session; sets user in context on success; throws error with `detail` on 4xx so callers can display inline errors
- [X] T006 [US1] Update `frontend/app/login/page.tsx`: add state `mode: "signin" | "register"`; render "Create Account" / "Sign In Instead" toggle; when mode === "register" show three-field form (username, email, password) with client-side validation (password ≥ 8 chars); on submit call `auth.register()`; on success call `router.push("/profile")`; display inline error for 409 responses ("Username already taken" or "Email already registered")

**Checkpoint**: Email/password registration fully functional and redirecting to `/profile`.

---

## Phase 4: User Story 2 — Display Name in Navigation (Priority: P1)

**Goal**: Nav top-left shows `first_name last_name` (or username fallback) for all users.

**Independent Test**: Log in with an account that has `first_name` set → nav shows real name. Log in with no profile name → nav shows username. Update name in Profile tab → nav updates immediately without page reload.

### Implementation for User Story 2

- [X] T007 [US2] Update `frontend/components/nav.tsx`: add `useQuery(["profile"], userApi.getProfile)` (same key already used in profile and recommendations pages — TanStack Query deduplicates); replace the current `user?.username` display with `profile?.first_name ? \`${profile.first_name} ${profile.last_name ?? ""}\`.trim() : user?.username`

**Checkpoint**: Nav shows real name for users with profile data; falls back to username otherwise; updates reactively on profile save.

---

## Phase 5: User Story 3 — Auto-Populate Name from Google Sign-In (Priority: P2)

**Goal**: When a Google user signs in and has a display name, their profile first/last name is auto-set — no manual input required.

**Independent Test**: Sign in with Google account that has a full name → open Profile tab → `first_name` and `last_name` pre-populated. Sign in with an account that already has a manually set name → existing name not overwritten.

### Implementation for User Story 3

- [X] T008 [US3] Update `frontend/lib/auth-context.tsx` Google login handler: after successful `auth.googleLogin()` and fetching the profile via `userApi.getProfile()`, if `googleName` is non-empty AND `profile.first_name` is null/empty, call `parseGoogleName(googleName)` then `userApi.updateProfile({ first_name: parsed.firstName, last_name: parsed.lastName ?? undefined })` to populate the profile; import `parseGoogleName` from `../lib/parse-google-name`

**Checkpoint**: Google users with a display name see their profile pre-filled after first sign-in; existing names are never overwritten.

---

## Phase 6: User Story 4 — New User Profile Setup Prompt (Priority: P2)

**Goal**: Google users with no name see a dismissible onboarding banner on every session until they set their name; banner disappears once the name is set.

**Independent Test**: Sign in with Google (no display name) → banner visible on dashboard. Dismiss banner → banner gone for rest of session. Close tab, reopen → banner reappears. Set first name in Profile → banner gone permanently.

### Implementation for User Story 4

- [X] T009 [US4] Create `frontend/components/onboarding-banner.tsx`: render a dismissible banner when `user` is authenticated AND `profile?.first_name` is null/empty AND `sessionStorage.getItem("onboarding_dismissed") !== "true"`; clicking dismiss sets `sessionStorage.setItem("onboarding_dismissed", "true")` and hides the banner; banner includes a link to `/profile`; component reads the `["profile"]` query from TanStack Query cache (same key — no extra network call); returns `null` when condition not met
- [X] T010 [US4] Update `frontend/app/(app)/layout.tsx`: import `OnboardingBanner` and render it above the main content area (inside the authenticated layout wrapper)

**Checkpoint**: All four user stories fully implemented. Run all 9 quickstart.md smoke test scenarios to verify end-to-end.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T011 [P] Run `tsc --noEmit` in `frontend/` to verify no TypeScript errors introduced
- [X] T012 [P] Manual smoke test all 9 scenarios from `specs/022-auth-name-onboarding/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — read existing files to understand shape
- **Phase 2 (Foundational)**: Depends on Phase 1 reads; T003 and T004 are independent [P]
- **Phase 3 (US1)**: Depends on T003 (backend email check) and Phase 2 complete
- **Phase 4 (US2)**: Independent of US1 — can run in parallel with Phase 3
- **Phase 5 (US3)**: Depends on T004 (parseGoogleName utility)
- **Phase 6 (US4)**: Independent of US1/US3 — can run in parallel
- **Phase 7 (Polish)**: Depends on all phases complete

### User Story Dependencies

- **US1**: Depends on T003 (backend email duplicate check)
- **US2**: No dependencies on other stories — independently parallelizable after Phase 2
- **US3**: Depends on T004 (parseGoogleName utility)
- **US4**: No dependencies on other stories — independently parallelizable after Phase 2

### Parallel Opportunities

After Phase 2 completes, all four stories can proceed simultaneously:
- T005+T006 (US1 registration form)
- T007 (US2 nav name)
- T008 (US3 Google name populate)
- T009+T010 (US4 onboarding banner)

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 — both P1)

1. Phase 1: Read existing files
2. Phase 2: Backend email check + parseGoogleName utility
3. Phase 3: Registration form → redirect to Profile
4. Phase 4: Nav name display
5. **STOP and VALIDATE**: Smoke test scenarios 1–4 from quickstart.md

### Incremental Delivery

1. Setup + Foundational → backend + utility ready
2. US1 + US2 (both P1) → MVP: registration works, nav shows real name
3. US3 → Google auto-populate
4. US4 → Onboarding banner
5. Full smoke test all 9 scenarios

---

## Notes

- No database migrations — `first_name` and `last_name` columns already exist in `user_profiles`
- TanStack Query key `["profile"]` is already used in multiple pages — adding it to Nav deduplicates (zero extra network calls)
- `sessionStorage` clears on tab close — correct behaviour for "reappears next session" requirement
- Google name auto-populate only runs when `profile.first_name` is null/empty — never overwrites existing manually set names
- `register()` in auth-context calls `/register` then `/login` immediately (register endpoint does not return a token)
