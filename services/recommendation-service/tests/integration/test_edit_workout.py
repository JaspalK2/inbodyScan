"""Integration tests for PATCH /api/recommendations/workout/{rec_id}."""
from __future__ import annotations
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from tests.conftest import requires_db


EDITED_PLAN = {
    "summary": "Edited plan",
    "weeks": [
        {
            "week": 1,
            "days": [
                {
                    "day": 1,
                    "focus": "Chest",
                    "exercises": [
                        {"name": "Bench Press", "sets": 5, "reps": "5", "rest_seconds": 120, "notes": "Heavy"},
                    ],
                    "estimated_duration_minutes": 45,
                }
            ],
        }
    ],
    "progression_notes": "Increase weight weekly",
}


@requires_db
@pytest.mark.asyncio
async def test_edit_workout_plan_persists(auth_headers, created_workout_rec):
    """PATCH /workout/{id} saves edited_plan and returns it in subsequent GET."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))
    from src.main import app

    rec_id = created_workout_rec["id"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        patch_resp = await client.patch(
            f"/api/recommendations/workout/{rec_id}",
            json={"edited_plan": EDITED_PLAN},
            headers=auth_headers,
        )
        assert patch_resp.status_code == 200
        data = patch_resp.json()
        assert data["edited_plan"] is not None
        assert data["edited_plan"]["summary"] == "Edited plan"

        # Verify persistence via list endpoint
        list_resp = await client.get("/api/recommendations/workout", headers=auth_headers)
        assert list_resp.status_code == 200
        recs = list_resp.json()
        matching = next((r for r in recs if r["id"] == rec_id), None)
        assert matching is not None
        assert matching["edited_plan"]["summary"] == "Edited plan"


@requires_db
@pytest.mark.asyncio
async def test_edit_workout_plan_wrong_user(auth_headers, other_user_headers, created_workout_rec):
    """PATCH /workout/{id} returns 404 when accessed by a different user."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))
    from src.main import app

    rec_id = created_workout_rec["id"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.patch(
            f"/api/recommendations/workout/{rec_id}",
            json={"edited_plan": EDITED_PLAN},
            headers=other_user_headers,
        )
    assert resp.status_code == 404
