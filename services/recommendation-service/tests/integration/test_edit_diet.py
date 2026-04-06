"""Integration tests for PATCH /api/recommendations/diet/{rec_id}."""
from __future__ import annotations
import pytest
from httpx import AsyncClient, ASGITransport
from tests.conftest import requires_db


EDITED_PLAN = {
    "summary": "Edited diet",
    "days": [
        {
            "day": 1,
            "meals": [
                {"meal": "breakfast", "foods": ["200g oats", "3 eggs"], "calories": 550, "protein_g": 35, "carbs_g": 60, "fat_g": 12},
                {"meal": "lunch",     "foods": ["200g chicken breast", "100g rice"], "calories": 480, "protein_g": 42, "carbs_g": 55, "fat_g": 8},
                {"meal": "dinner",    "foods": ["150g salmon", "150g broccoli"], "calories": 420, "protein_g": 38, "carbs_g": 15, "fat_g": 18},
                {"meal": "snack",     "foods": ["Greek yogurt 150g"], "calories": 130, "protein_g": 15, "carbs_g": 10, "fat_g": 3},
            ],
            "day_totals": {"calories": 1580, "protein_g": 130, "carbs_g": 140, "fat_g": 41, "fiber_g": 20},
        }
    ],
    "micronutrient_highlights": ["High omega-3 from salmon"],
    "meal_prep_tips": ["Prep chicken and rice in bulk"],
}


@requires_db
@pytest.mark.asyncio
async def test_edit_diet_plan_persists(auth_headers, created_diet_rec):
    """PATCH /diet/{id} saves edited_plan and returns updated data."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))
    from src.main import app

    rec_id = created_diet_rec["id"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        patch_resp = await client.patch(
            f"/api/recommendations/diet/{rec_id}",
            json={"edited_plan": EDITED_PLAN},
            headers=auth_headers,
        )
        assert patch_resp.status_code == 200
        data = patch_resp.json()
        assert data["edited_plan"] is not None
        assert data["edited_plan"]["summary"] == "Edited diet"

        # Verify via list
        list_resp = await client.get("/api/recommendations/diet", headers=auth_headers)
        recs = list_resp.json()
        matching = next((r for r in recs if r["id"] == rec_id), None)
        assert matching is not None
        assert matching["edited_plan"]["summary"] == "Edited diet"


@requires_db
@pytest.mark.asyncio
async def test_edit_diet_plan_wrong_user(auth_headers, other_user_headers, created_diet_rec):
    """PATCH /diet/{id} returns 404 when accessed by a different user."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))
    from src.main import app

    rec_id = created_diet_rec["id"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.patch(
            f"/api/recommendations/diet/{rec_id}",
            json={"edited_plan": EDITED_PLAN},
            headers=other_user_headers,
        )
    assert resp.status_code == 404
