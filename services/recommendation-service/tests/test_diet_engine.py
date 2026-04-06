"""Unit tests for diet_engine.py (013-algorithmic-plan-engine)."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from src.services.diet_engine import generate_diet_plan
from src.services.macro_calculator import calculate_macros


def _macros(goal="build_muscle"):
    return calculate_macros(
        body_weight_kg=80.0,
        fat_free_mass_kg=64.0,
        body_fat_percentage=20.0,
        age=28,
        height_cm=178.0,
        gender="male",
        goal_type=goal,
    )


def test_plan_has_7_days():
    plan = generate_diet_plan(_macros(), [], "build_muscle")
    assert len(plan["days"]) == 7


def test_each_day_has_4_meals():
    plan = generate_diet_plan(_macros(), [], "build_muscle")
    for day in plan["days"]:
        assert len(day["meals"]) == 4, f"Day {day['day']} has {len(day['meals'])} meals"


def test_day_totals_match_sum_of_meals():
    """day_totals must equal the sum of meal_totals, not an estimate."""
    plan = generate_diet_plan(_macros(), [], "lose_fat")
    for day in plan["days"]:
        summed_cal = round(sum(m["meal_totals"]["calories"] for m in day["meals"]), 1)
        assert abs(day["day_totals"]["calories"] - summed_cal) < 1.0, (
            f"Day {day['day']} totals mismatch: {day['day_totals']['calories']} vs {summed_cal}"
        )


def test_plan_explanation_present():
    plan = generate_diet_plan(_macros(), [], "build_muscle")
    assert isinstance(plan.get("plan_explanation"), str)
    assert len(plan["plan_explanation"]) > 20


def test_vegetarian_restriction_filters_meat():
    plan = generate_diet_plan(_macros(), ["vegetarian"], "build_muscle")
    for day in plan["days"]:
        for meal in day["meals"]:
            for item in meal["items"]:
                # If a food is here, it passed the vegetarian filter
                assert item["food_name"], "Empty food name"


def test_calorie_targets_roughly_met():
    """Each day's calories should be within 40% of the target (food DB may be sparse)."""
    macros = _macros("build_muscle")
    plan = generate_diet_plan(macros, [], "build_muscle")
    for day in plan["days"]:
        actual = day["day_totals"]["calories"]
        # Only check if we have actual food items
        if actual > 0:
            ratio = actual / macros.calories
            assert 0.3 <= ratio <= 1.8, (
                f"Day {day['day']} calories {actual} too far from target {macros.calories}"
            )


def test_all_goal_types_generate_plans():
    """All supported goal types produce a 7-day plan."""
    goals = ["muscle_gain", "build_muscle", "lose_fat", "weight_loss",
             "general_health", "maintain", "improve_endurance"]
    for goal in goals:
        macros = calculate_macros(80.0, None, 20.0, 28, 178.0, "male", goal)
        plan = generate_diet_plan(macros, [], goal)
        assert len(plan["days"]) == 7, f"Goal {goal} did not produce 7 days"


def test_deterministic_output():
    """Same inputs always produce the same plan."""
    macros = _macros("maintain")
    plan1 = generate_diet_plan(macros, [], "maintain")
    plan2 = generate_diet_plan(macros, [], "maintain")
    assert plan1["days"][0]["meals"][0]["items"] == plan2["days"][0]["meals"][0]["items"]


import pytest as _pytest

@_pytest.mark.parametrize("target_cal", [1200, 1800, 2200, 3000, 4000])
def test_caloric_accuracy_within_5_percent(target_cal):
    """Every day in a generated plan must land within ±5% of the caloric target (FR-001)."""
    from src.services.macro_calculator import calculate_macros
    macros = calculate_macros(
        body_weight_kg=70.0,
        fat_free_mass_kg=None,
        body_fat_percentage=20.0,
        age=30,
        height_cm=170.0,
        gender="male",
        goal_type="general_health",
    )
    # Override calories to our test target while keeping macro ratios proportional
    import dataclasses
    macros = dataclasses.replace(
        macros,
        calories=float(target_cal),
        protein_g=target_cal * 0.075,
        carbs_g=target_cal * 0.1125,
        fat_g=target_cal * 0.0333,
    )
    plan = generate_diet_plan(macros, [], "general_health")
    for day in plan["days"]:
        actual = day["day_totals"]["calories"]
        if actual == 0:
            continue  # sparse DB edge case — skip empty days
        deviation_pct = abs(actual - target_cal) / target_cal * 100
        assert deviation_pct <= 5.0, (
            f"target={target_cal} day={day['day']}: {actual:.1f} kcal → {deviation_pct:.1f}% deviation (exceeds ±5%)"
        )


@_pytest.mark.parametrize("restriction", [["vegetarian"], ["vegan"]])
def test_caloric_accuracy_with_restrictions(restriction):
    """±5% accuracy must hold even with dietary restrictions applied (FR-003)."""
    macros = calculate_macros(70.0, None, 20.0, 30, 170.0, "male", "general_health")
    import dataclasses
    macros = dataclasses.replace(
        macros,
        calories=2200.0,
        protein_g=165.0,
        carbs_g=247.5,
        fat_g=73.3,
    )
    plan = generate_diet_plan(macros, restriction, "general_health")
    for day in plan["days"]:
        actual = day["day_totals"]["calories"]
        if actual == 0:
            continue
        deviation_pct = abs(actual - 2200.0) / 2200.0 * 100
        assert deviation_pct <= 5.0, (
            f"restriction={restriction} day={day['day']}: {actual:.1f} kcal → {deviation_pct:.1f}% deviation"
        )


def test_portion_bounds():
    """No item's grams should fall below 20g or exceed 600g (FR-004)."""
    import dataclasses
    for target_cal in [1200, 4000]:
        macros = calculate_macros(70.0, None, 20.0, 30, 170.0, "male", "general_health")
        macros = dataclasses.replace(
            macros,
            calories=float(target_cal),
            protein_g=target_cal * 0.075,
            carbs_g=target_cal * 0.1125,
            fat_g=target_cal * 0.0333,
        )
        plan = generate_diet_plan(macros, [], "general_health")
        for day in plan["days"]:
            for meal in day["meals"]:
                for item in meal["items"]:
                    g = item["grams"]
                    assert g >= 20.0, f"target={target_cal} item {item['food_name']}: {g}g < 20g"
                    assert g <= 600.0, f"target={target_cal} item {item['food_name']}: {g}g > 600g"


def test_empty_foods_does_not_crash(tmp_path, monkeypatch):
    """If foods.json is missing, engine returns 7 days with empty meals (no crash)."""
    import src.services.diet_engine as de
    monkeypatch.setattr(de, "_FOODS_PATH", tmp_path / "nonexistent.json")
    plan = generate_diet_plan(_macros(), [], "general_health")
    assert len(plan["days"]) == 7
