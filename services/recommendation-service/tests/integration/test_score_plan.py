"""Integration tests for POST /api/recommendations/workout/score-plan."""
from __future__ import annotations
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch


MINIMAL_PLAN = {
    "summary": "Test plan",
    "weeks": [
        {
            "week": 1,
            "days": [
                {
                    "day": 1,
                    "focus": "Upper Body",
                    "exercises": [
                        {"name": "Bench Press", "sets": 4, "reps": "8-10", "rest_seconds": 90, "notes": ""},
                        {"name": "Pull-up", "sets": 3, "reps": "6-8", "rest_seconds": 90, "notes": ""},
                    ],
                    "estimated_duration_minutes": 60,
                },
                {
                    "day": 2,
                    "focus": "Lower Body",
                    "exercises": [
                        {"name": "Squat", "sets": 4, "reps": "6-8", "rest_seconds": 120, "notes": ""},
                        {"name": "Romanian Deadlift", "sets": 3, "reps": "10-12", "rest_seconds": 90, "notes": ""},
                    ],
                    "estimated_duration_minutes": 60,
                },
            ],
        }
    ],
    "progression_notes": "Add weight each week",
}

SCORE_FIELDS = {
    "overall", "coverage_score", "volume_score", "balance_score",
    "cardio_score", "frequency_score", "covered_groups", "missing_groups",
    "weekly_sets_per_group", "feedback", "label",
}


@pytest.mark.asyncio
async def test_score_plan_returns_valid_score(auth_headers):
    """POST /workout/score-plan returns a WorkoutScoreOut with all required fields."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))
    from src.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/recommendations/workout/score-plan",
            json={"plan": MINIMAL_PLAN},
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    for field in SCORE_FIELDS:
        assert field in data, f"Missing field: {field}"
    assert 0 <= data["overall"] <= 100


@pytest.mark.asyncio
async def test_score_plan_requires_auth():
    """POST /workout/score-plan returns 401 without auth."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))
    from src.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/recommendations/workout/score-plan",
            json={"plan": MINIMAL_PLAN},
        )

    assert response.status_code in (401, 403)


@pytest.mark.asyncio
async def test_score_plan_empty_weeks(auth_headers):
    """POST /workout/score-plan with empty weeks returns a score (all zeros / missing groups)."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))
    from src.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/recommendations/workout/score-plan",
            json={"plan": {"weeks": []}},
            headers=auth_headers,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["overall"] >= 0
