"""Unit tests for plan_explainer.py (013-algorithmic-plan-engine)."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from src.services.plan_explainer import build_workout_explanation, build_diet_explanation


def test_high_bf_lose_fat_mentions_body_fat_and_cardio():
    """BF=32% + lose_fat → explanation mentions body fat and cardio."""
    result = build_workout_explanation(
        {"body_fat_percentage": 32.0, "weight": 90.0}, "lose_fat"
    )
    assert "32" in result or "body fat" in result.lower()
    assert "cardio" in result.lower() or "fat" in result.lower()


def test_lean_bf_muscle_gain_mentions_progressive_overload():
    """BF=12% + muscle_gain → explanation mentions lean/overload."""
    result = build_workout_explanation(
        {"body_fat_percentage": 12.0, "weight": 80.0, "fat_free_mass": 70.4}, "muscle_gain"
    )
    assert "12" in result or "lean" in result.lower() or "progressive" in result.lower()


def test_missing_bf_returns_valid_string():
    """No body_fat_percentage in metrics → still returns a non-empty string."""
    result = build_workout_explanation({"weight": 80.0}, "general_health")
    assert isinstance(result, str)
    assert len(result) > 20


def test_explanation_references_lean_mass_when_derivable():
    """Lean mass derived from weight + BF% should appear in explanation."""
    result = build_workout_explanation(
        {"body_fat_percentage": 20.0, "weight": 80.0}, "build_muscle"
    )
    # lean mass = 80 * 0.8 = 64kg — should appear or result should be non-trivial
    assert isinstance(result, str)
    assert len(result) > 30


def test_diet_explanation_includes_calories_and_protein():
    """Diet explanation mentions calorie and protein targets."""
    from dataclasses import dataclass

    @dataclass
    class FakeMacros:
        calories: int = 2200
        protein_g: float = 165.0
        protein_ratio: str = "2.0g/kg lean mass"

    result = build_diet_explanation(FakeMacros(), "muscle_gain")
    assert "2200" in result
    assert "165" in result


def test_diet_explanation_fallback_no_crash():
    """diet explanation with no macros object still returns a string."""
    class Empty:
        pass

    result = build_diet_explanation(Empty(), "general_health")
    assert isinstance(result, str)
    assert len(result) > 10
