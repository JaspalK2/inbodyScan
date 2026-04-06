"""Tests for workout score floor logic in recommendation_service — 009-workout-diet-ux-fixes."""
from __future__ import annotations
import sys
import os
import json
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from src.services.recommendation_service import _score_generated_plan


# ── _score_generated_plan helper ──────────────────────────────────────────────

def _make_plan(exercises_per_day: list[list[str]], rest_days: list[int] | None = None) -> dict:
    """Build a minimal single-week plan dict for scoring tests."""
    days = []
    for i, exs in enumerate(exercises_per_day):
        is_rest = rest_days is not None and i in rest_days
        days.append({
            "day": i + 1,
            "focus": "Test",
            "is_rest": is_rest,
            "exercises": [{"name": e, "sets": 4} for e in exs] if not is_rest else [],
        })
    return {"days": days}


def test_score_generated_plan_returns_int():
    plan = _make_plan([["bench press", "row", "squat", "overhead press", "deadlift", "curl", "tricep pushdown", "plank", "cardio"]])
    score = _score_generated_plan(plan)
    assert isinstance(score, int)
    assert 0 <= score <= 100


def test_score_generated_plan_empty_plan():
    score = _score_generated_plan({"days": []})
    # No exercises → coverage=0, volume=0, balance=0, cardio=0; freq gets residual points
    assert score < 20, f"Empty plan should score very low, got {score}"


def test_score_generated_plan_high_quality_plan():
    """A well-balanced plan covering all groups with high volume should score ≥ 90."""
    # Each exercise repeated to hit weekly set targets (≥ target for full volume points)
    chest_exs   = ["bench press"] * 4 + ["incline press"] * 4 + ["dumbbell fly"] * 4
    back_exs    = ["pull-up"] * 4 + ["seated cable row"] * 4 + ["deadlift"] * 4
    shoulder_exs = ["overhead press"] * 4 + ["lateral raise"] * 3 + ["face pull"] * 3
    arm_exs     = ["curl"] * 4 + ["hammer curl"] * 4 + ["tricep pushdown"] * 4 + ["skull crusher"] * 4
    leg_exs     = ["squat"] * 4 + ["leg press"] * 4 + ["leg curl"] * 4 + ["calf raise"] * 4 + ["hip thrust"] * 4
    core_exs    = ["plank"] * 3 + ["crunch"] * 4 + ["russian twist"] * 3
    cardio_exs  = ["treadmill"] * 2 + ["hiit"] * 2
    # 5 training days + 2 rest days
    plan = _make_plan(
        [
            chest_exs + back_exs,
            shoulder_exs + arm_exs,
            leg_exs + core_exs,
            chest_exs + shoulder_exs,
            back_exs + arm_exs + cardio_exs,
            [],  # rest
            [],  # rest
        ],
        rest_days=[5, 6],
    )
    score = _score_generated_plan(plan)
    assert score >= 90, f"High-quality plan scored only {score} — expected ≥ 90"


def test_score_generated_plan_legacy_weeks_format():
    """Legacy {weeks:[{days:[...]}]} format — no top-level 'days' key, scores low."""
    legacy_plan = {"weeks": [{"week": 1, "days": [{"day": 1, "exercises": [{"name": "squat", "sets": 3}]}]}]}
    score = _score_generated_plan(legacy_plan)
    # No "days" key at top level → treated as empty → score very low
    assert isinstance(score, int)
    assert score < 30, f"Legacy format with no top-level 'days' should score low, got {score}"
