"""Unit tests for Google user functions in auth_service — T014.

Run: cd services/auth-service && python -m pytest tests/unit/test_auth_service_google.py -v
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_create_google_user_sets_google_sub_and_null_password():
    """create_google_user creates user with hashed_password=None and google_sub set (T014)."""
    from unittest.mock import AsyncMock, call
    import services.auth_service.src.services.auth_service as auth_mod

    mock_session = AsyncMock()
    # get_user_by_username returns None (no collision)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result
    mock_session.refresh = AsyncMock()

    google_sub = "abcdefgh12345678"
    email = "newuser@google.com"

    # Capture the User that gets added to the session
    added_users = []

    def capture_add(obj):
        added_users.append(obj)

    mock_session.add.side_effect = capture_add

    await auth_mod.create_google_user(mock_session, email, google_sub)

    assert len(added_users) == 1
    user = added_users[0]
    assert user.hashed_password is None
    assert user.google_sub == google_sub
    assert user.email == email
    # Username must start with google_ followed by first 8 chars of sub
    assert user.username == f"google_{google_sub[:8]}"


@pytest.mark.asyncio
async def test_create_google_user_auto_generates_unique_username():
    """create_google_user appends suffix if auto-generated username is already taken (T014)."""
    import services.auth_service.src.services.auth_service as auth_mod
    from services.auth_service.src.models.user import User

    google_sub = "abcdefgh12345678"
    base_username = f"google_{google_sub[:8]}"

    # First call (username check) returns an existing user — collision
    existing_user = MagicMock(spec=User)
    existing_user.username = base_username

    mock_session = AsyncMock()
    call_count = 0

    async def mock_execute(stmt):
        nonlocal call_count
        mock_result = MagicMock()
        if call_count == 0:
            # First username check — returns existing (collision)
            mock_result.scalar_one_or_none.return_value = existing_user
        else:
            # Second username check — no collision
            mock_result.scalar_one_or_none.return_value = None
        call_count += 1
        return mock_result

    mock_session.execute.side_effect = mock_execute
    mock_session.refresh = AsyncMock()

    added_users = []
    mock_session.add.side_effect = lambda obj: added_users.append(obj)

    await auth_mod.create_google_user(mock_session, "email@test.com", google_sub)

    assert len(added_users) == 1
    # Username should have a suffix to avoid collision
    assert added_users[0].username != base_username
    assert added_users[0].username.startswith(base_username)
