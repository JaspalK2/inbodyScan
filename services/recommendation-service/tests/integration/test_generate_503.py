"""Integration tests: generate endpoints return 503 when the LLM client raises a quota error."""
from __future__ import annotations
import pytest
from fastapi import HTTPException
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock


WORKOUT_BODY = {
    "scan_id": "test-scan-id",
    "metrics": {"weight": 80.0, "body_fat_percentage": 20.0},
    "goal_type": "muscle_gain",
}

DIET_BODY = {
    "scan_id": "test-scan-id",
    "metrics": {"weight": 80.0, "body_fat_percentage": 20.0},
    "goal_type": "muscle_gain",
    "dietary_restrictions": [],
    "age": 28,
    "height_cm": 178.0,
    "gender": "male",
    "activity_level": "moderate",
}

_503_detail = "Plan generation is temporarily unavailable — please try again shortly."


def _quota_client():
    """Return a mock LLMClient whose generate() always raises a 503 HTTPException."""
    mock = AsyncMock()
    mock.generate = AsyncMock(
        side_effect=HTTPException(status_code=503, detail=_503_detail)
    )
    return mock


@pytest.mark.asyncio
async def test_generate_workout_returns_503_on_quota_error(auth_headers):
    """POST /workout/generate returns 503 (not 500) when the LLM quota is exhausted."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))
    from src.main import app

    with patch("src.services.recommendation_service.get_llm_client", return_value=_quota_client()):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/recommendations/workout/generate",
                json=WORKOUT_BODY,
                headers=auth_headers,
            )

    assert response.status_code == 503
    detail = response.json().get("detail", "")
    assert "temporarily unavailable" in detail.lower() or "try again" in detail.lower()


@pytest.mark.asyncio
async def test_generate_diet_returns_503_on_quota_error(auth_headers):
    """POST /diet/generate returns 503 (not 500) when the LLM quota is exhausted."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))
    from src.main import app

    with patch("src.services.recommendation_service.get_llm_client", return_value=_quota_client()):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/recommendations/diet/generate",
                json=DIET_BODY,
                headers=auth_headers,
            )

    assert response.status_code == 503
