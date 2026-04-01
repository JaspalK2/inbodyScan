"""Tests for auth-service: user creation, login, JWT, password hashing."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from ..services.auth_service import (
    hash_password, verify_password, create_access_token,
    create_refresh_token_value, hash_token,
)


class TestPasswordHashing:
    def test_hash_password_returns_non_plaintext(self):
        plain = "SecurePass123"
        hashed = hash_password(plain)
        assert hashed != plain
        assert len(hashed) > 20

    def test_verify_password_correct(self):
        plain = "SecurePass123"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("correct")
        assert verify_password("wrong", hashed) is False


class TestJWT:
    def test_create_access_token_returns_string(self, monkeypatch):
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-32-chars-long-xxxxxx")
        import importlib
        import services.auth_service.src.services.auth_service as svc
        importlib.reload(svc)
        token = svc.create_access_token("user-123", False)
        assert isinstance(token, str)
        assert len(token) > 10

    def test_create_access_token_admin(self, monkeypatch):
        import jwt
        monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-32-chars-long-xxxxxx")
        monkeypatch.setenv("JWT_ALGORITHM", "HS256")
        token = create_access_token("user-admin", True)
        payload = jwt.decode(token, "test-secret-32-chars-long-xxxxxx", algorithms=["HS256"])
        assert payload["is_admin"] is True
        assert payload["sub"] == "user-admin"


class TestRefreshToken:
    def test_refresh_token_value_is_unique(self):
        t1 = create_refresh_token_value()
        t2 = create_refresh_token_value()
        assert t1 != t2

    def test_hash_token_is_deterministic(self):
        token = "some-refresh-token-value"
        assert hash_token(token) == hash_token(token)

    def test_hash_token_different_values(self):
        assert hash_token("a") != hash_token("b")
