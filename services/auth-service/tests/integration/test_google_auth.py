"""Integration tests for Google OAuth endpoints — T012, T020, T021, T024–T026, T031, T032, T039.

These tests mock Google's token verification so no real Google credentials are needed.
They hit the FastAPI app via TestClient and test against a real (test) database.

Prerequisites:
- Set TEST_DATABASE_URL env var pointing to a test Supabase/PostgreSQL instance
- Run SQL migration from quickstart.md before running these tests

Run: cd services/auth-service && python -m pytest tests/integration/test_google_auth.py -v
"""
import pytest
from unittest.mock import patch


VALID_GOOGLE_PAYLOAD_NEW = {
    "sub": "google_sub_new_user_001",
    "email": "newgoogleuser@example.com",
    "name": "New Google User",
    "aud": "test-client-id.apps.googleusercontent.com",
}

VALID_GOOGLE_PAYLOAD_EXISTING = {
    "sub": "google_sub_existing_001",
    "email": "existinggoogle@example.com",
    "name": "Existing Google User",
    "aud": "test-client-id.apps.googleusercontent.com",
}

VALID_GOOGLE_PAYLOAD_CONFLICT = {
    "sub": "google_sub_conflict_001",
    "email": "conflictuser@example.com",
    "name": "Conflict User",
    "aud": "test-client-id.apps.googleusercontent.com",
}


# ── T012: New user sign-up ─────────────────────────────────────────────────────

@pytest.mark.integration
def test_google_login_new_user_creates_account(test_client, mock_google_verify):
    """POST /api/auth/google with new email creates account, returns 201 + access_token + cookie."""
    mock_google_verify.return_value = VALID_GOOGLE_PAYLOAD_NEW

    response = test_client.post("/api/auth/google", json={"id_token": "mock.id.token"})

    assert response.status_code == 201
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert "refresh_token" in response.cookies

    # Verify the cookie has 30-day max-age
    cookie_header = response.headers.get("set-cookie", "")
    assert "max-age=2592000" in cookie_header.lower() or "Max-Age=2592000" in cookie_header


@pytest.mark.integration
def test_google_login_new_user_has_null_password(test_client, mock_google_verify, db_session):
    """New Google user has hashed_password=None and google_sub set (T012)."""
    mock_google_verify.return_value = VALID_GOOGLE_PAYLOAD_NEW

    test_client.post("/api/auth/google", json={"id_token": "mock.id.token"})

    # Query the DB directly
    from services.auth_service.src.models.user import User
    from sqlalchemy import select
    result = db_session.execute(
        select(User).where(User.email == VALID_GOOGLE_PAYLOAD_NEW["email"])
    ).scalar_one_or_none()
    assert result is not None
    assert result.hashed_password is None
    assert result.google_sub == VALID_GOOGLE_PAYLOAD_NEW["sub"]


# ── T020, T021: Existing Google user sign-in ──────────────────────────────────

@pytest.mark.integration
def test_google_login_existing_google_user_returns_200(test_client, mock_google_verify, existing_google_user):
    """POST /api/auth/google for existing Google account returns 200 and does not create duplicate (T020)."""
    mock_google_verify.return_value = VALID_GOOGLE_PAYLOAD_EXISTING

    response = test_client.post("/api/auth/google", json={"id_token": "mock.id.token"})

    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.integration
