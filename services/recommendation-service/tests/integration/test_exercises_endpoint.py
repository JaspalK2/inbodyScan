"""Integration tests for GET /api/recommendations/exercises/search."""
from __future__ import annotations
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_exercise_search_returns_results(auth_headers):
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))
    from src.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/recommendations/exercises/search?q=squat",
            headers=auth_headers,
        )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "name" in first
    assert "primary_muscles" in first
    assert "secondary_muscles" in first
    assert "category" in first
    assert "equipment" in first
    assert "level" in first


@pytest.mark.asyncio
async def test_exercise_search_400_on_short_query(auth_headers):
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))
    from src.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/recommendations/exercises/search?q=a",
            headers=auth_headers,
        )
    assert resp.status_code == 422  # FastAPI Query min_length validation


@pytest.mark.asyncio
async def test_exercise_search_401_without_auth():
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))
    from src.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/recommendations/exercises/search?q=bench")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_exercise_search_empty_results(auth_headers):
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))
    from src.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/recommendations/exercises/search?q=zzzzxxx",
            headers=auth_headers,
        )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_exercise_search_limit(auth_headers):
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))
    from src.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/recommendations/exercises/search?q=press&limit=3",
            headers=auth_headers,
        )
    assert resp.status_code == 200
    assert len(resp.json()) <= 3
