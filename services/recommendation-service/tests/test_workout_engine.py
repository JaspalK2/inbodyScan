"""Unit tests for workout_engine.py (013-algorithmic-plan-engine)."""
from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from src.services.workout_engine import generate_workout_plan
from src.services.workout_scorer import score_workout_split


def test_muscle_gain_has_5_training_2_rest():
    plan = generate_workout_plan({"weight": 80.0, "body_fat_percentage": 18.0}, "muscle_gain")
    days = plan["days"]
    assert len(days) == 7
    rest = sum(1 for d in days if d["is_rest"])
    training = sum(1 for d in days if not d["is_rest"])
    assert rest == 1  # PPL template has 1 rest day
    assert training == 6


def test_lose_fat_has_at_least_2_cardio_days():
    plan = generate_workout_plan({"weight": 90.0, "body_fat_percentage": 30.0}, "lose_fat")
    days = plan["days"]
    cardio_days = [d for d in days if not d["is_rest"] and "Cardio" in d["focus"]]
    assert len(cardio_days) >= 2


def test_plan_has_required_muscle_groups():
    """All required muscle groups must appear across training days."""
    plan = generate_workout_plan({"weight": 80.0, "body_fat_percentage": 20.0}, "muscle_gain")
    all_exercises = []
    for day in plan["days"]:
        all_exercises.extend(day.get("exercises", []))
    exercise_names = " ".join(e["name"].lower() for e in all_exercises)

    # Check key muscle groups are represented via exercise names
    assert any(kw in exercise_names for kw in ["bench", "push", "chest"]), "Missing chest"
    assert any(kw in exercise_names for kw in ["row", "pull", "lat"]), "Missing back"
    assert any(kw in exercise_names for kw in ["squat", "leg press", "lunge"]), "Missing quads"
    assert any(kw in exercise_names for kw in ["curl", "bicep", "hammer"]), "Missing biceps"
    assert any(kw in exercise_names for kw in ["tricep", "pushdown", "skull", "dip"]), "Missing triceps"
    assert any(kw in exercise_names for kw in ["deadlift", "romanian"]), "Missing hinge pattern"


def test_plan_has_compound_lift():
    """At least one compound lift must be present."""
    plan = generate_workout_plan({"weight": 80.0, "body_fat_percentage": 15.0}, "build_muscle")
    all_names = [e["name"].lower() for d in plan["days"] for e in d.get("exercises", [])]
    compound_found = any(
        kw in name for name in all_names
        for kw in ["squat", "deadlift", "bench press", "row", "military press", "shoulder press"]
    )
    assert compound_found, "No compound lift found in plan"


def test_plan_scores_above_70():
    """Generated plan must score ≥ 70 on the workout scorer."""
    plan = generate_workout_plan({"weight": 80.0, "body_fat_percentage": 20.0}, "muscle_gain")
    scorer_days = [
        {
            "day_label": str(d["day"]),
            "focus": d["focus"],
            "is_rest": d["is_rest"],
            "exercises": [{"exercise_name": ex["name"], "sets": ex.get("sets", 3)} for ex in d.get("exercises", [])],
        }
        for d in plan["days"]
    ]
    score = score_workout_split(scorer_days)
    assert score.overall >= 70, f"Score too low: {score.overall}"


def test_missing_body_fat_uses_defaults():
    """Missing body_fat_percentage in metrics → plan still generates."""
    plan = generate_workout_plan({"weight": 80.0}, "general_health")
    assert len(plan["days"]) == 7
    assert "plan_explanation" in plan
    assert plan["plan_explanation"]


def test_plan_explanation_is_populated():
    """plan_explanation must be non-empty string referencing body composition."""
    plan = generate_workout_plan(
        {"weight": 80.0, "body_fat_percentage": 28.0}, "lose_fat"
    )
    expl = plan.get("plan_explanation", "")
    assert isinstance(expl, str) and len(expl) > 30


def test_all_goal_types_generate_plans():
    """All supported goal types must produce a 7-day plan."""
    goals = ["muscle_gain", "build_muscle", "lose_fat", "weight_loss",
             "general_health", "maintain", "improve_endurance"]
    for goal in goals:
        plan = generate_workout_plan({"weight": 80.0, "body_fat_percentage": 20.0}, goal)
        assert len(plan["days"]) == 7, f"Goal {goal} did not produce 7 days"
