"""Tests for diet macro validation and retry logic — 010-profile-diet-fixes."""
from __future__ import annotations
import sys
import os
from dataclasses import dataclass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from src.services.recommendation_service import _validate_diet_macros


@dataclass
class MockMacroTargets:
    calories: int = 2000
    protein_g: int = 150
    carbs_g: int = 200
    fat_g: int = 65
    fiber_g: int = 30


def _make_day(calories: float, protein_g: float, carbs_g: float, fat_g: float) -> dict:
    return {
        "day": 1,
        "meals": [],
        "day_totals": {
            "calories": calories,
            "protein_g": protein_g,
            "carbs_g": carbs_g,
            "fat_g": fat_g,
            "fiber_g": 25.0,
        },
    }


def test_validate_diet_macros_pass():
    """All days within ±10% of targets → returns True."""
    targets = MockMacroTargets()
    plan = {
        "days": [
            _make_day(2000, 150, 200, 65),   # exact
            _make_day(2100, 155, 205, 68),   # +5%
            _make_day(1900, 145, 195, 62),   # -5%
        ]
    }
    assert _validate_diet_macros(plan, targets) is True


def test_validate_diet_macros_fail_calories():
    """Day with calories 50% below target → returns False."""
    targets = MockMacroTargets()
    plan = {"days": [_make_day(1000, 150, 200, 65)]}  # 50% under
    assert _validate_diet_macros(plan, targets) is False


def test_validate_diet_macros_fail_protein():
    """Day with protein 20% over target → returns False."""
    targets = MockMacroTargets()
    plan = {"days": [_make_day(2000, 185, 200, 65)]}  # protein +23%
    assert _validate_diet_macros(plan, targets) is False


def test_validate_diet_macros_fail_carbs():
    """Day with carbs 15% under target → returns False."""
    targets = MockMacroTargets()
    plan = {"days": [_make_day(2000, 150, 165, 65)]}  # carbs -17.5%
    assert _validate_diet_macros(plan, targets) is False


def test_validate_diet_macros_fail_fat():
    """Day with fat 20% over target → returns False."""
    targets = MockMacroTargets()
    plan = {"days": [_make_day(2000, 150, 200, 82)]}  # fat +26%
    assert _validate_diet_macros(plan, targets) is False


def test_validate_diet_macros_empty_days():
    """Empty days list → returns True (vacuously valid, no days to fail)."""
    targets = MockMacroTargets()
    plan = {"days": []}
    assert _validate_diet_macros(plan, targets) is True


def test_validate_diet_macros_zero_target():
    """Zero calorie target → skips that macro, no division by zero."""
    targets = MockMacroTargets(calories=0)
    plan = {"days": [_make_day(0, 150, 200, 65)]}
    assert _validate_diet_macros(plan, targets) is True


def test_validate_diet_macros_missing_day_totals():
    """Day missing day_totals key → treated as 0 → fails target check."""
    targets = MockMacroTargets()
    plan = {"days": [{"day": 1, "meals": []}]}  # no day_totals
    assert _validate_diet_macros(plan, targets) is False


def test_validate_diet_macros_boundary_exactly_10_percent():
    """Exactly 10% deviation → should pass (≤ 10% tolerance)."""
    targets = MockMacroTargets(calories=2000)
    plan = {"days": [_make_day(1800, 150, 200, 65)]}  # exactly -10%
    assert _validate_diet_macros(plan, targets) is True


def test_validate_diet_macros_just_over_10_percent():
    """10.1% deviation → should fail."""
    targets = MockMacroTargets(calories=2000)
    plan = {"days": [_make_day(1797, 150, 200, 65)]}  # -10.15%
    assert _validate_diet_macros(plan, targets) is False
