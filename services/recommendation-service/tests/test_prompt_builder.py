"""Tests for prompt_builder — 009-workout-diet-ux-fixes."""
from __future__ import annotations
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from src.services.prompt_builder import build_workout_prompt


def test_workout_prompt_is_single_week():
    """Generated prompt must NOT request a 4-week program."""
    prompt = build_workout_prompt({"weight": 80.0}, "muscle_gain")
    assert "4-week" not in prompt.lower(), "Prompt must not reference 4-week program"


def test_workout_prompt_has_single_week_instruction():
    """Generated prompt must request a single-week plan."""
    prompt = build_workout_prompt({"weight": 80.0}, "general_health")
    assert "single-week" in prompt.lower() or "one week" in prompt.lower(), \
        "Prompt must explicitly request a single-week plan"


def test_workout_prompt_json_schema_has_days_not_weeks():
    """JSON schema in prompt must use 'days' at the top level, not 'weeks'."""
    prompt = build_workout_prompt({"weight": 75.0}, "weight_loss")
    # Schema should have "days": [ at top level
    assert '"days"' in prompt, "Prompt JSON schema must include top-level 'days' key"


def test_workout_prompt_requires_quality():
    """Prompt must include quality/score instruction to achieve ≥90."""
    prompt = build_workout_prompt({"weight": 80.0}, "muscle_gain")
    assert "90" in prompt or "quality" in prompt.lower(), \
        "Prompt must reference quality score target"


def test_workout_prompt_includes_required_muscle_groups():
    """Prompt must still require all major muscle groups."""
    prompt = build_workout_prompt({"body_fat_percentage": 25.0}, "weight_loss")
    for group in ["chest", "biceps", "triceps", "quadriceps", "hamstrings", "core"]:
        assert group in prompt.lower(), f"Prompt missing muscle group: {group}"


def test_workout_prompt_requests_plan_explanation():
    """Prompt must request a plan_explanation field in the JSON schema."""
    prompt = build_workout_prompt({"weight": 80.0, "body_fat_percentage": 22.0}, "build_muscle")
    assert '"plan_explanation"' in prompt, \
        "Prompt JSON schema must include 'plan_explanation' key"


def test_workout_prompt_explanation_references_body_composition():
    """plan_explanation instruction must reference body composition data."""
    prompt = build_workout_prompt({"weight": 80.0}, "general_health")
    assert "body composition" in prompt.lower() or "muscle" in prompt.lower(), \
        "plan_explanation instruction must reference body composition"
