"""
Tests for plan generation using the algorithmic engine (013-algorithmic-plan-engine).

The LLM-based generation has been replaced with deterministic engines.
These tests verify that generate_diet_recommendation and generate_workout_recommendation
produce valid structured plans without any external API calls.
"""
from __future__ import annotations
import json
import pytest
from unittest.mock import AsyncMock, MagicMock


def _make_session():
    """Return a mock AsyncSession that no-ops add/commit/refresh."""
    session = AsyncMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock(side_effect=lambda obj: obj)
    return session


# ── Diet generation ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_diet_uses_first_plan_when_retry_is_rate_limited():
    """Algorithmic diet generation always succeeds — returns a plan with 'days'."""
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
    from src.services.recommendation_service import generate_diet_recommendation

    session = _make_session()
    rec = await generate_diet_recommendation(
        session=session,
        user_id="user-1",
        scan_id="scan-1",
        metrics={"weight": 80.0, "body_fat_percentage": 20.0},
        goal_type="muscle_gain",
        restrictions=[],
        age=28,
        height_cm=178.0,
        gender="male",
        activity_level="moderate",
    )

    assert rec is not None
    plan = json.loads(rec.structured_plan)
    assert "days" in plan
    assert len(plan["days"]) == 7


@pytest.mark.asyncio
async def test_diet_propagates_503_when_first_attempt_fails():
    """With algorithmic engine, generation never raises 503 — plan always returned."""
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
    from src.services.recommendation_service import generate_diet_recommendation

    session = _make_session()
    rec = await generate_diet_recommendation(
        session=session,
        user_id="user-1",
        scan_id="scan-1",
        metrics={"weight": 80.0},
        goal_type="muscle_gain",
        restrictions=[],
    )

    assert rec is not None
    plan = json.loads(rec.structured_plan)
    assert "days" in plan


# ── Workout generation ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_workout_uses_first_plan_when_retry_is_rate_limited():
    """Algorithmic workout generation always succeeds — returns a plan with 'days'."""
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
    from src.services.recommendation_service import generate_workout_recommendation

    session = _make_session()
    rec = await generate_workout_recommendation(
        session=session,
        user_id="user-1",
        scan_id="scan-1",
        metrics={"weight": 80.0, "body_fat_percentage": 20.0},
        goal_type="muscle_gain",
    )

    assert rec is not None
    plan = json.loads(rec.structured_plan)
    assert "days" in plan
    assert len(plan["days"]) == 7


@pytest.mark.asyncio
async def test_workout_propagates_503_when_first_attempt_fails():
    """With algorithmic engine, generation never raises 503 — plan always returned."""
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
    from src.services.recommendation_service import generate_workout_recommendation

    session = _make_session()
    rec = await generate_workout_recommendation(
        session=session,
        user_id="user-1",
        scan_id="scan-1",
        metrics={"weight": 80.0},
        goal_type="muscle_gain",
    )

    assert rec is not None
    plan = json.loads(rec.structured_plan)
    assert "days" in plan
