"""Tests for dietary restriction enforcement in diet_engine.py (018-diet-restrictions-plan-ux).

These tests verify that food items violating a user's declared dietary restrictions
never appear in generated plans. This is a safety-critical requirement.
"""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import dataclasses
import pytest

from src.services.diet_engine import generate_diet_plan
from src.services.macro_calculator import calculate_macros

# Canonical list of food name substrings that are NOT vegetarian / not vegan.
# Checked case-insensitively against each item's food_name.
_NON_VEGETARIAN_SUBSTRINGS = [
    "chicken", "beef", "pork", "lamb", "turkey", "duck", "veal", "venison",
    "salmon", "tuna", "tilapia", "fish", "shrimp", "lobster", "crab", "prawn",
    "anchov", "sardine", "clam", "oyster", "scallop", "squid", "octopus",
    "bacon", "ham", "sausage", "pepperoni", "salami",
]

# Dairy and eggs are acceptable for vegetarians but not for vegans
_NON_VEGAN_SUBSTRINGS = _NON_VEGETARIAN_SUBSTRINGS + [
    "milk", "cheese", "butter", "yogurt", "cream", "whey", "casein",
    "egg", "honey",
]


def _macros_at(calories: float = 2200.0):
    macros = calculate_macros(70.0, None, 20.0, 30, 170.0, "male", "general_health")
    return dataclasses.replace(
        macros,
        calories=calories,
        protein_g=calories * 0.075,
        carbs_g=calories * 0.1125,
        fat_g=calories * 0.0333,
    )


def _all_item_names(plan: dict) -> list[str]:
    names = []
    for day in plan["days"]:
        for meal in day["meals"]:
            for item in meal["items"]:
                names.append(item["food_name"])
    return names


def test_vegetarian_plan_contains_no_meat_or_fish():
    """Generated plan with vegetarian restriction must contain zero meat/fish items (FR-003)."""
    plan = generate_diet_plan(_macros_at(2200.0), ["vegetarian"], "general_health")
    item_names = _all_item_names(plan)
    violations = [
        name for name in item_names
        if any(s in name.lower() for s in _NON_VEGETARIAN_SUBSTRINGS)
    ]
    assert violations == [], (
        f"Vegetarian plan contains {len(violations)} non-vegetarian item(s): {violations}"
    )


@pytest.mark.parametrize("restriction", [["vegetarian"], ["vegan"]])
def test_restriction_plan_contains_no_meat_or_fish(restriction):
    """Both vegetarian and vegan restrictions must exclude all meat/fish items."""
    plan = generate_diet_plan(_macros_at(2200.0), restriction, "general_health")
    item_names = _all_item_names(plan)
    violations = [
        name for name in item_names
        if any(s in name.lower() for s in _NON_VEGETARIAN_SUBSTRINGS)
    ]
    assert violations == [], (
        f"restriction={restriction}: {len(violations)} non-vegetarian item(s) found: {violations}"
    )


def test_multiple_restrictions_satisfied():
    """Plan with multiple simultaneous restrictions must satisfy all of them."""
    plan = generate_diet_plan(_macros_at(2200.0), ["vegetarian", "gluten_free"], "general_health")
    assert len(plan["days"]) == 7, "Plan must still produce 7 days with multiple restrictions"
    item_names = _all_item_names(plan)
    violations = [
        name for name in item_names
        if any(s in name.lower() for s in _NON_VEGETARIAN_SUBSTRINGS)
    ]
    assert violations == [], (
        f"Multi-restriction plan contains non-vegetarian items: {violations}"
    )


def test_no_restrictions_generates_normally():
    """Empty restrictions list must produce a normal 7-day plan with food items present."""
    plan = generate_diet_plan(_macros_at(2200.0), [], "general_health")
    assert len(plan["days"]) == 7
    total_items = sum(
        len(meal["items"])
        for day in plan["days"]
        for meal in day["meals"]
    )
    assert total_items > 0, "Plan with no restrictions must contain food items"
