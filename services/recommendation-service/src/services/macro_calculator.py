"""
Macro calculator based on Mifflin-St Jeor BMR formula.
Uses InBody scan metrics + user profile to compute daily targets.
All formulas are from publicly available sports science literature.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class MacroTargets:
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    # breakdown for transparency
    bmr: int
    tdee: int
    goal_adjustment_kcal: int
    protein_ratio: str  # e.g. "2.2g/kg lean mass"
    notes: str


_ACTIVITY_MULTIPLIERS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}

_GOAL_CONFIG = {
    # (kcal_adjust, protein_per_kg, carb_pct_remaining, fat_pct_remaining, protein_ratio_label)
    "lose_fat":          (-500, 2.2, 0.30, 0.25, "2.2g/kg lean mass"),
    "build_muscle":      (300,  2.0, 0.45, 0.25, "2.0g/kg lean mass"),
    "maintain":          (0,    1.8, 0.40, 0.30, "1.8g/kg lean mass"),
    "improve_endurance": (-100, 1.6, 0.50, 0.25, "1.6g/kg lean mass"),
    "general_health":    (0,    1.6, 0.35, 0.35, "1.6g/kg lean mass"),
}


def calculate_macros(
    body_weight_kg: float | None,
    fat_free_mass_kg: float | None,
    body_fat_percentage: float | None,
    age: int | None,
    height_cm: float | None,
    gender: str | None,    # "male" | "female" | other
    goal_type: str,        # lose_fat | build_muscle | maintain | improve_endurance | general_health
    activity_level: str = "moderate",
) -> MacroTargets:
    # ── Fallback defaults ──────────────────────────────────────────────────────
    weight = body_weight_kg if body_weight_kg is not None else 70.0
    age_val = age if age is not None else 30
    height = height_cm if height_cm is not None else 170.0

    # Lean mass resolution
    if fat_free_mass_kg is not None:
        lean_mass = fat_free_mass_kg
    elif body_weight_kg is not None and body_fat_percentage is not None:
        lean_mass = body_weight_kg * (1.0 - body_fat_percentage / 100.0)
    else:
        lean_mass = weight * 0.75

    # ── BMR (Mifflin-St Jeor) ──────────────────────────────────────────────────
    base_bmr = 10.0 * weight + 6.25 * height - 5.0 * age_val
    if isinstance(gender, str) and gender.lower() == "female":
        bmr = base_bmr - 161.0
    else:
        bmr = base_bmr + 5.0

    # ── TDEE ──────────────────────────────────────────────────────────────────
    multiplier = _ACTIVITY_MULTIPLIERS.get(activity_level, 1.55)
    tdee = bmr * multiplier

    # ── Goal config ───────────────────────────────────────────────────────────
    config = _GOAL_CONFIG.get(goal_type, _GOAL_CONFIG["general_health"])
    kcal_adjust, protein_per_kg, carb_pct, fat_pct, ratio_label = config

    target_calories = tdee + kcal_adjust

    # ── Protein ───────────────────────────────────────────────────────────────
    protein_g = lean_mass * protein_per_kg
    protein_kcal = protein_g * 4.0

    remaining_kcal = target_calories - protein_kcal

    # ── Carbs ─────────────────────────────────────────────────────────────────
    carbs_g = (remaining_kcal * carb_pct) / 4.0

    # ── Fat ───────────────────────────────────────────────────────────────────
    fat_kcal_from_remaining = remaining_kcal * fat_pct
    # Cap fat at 35% of total calories
    max_fat_kcal = target_calories * 0.35
    fat_kcal = min(fat_kcal_from_remaining, max_fat_kcal)
    fat_g = fat_kcal / 9.0

    # ── Fiber ─────────────────────────────────────────────────────────────────
    fiber_g = (target_calories / 1000.0) * 14.0

    notes = (
        f"Based on {weight:.1f}kg body weight, {lean_mass:.1f}kg lean mass, "
        f"{activity_level} activity. Goal: {goal_type.replace('_', ' ')}."
    )

    return MacroTargets(
        calories=round(target_calories),
        protein_g=round(protein_g, 1),
        carbs_g=round(carbs_g, 1),
        fat_g=round(fat_g, 1),
        fiber_g=round(fiber_g, 1),
        bmr=round(bmr),
        tdee=round(tdee),
        goal_adjustment_kcal=kcal_adjust,
        protein_ratio=ratio_label,
        notes=notes,
    )
