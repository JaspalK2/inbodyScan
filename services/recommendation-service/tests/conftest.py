"""Shared pytest fixtures for recommendation-service tests."""
from __future__ import annotations
import os
import sys
import uuid
import pytest
import pytest_asyncio

# Ensure repo root is on sys.path so `shared` package resolves (mirrors src/main.py which does ../../..)
# tests/ is 3 levels below repo root: services/recommendation-service/tests/
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# Set required env vars before any app imports
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing-only")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("GOOGLE_API_KEY", "test-api-key")
# Load env vars from root .env so the app can create its DB engine at import time.
_ENV_FILE = os.path.join(_REPO_ROOT, ".env")
if os.path.exists(_ENV_FILE):
    with open(_ENV_FILE) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip())


def _make_token(user_id: str) -> str:
    import jwt as pyjwt
    return pyjwt.encode(
        {"sub": user_id, "type": "access"},
        os.environ["JWT_SECRET_KEY"],
        algorithm=os.environ["JWT_ALGORITHM"],
    )


@pytest.fixture
def user_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def other_user_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def auth_headers(user_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {_make_token(user_id)}"}


@pytest.fixture
def other_user_headers(other_user_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {_make_token(other_user_id)}"}


requires_db = pytest.mark.skipif(
    not os.environ.get("RECOMMENDATION_DATABASE_URL"),
    reason="Requires RECOMMENDATION_DATABASE_URL (real asyncpg connection)",
)


@pytest_asyncio.fixture
async def created_workout_rec(auth_headers: dict[str, str], user_id: str) -> dict:
    """Create a WorkoutRecommendation row via the generate endpoint (uses the real DB stack)."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))
    from src.main import app
    from httpx import AsyncClient, ASGITransport
    from unittest.mock import patch, AsyncMock
    import json

    fake_plan = json.dumps({"summary": "test", "weeks": [], "progression_notes": ""})
    with patch(
        "google.generativeai.GenerativeModel.generate_content_async",
        new=AsyncMock(return_value=type("R", (), {"text": fake_plan})()),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/recommendations/workout/generate",
                json={"scan_id": "test-scan", "metrics": {"weight": 80.0}, "goal_type": "muscle_gain"},
                headers=auth_headers,
            )
    assert resp.status_code == 201, f"Setup failed: {resp.text}"
    data = resp.json()
    return {"id": data["id"], "user_id": data["user_id"]}


@pytest_asyncio.fixture
async def created_diet_rec(auth_headers: dict[str, str], user_id: str) -> dict:
    """Create a DietRecommendation row via the generate endpoint (uses the real DB stack)."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../src"))
    from src.main import app
    from httpx import AsyncClient, ASGITransport
    from unittest.mock import patch, AsyncMock
    import json

    fake_plan = json.dumps({"summary": "test", "days": [], "daily_targets": {}, "macro_targets": {}})
    with patch(
        "google.generativeai.GenerativeModel.generate_content_async",
        new=AsyncMock(return_value=type("R", (), {"text": fake_plan})()),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/recommendations/diet/generate",
                json={"scan_id": "test-scan", "metrics": {"weight": 80.0}, "goal_type": "muscle_gain",
                      "dietary_restrictions": [], "age": 28, "height_cm": 175.0, "gender": "male"},
                headers=auth_headers,
            )
    assert resp.status_code == 201, f"Setup failed: {resp.text}"
    data = resp.json()
    return {"id": data["id"], "user_id": data["user_id"]}
