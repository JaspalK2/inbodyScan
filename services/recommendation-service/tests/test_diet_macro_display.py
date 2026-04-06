"""
Unit tests for diet plan day total computation logic (US1).

These tests validate the Python-side understanding of the expected meal summation
logic that must also be applied on the frontend display layer.
The rule: day totals = sum of individual meal values; AI-returned day_totals ignored.
"""
from __future__ import annotations


def compute_day_totals(meals: list[dict]) -> dict:
    """Reference implementation of the correct day-total computation."""
    result = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "fiber_g": 0.0}
    for meal in meals:
        result["calories"] += meal.get("calories", 0) or 0
        result["protein_g"] += meal.get("protein_g", 0) or 0
        result["carbs_g"] += meal.get("carbs_g", 0) or 0
        result["fat_g"] += meal.get("fat_g", 0) or 0
        result["fiber_g"] += meal.get("fiber_g", 0) or 0
    return result


def test_day_totals_sum_calories_correctly():
    meals = [
        {"meal": "breakfast", "calories": 650, "protein_g": 40, "carbs_g": 70, "fat_g": 15},
        {"meal": "lunch",     "calories": 700, "protein_g": 45, "carbs_g": 80, "fat_g": 18},
        {"meal": "dinner",    "calories": 600, "protein_g": 38, "carbs_g": 65, "fat_g": 16},
    ]
    totals = compute_day_totals(meals)
    assert totals["calories"] == 1950
    assert totals["protein_g"] == 123
    assert totals["carbs_g"] == 215
    assert totals["fat_g"] == 49


def test_ai_day_totals_are_different_from_sum():
    """Demonstrates the original bug: AI-returned totals don't match meal sums."""
    meals = [
        {"meal": "breakfast", "calories": 650},
        {"meal": "lunch",     "calories": 700},
        {"meal": "dinner",    "calories": 600},
    ]
    ai_day_total = 2950  # AI-hallucinated value
    actual_sum = compute_day_totals(meals)["calories"]
    # The AI total is wrong — our computed sum is correct
    assert actual_sum == 1950
    assert ai_day_total != actual_sum, "AI total should differ from real sum in this test case"


def test_empty_meals_returns_zeros():
    totals = compute_day_totals([])
    assert totals == {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "fiber_g": 0.0}


def test_missing_macro_fields_default_to_zero():
    meals = [{"meal": "breakfast", "calories": 500}]  # protein_g etc. missing
    totals = compute_day_totals(meals)
    assert totals["calories"] == 500
    assert totals["protein_g"] == 0.0


def test_none_macro_fields_default_to_zero():
    meals = [{"meal": "breakfast", "calories": None, "protein_g": None}]
    totals = compute_day_totals(meals)
    assert totals["calories"] == 0.0
    assert totals["protein_g"] == 0.0


def test_four_meal_day_totals():
    meals = [
        {"meal": "breakfast", "calories": 500, "protein_g": 35, "carbs_g": 60, "fat_g": 10},
        {"meal": "lunch",     "calories": 700, "protein_g": 50, "carbs_g": 80, "fat_g": 20},
        {"meal": "dinner",    "calories": 600, "protein_g": 45, "carbs_g": 70, "fat_g": 15},
        {"meal": "snack",     "calories": 200, "protein_g": 15, "carbs_g": 25, "fat_g": 5},
    ]
    totals = compute_day_totals(meals)
    assert totals["calories"] == 2000
    assert totals["protein_g"] == 145
    assert totals["carbs_g"] == 235
    assert totals["fat_g"] == 50