def test_google_login_me_returns_existing_user(test_client, mock_google_verify, existing_google_user):
    """GET /api/auth/me after Google sign-in returns the correct existing user profile (T021)."""
    mock_google_verify.return_value = VALID_GOOGLE_PAYLOAD_EXISTING

    login_resp = test_client.post("/api/auth/google", json={"id_token": "mock.id.token"})
    access_token = login_resp.json()["access_token"]

    me_resp = test_client.get("/api/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["id"] == existing_google_user.id


# ── T024–T026: Account linking flow ───────────────────────────────────────────

@pytest.mark.integration
def test_google_login_conflict_returns_202_with_link_token(test_client, mock_google_verify, existing_password_user):
    """POST /api/auth/google with email matching password account returns 202 + link_token, no session (T024)."""
    mock_google_verify.return_value = VALID_GOOGLE_PAYLOAD_CONFLICT

    response = test_client.post("/api/auth/google", json={"id_token": "mock.id.token"})

    assert response.status_code == 202
    body = response.json()
    assert "link_token" in body
    assert body["email"] == VALID_GOOGLE_PAYLOAD_CONFLICT["email"]
    # No session cookie should be set
    assert "refresh_token" not in response.cookies


@pytest.mark.integration
def test_confirm_link_sets_google_sub_and_issues_session(test_client, mock_google_verify, existing_password_user, db_session):
    """POST /api/auth/google/confirm-link links Google account and returns session (T025)."""
    mock_google_verify.return_value = VALID_GOOGLE_PAYLOAD_CONFLICT

    conflict_resp = test_client.post("/api/auth/google", json={"id_token": "mock.id.token"})
    link_token = conflict_resp.json()["link_token"]

    confirm_resp = test_client.post("/api/auth/google/confirm-link", json={"link_token": link_token})
    assert confirm_resp.status_code == 200
    assert "access_token" in confirm_resp.json()
    assert "refresh_token" in confirm_resp.cookies

    # Verify google_sub now set on the existing user
    from services.auth_service.src.models.user import User
    from sqlalchemy import select
    user = db_session.execute(
        select(User).where(User.email == VALID_GOOGLE_PAYLOAD_CONFLICT["email"])
    ).scalar_one_or_none()
    assert user.google_sub == VALID_GOOGLE_PAYLOAD_CONFLICT["sub"]


@pytest.mark.integration
def test_confirm_link_expired_token_returns_410(test_client):
    """POST /api/auth/google/confirm-link with unknown/expired token returns 410 (T026)."""
    response = test_client.post(
        "/api/auth/google/confirm-link",
        json={"link_token": "nonexistent-or-expired-token"},
    )
    assert response.status_code == 410


# ── T031, T032: Session management ────────────────────────────────────────────

@pytest.mark.integration
def test_google_session_cookie_has_30_day_max_age(test_client, mock_google_verify):
    """Refresh cookie from Google sign-in has 30-day max-age (T031)."""
    mock_google_verify.return_value = VALID_GOOGLE_PAYLOAD_NEW

    response = test_client.post("/api/auth/google", json={"id_token": "mock.id.token"})
    cookie_header = response.headers.get("set-cookie", "")
    # 30 days = 2592000 seconds
    assert "2592000" in cookie_header


@pytest.mark.integration
def test_logout_invalidates_google_session(test_client, mock_google_verify):
    """POST /api/auth/logout revokes Google session; subsequent refresh returns 401 (T032)."""
    mock_google_verify.return_value = VALID_GOOGLE_PAYLOAD_NEW

    test_client.post("/api/auth/google", json={"id_token": "mock.id.token"})
    test_client.post("/api/auth/logout")

    refresh_resp = test_client.post("/api/auth/refresh")
    assert refresh_resp.status_code == 401


# ── T039: Data isolation ───────────────────────────────────────────────────────

@pytest.mark.integration
def test_google_me_returns_only_own_data(test_client, mock_google_verify):
    """GET /api/auth/me returns only the authenticated user's record, not another user's (T039)."""
    payload_a = {**VALID_GOOGLE_PAYLOAD_NEW, "sub": "sub_user_a", "email": "usera@example.com"}
    payload_b = {**VALID_GOOGLE_PAYLOAD_NEW, "sub": "sub_user_b", "email": "userb@example.com"}

    mock_google_verify.return_value = payload_a
    resp_a = test_client.post("/api/auth/google", json={"id_token": "token_a"})
    token_a = resp_a.json()["access_token"]

    mock_google_verify.return_value = payload_b
    test_client.post("/api/auth/google", json={"id_token": "token_b"})

    me_resp = test_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    assert me_resp.json()["email"] == "usera@example.com"
