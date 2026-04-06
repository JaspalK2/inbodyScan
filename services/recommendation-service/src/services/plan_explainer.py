"""
Template-based plan explanation generator.

Produces 2-4 sentence explanations referencing actual body composition
metrics and goal type. No LLM required.
"""
from __future__ import annotations


_GOAL_LABELS = {
    "muscle_gain":       "muscle gain",
    "build_muscle":      "muscle gain",
    "lose_fat":          "fat loss",
    "weight_loss":       "fat loss",
    "general_health":    "general health",
    "maintain":          "maintenance",
    "improve_endurance": "endurance improvement",
}

# Body fat thresholds (%)
_BF_LEAN    = 15.0
_BF_NORMAL  = 25.0
_BF_HIGH    = 35.0


def _bf_observation(bf_pct: float | None, goal: str) -> str:
    if bf_pct is None:
        return "Body composition data was not provided, so a balanced program was selected."
    if bf_pct < _BF_LEAN:
        return f"With a lean body fat of {bf_pct:.1f}%, your muscle-to-fat ratio is excellent — volume and intensity are the primary levers."
    if bf_pct < _BF_NORMAL:
        return f"At {bf_pct:.1f}% body fat you are in a healthy range, allowing for a well-balanced program."
    if bf_pct < _BF_HIGH:
        return f"Your body fat of {bf_pct:.1f}% is above the optimal range, so cardio volume has been elevated and compound lifts prioritised to maximise caloric expenditure."
    return f"With body fat at {bf_pct:.1f}%, reducing fat mass is the primary focus — cardio sessions and full-body compound work dominate the weekly structure."


def _lean_mass_note(lean_kg: float | None) -> str:
    if lean_kg is None:
        return ""
    if lean_kg >= 65:
        return f" Your lean mass of {lean_kg:.1f} kg indicates a strong muscular base to build upon."
    if lean_kg >= 45:
        return f" Your lean mass of {lean_kg:.1f} kg provides a solid foundation; progressive overload will drive continued growth."
    return f" With {lean_kg:.1f} kg of lean mass, building a strong foundation of compound strength is the priority."


def _goal_emphasis(goal: str, bf_pct: float | None) -> str:
    label = _GOAL_LABELS.get(goal, goal.replace("_", " "))
    if goal in ("lose_fat", "weight_loss"):
        if bf_pct is not None and bf_pct >= _BF_NORMAL:
            return "Cardio sessions are placed strategically to maximise fat oxidation while preserving lean muscle through resistance work."
        return "A caloric deficit combined with resistance training protects muscle while targeting fat loss."
    if goal in ("muscle_gain", "build_muscle"):
        return "Progressive overload across compound and isolation movements will stimulate hypertrophy; rest days are positioned to allow full recovery."
    if goal == "improve_endurance":
        return "Higher rep ranges, shorter rest periods, and dedicated cardio sessions build aerobic capacity alongside muscular endurance."
    return f"The program is balanced for {label} — combining strength, conditioning, and recovery in equal measure."


def build_workout_explanation(metrics: dict, goal_type: str) -> str:
    """Generate a 2–4 sentence workout plan explanation from body composition metrics."""
    bf_pct: float | None = (
        metrics.get("body_fat_percentage")
        or metrics.get("pbf")
        or metrics.get("body_fat_pct")
    )
    lean_kg: float | None = (
        metrics.get("fat_free_mass")
        or metrics.get("fat_free_mass_kg")
        or metrics.get("lean_mass_kg")
    )
    # Derive lean mass from weight + BF if not directly provided
    if lean_kg is None and bf_pct is not None:
        weight = metrics.get("weight") or metrics.get("body_weight_kg")
        if weight:
            lean_kg = weight * (1.0 - bf_pct / 100.0)

    obs = _bf_observation(bf_pct, goal_type)
    lean_note = _lean_mass_note(lean_kg)
    emphasis = _goal_emphasis(goal_type, bf_pct)

    return f"{obs}{lean_note} {emphasis}"


def build_diet_explanation(macro_targets, goal_type: str) -> str:
    """Generate a 1–2 sentence diet plan summary from macro targets."""
    label = _GOAL_LABELS.get(goal_type, goal_type.replace("_", " "))
    cals = getattr(macro_targets, "calories", None)
    protein = getattr(macro_targets, "protein_g", None)
    ratio = getattr(macro_targets, "protein_ratio", None)

    if cals and protein:
        return (
            f"This 7-day plan is calibrated for {label} at {cals} kcal/day "
            f"with {protein:.0f}g protein ({ratio or 'high protein'}) to support your goal. "
            f"Each day's meals are portioned to hit your targets within ±5%."
        )
    return f"This 7-day meal plan is designed to support your {label} goal with balanced macros across all meals."
