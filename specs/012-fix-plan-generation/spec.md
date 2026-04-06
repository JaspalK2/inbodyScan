# Feature Specification: Fix Plan Generation Availability

**Feature Branch**: `012-fix-plan-generation`  
**Created**: 2026-04-05  
**Status**: Draft  
**Input**: User description: "currently plan generation is showing up as temporarily unavailable, this has to be fixed."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Plan Generation Always Delivers a Plan (Priority: P1)

A user fills in their health goal and scan data, clicks "Generate Plan" (diet or workout), and receives a complete plan. Currently the system sometimes returns a "temporarily unavailable" error instead of a plan, blocking the user entirely. The plan generation must succeed reliably on every request, even if the AI-quality retry loop encounters rate limiting during its internal retries.

**Why this priority**: Core functionality — plan generation is the primary value of the application. Any failure here makes the app unusable.

**Independent Test**: Click "Generate Plan" for both diet and workout; verify a complete plan is displayed, never an error message, regardless of how many AI quality retry attempts are needed internally.

**Acceptance Scenarios**:

1. **Given** a user has scan data and a goal selected, **When** they click "Generate Plan", **Then** a full plan (diet or workout) is displayed within a reasonable wait time, with no error message shown.
2. **Given** the AI service returns a lower-quality response on its first attempt and the system retries internally, **When** a rate-limit error occurs on a subsequent retry attempt, **Then** the system still returns the best plan it already received rather than showing an error to the user.
3. **Given** the AI service is completely unreachable (e.g., API key invalid or total quota exhaustion), **When** the user tries to generate a plan, **Then** a clear, actionable error message is shown (e.g., "Service is currently busy — please try again in a few minutes").

---

### User Story 2 - Graceful Degradation with Clear User Feedback (Priority: P2)

When the plan generation service genuinely cannot produce a plan (e.g., the AI provider is fully down), the user receives a clear, friendly message that distinguishes a temporary delay from a permanent error, and knows to retry.

**Why this priority**: Improves user experience during unavoidable service disruptions; reduces confusion and abandonment.

**Independent Test**: Simulate complete AI service unavailability; verify a helpful, non-technical error message appears in the UI with a retry prompt.

**Acceptance Scenarios**:

1. **Given** the AI service is completely unavailable, **When** the user clicks "Generate Plan", **Then** a message is shown that explains the service is temporarily busy and suggests trying again.
2. **Given** a plan generation fails and shows an error, **When** the user clicks "Try Again", **Then** the generation is re-attempted without needing a full page reload.

---

### Edge Cases

- What happens if the AI returns a valid but incomplete plan (missing some days)?
- What happens if rate limiting is hit on the very first generation attempt?
- How does the system behave if both diet and workout are generated simultaneously by the same user?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The plan generation system MUST return a plan to the user whenever at least one valid AI response has been received, even if subsequent quality-improvement retries fail.
- **FR-002**: The system MUST NOT propagate internal rate-limit errors (from quality retry attempts) to the user as a "temporarily unavailable" failure when a valid plan was already generated.
- **FR-003**: If no valid AI response can be obtained at all (first attempt fails with rate limiting or total quota exhaustion), the system MUST return a clear, user-friendly error message.
- **FR-004**: The system MUST add a delay between AI retry attempts to reduce the likelihood of hitting rate limits during quality improvement retries.
- **FR-005**: The UI MUST provide a way for the user to retry plan generation after an error without reloading the page.
- **FR-006**: The error message shown to users MUST be friendly and non-technical, avoiding raw API error codes or internal exception names.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Plan generation succeeds (returns a plan, not an error) in 100% of cases where the AI service responds to at least one request successfully.
- **SC-002**: Users never see a "temporarily unavailable" error when a valid plan was already produced internally during quality retries.
- **SC-003**: When a genuine service outage occurs, 100% of error messages shown to users are friendly and include a retry suggestion.
- **SC-004**: The retry button works in 100% of cases — clicking it re-triggers generation without requiring a page reload.

## Assumptions

- The "temporarily unavailable" error is caused by the AI quality-retry loop hitting rate limits on the 2nd or 3rd internal attempt, not by total API quota exhaustion.
- The fix is primarily backend logic (preserve the first successful plan and use it as a fallback if retries fail) plus a small UI improvement (retry button on error state).
- No changes to the AI provider or API keys are needed to resolve the core issue.
- Both diet and workout plan generation share the same retry pattern and both need the same fix.
- The existing LLM client abstraction is retained; no provider switching is required for this fix.
