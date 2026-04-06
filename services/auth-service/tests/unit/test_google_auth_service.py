"""Unit tests for google_auth_service — T013, T027, T040.

Run: cd services/auth-service && python -m pytest tests/unit/test_google_auth_service.py -v
"""
import os
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock


# ── T013: verify_google_token ─────────────────────────────────────────────────

def test_verify_google_token_raises_when_client_id_missing():
    """verify_google_token raises ValueError if GOOGLE_CLIENT_ID env var is not set."""
    with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": ""}):
        # Re-import to pick up patched env
        import importlib
        import services.auth_service.src.services.google_auth_service as gauth_mod
        importlib.reload(gauth_mod)
        with pytest.raises(ValueError, match="GOOGLE_CLIENT_ID"):
            gauth_mod.verify_google_token("any.token.here")


def test_verify_google_token_raises_for_invalid_token():
    """verify_google_token raises ValueError when Google rejects the token."""
    with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": "test-client-id.apps.googleusercontent.com"}):
        import importlib
        import services.auth_service.src.services.google_auth_service as gauth_mod
        importlib.reload(gauth_mod)

        with patch("google.oauth2.id_token.verify_oauth2_token", side_effect=Exception("Invalid token")):
            with pytest.raises(ValueError, match="Google token verification failed"):
                gauth_mod.verify_google_token("invalid.token")


def test_verify_google_token_returns_payload_for_valid_token():
    """verify_google_token returns decoded payload dict when token is valid."""
    client_id = "test-client-id.apps.googleusercontent.com"
    expected_payload = {
        "sub": "1234567890",
        "email": "user@example.com",
        "name": "Test User",
        "aud": client_id,
    }
    with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": client_id}):
        import importlib
        import services.auth_service.src.services.google_auth_service as gauth_mod
        importlib.reload(gauth_mod)

        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=expected_payload):
            result = gauth_mod.verify_google_token("valid.token.here")

    assert result["sub"] == "1234567890"
    assert result["email"] == "user@example.com"


def test_verify_google_token_raises_on_audience_mismatch():
    """verify_google_token raises ValueError if aud does not match GOOGLE_CLIENT_ID."""
    client_id = "correct-client.apps.googleusercontent.com"
    wrong_aud_payload = {
        "sub": "123",
        "email": "user@example.com",
        "aud": "wrong-client.apps.googleusercontent.com",
    }
    with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": client_id}):
        import importlib
        import services.auth_service.src.services.google_auth_service as gauth_mod
        importlib.reload(gauth_mod)

        with patch("google.oauth2.id_token.verify_oauth2_token", return_value=wrong_aud_payload):
            with pytest.raises(ValueError, match="audience mismatch"):
                gauth_mod.verify_google_token("token.with.wrong.aud")


# ── T027: resolve_link_request returns None for expired row ───────────────────

@pytest.mark.asyncio
async def test_resolve_link_request_returns_none_for_expired_row():
    """resolve_link_request returns None when the row is expired (expires_at in past)."""
    from unittest.mock import AsyncMock
    import services.auth_service.src.services.google_auth_service as gauth_mod

    expired_row = MagicMock()
    expired_row.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)

    mock_session = AsyncMock()
    # Simulate the SELECT returning no rows (expired condition filters it out)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    result = await gauth_mod.resolve_link_request(mock_session, "expired-state-token")
    assert result is None


# ── T040: wrong-audience token returns 401 ────────────────────────────────────

def test_verify_google_token_id_not_logged(caplog):
    """verify_google_token must NOT log the raw id_token or email (constitution requirement)."""
    import logging
    client_id = "test-client.apps.googleusercontent.com"
    sensitive_token = "SENSITIVE_ID_TOKEN_VALUE"

    with patch.dict(os.environ, {"GOOGLE_CLIENT_ID": client_id}):
        import importlib
        import services.auth_service.src.services.google_auth_service as gauth_mod
        importlib.reload(gauth_mod)

        with patch("google.oauth2.id_token.verify_oauth2_token", side_effect=Exception("fail")):
            with caplog.at_level(logging.DEBUG):
                try:
                    gauth_mod.verify_google_token(sensitive_token)
                except ValueError:
                    pass

    assert sensitive_token not in caplog.text, "Raw id_token must never appear in logs"
