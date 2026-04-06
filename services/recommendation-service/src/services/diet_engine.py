"""
Algorithmic diet plan generator.
Builds a 7-day meal plan from the local USDA-seeded food database.
No external API calls; fully deterministic given the same inputs.
"""
from __future__ import annotations

import json
import logging
import pathlib
import random
from dataclasses import dataclass
from typing import Any

from .plan_explainer import build_diet_explanation

logger = logging.getLogger(__name__)

_DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
_FOODS_PATH = _DATA_DIR / "foods.json"

# Proportion of daily targets assigned to each meal slot
MEAL_SLOT_RATIOS: dict[str, float] = {
    "breakfast": 0.25,
    "lunch": 0.35,
    "dinner": 0.30,
    "snack": 0.10,
}

# How many food items to include per meal slot
_SLOT_ITEM_COUNTS: dict[str, int] = {
    "breakfast": 3,
    "lunch": 4,
    "dinner": 4,
    "snack": 2,
}

# Tags that indicate a "protein source" vs other food types
_PROTEIN_TAGS = {"protein_source", "meat", "dairy", "legume"}
_CARB_TAGS = {"carb_source", "grain", "fruit"}
_FAT_TAGS = {"fat_source"}


def _load_foods() -> list[dict]:
    if not _FOODS_PATH.exists():
        logger.warning("foods.json not found at %s – diet plan will be sparse", _FOODS_PATH)
        return []
    with open(_FOODS_PATH, "r") as f:
        return json.load(f)


def _filter_foods(foods: list[dict], slot: str, restrictions: list[str]) -> list[dict]:
    """Return foods available for a given meal slot that meet dietary restrictions."""
    result = []
    for food in foods:
        # Must include this meal slot
        if slot not in food.get("meal_slots", []):
            continue
        # Must satisfy all restriction flags
        food_restrictions = food.get("restrictions", {})
        skip = False
        for r in restrictions:
            if r in food_restrictions and not food_restrictions[r]:
                skip = True
                break
        if not skip:
            result.append(food)
    return result


def _pick_items(
    available: list[dict],
    n: int,
    rng: random.Random,
) -> list[dict]:
    """Pick up to n foods, trying to include protein + carb + fat variety."""
    if not available:
        return []

    protein_foods = [f for f in available if any(t in _PROTEIN_TAGS for t in f.get("tags", []))]
    carb_foods = [f for f in available if any(t in _CARB_TAGS for t in f.get("tags", []))]
    fat_foods = [f for f in available if any(t in _FAT_TAGS for t in f.get("tags", []))]
    other = [f for f in available if f not in protein_foods and f not in carb_foods and f not in fat_foods]

    chosen: list[dict] = []
    used_ids: set = set()

    def _pick_one(pool: list[dict]) -> dict | None:
        candidates = [f for f in pool if f["fdc_id"] not in used_ids]
        if not candidates:
            return None
        item = rng.choice(candidates)
        used_ids.add(item["fdc_id"])
        return item

    # Always try protein + carb first
    p = _pick_one(protein_foods)
    if p:
        chosen.append(p)
    c = _pick_one(carb_foods)
    if c:
        chosen.append(c)

    # Fill remaining slots from fat / other / general pool
    fill_pools = [fat_foods, other, available]
    while len(chosen) < n:
        added = False
        for pool in fill_pools:
            item = _pick_one(pool)
            if item:
                chosen.append(item)
                added = True
                break
        if not added:
            break

    return chosen[:n]


def _scale_item(food: dict, target_calories: float) -> dict:
    """Scale a food item to match a target calorie contribution, return meal item dict."""
    cal_per_100g = food.get("calories_per_100g") or 100.0
    grams = max(20.0, min(600.0, (target_calories / cal_per_100g) * 100.0))

    factor = grams / 100.0
    return {
        "food_name": food["name"],
        "fdc_id": food["fdc_id"],
        "grams": round(grams, 1),
        "calories": round(food.get("calories_per_100g", 0) * factor, 1),
        "protein_g": round(food.get("protein_per_100g", 0) * factor, 1),
        "carbs_g": round(food.get("carbs_per_100g", 0) * factor, 1),
        "fat_g": round(food.get("fat_per_100g", 0) * factor, 1),
        "fiber_g": round(food.get("fiber_per_100g", 0) * factor, 1),
    }


def _build_meal(
    slot: str,
    slot_ratio: float,
    macro_targets,
    available: list[dict],
    rng: random.Random,
) -> dict:
    """Build a single meal for the given slot."""
    target_cal = macro_targets.calories * slot_ratio
    n_items = _SLOT_ITEM_COUNTS.get(slot, 3)
    items = _pick_items(available, n_items, rng)

    if not items:
        return {
            "meal_name": slot.capitalize(),
            "items": [],
            "meal_totals": {"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "fiber_g": 0},
        }

    # Distribute target calories evenly across items
    cal_per_item = target_cal / len(items)
    scaled = [_scale_item(item, cal_per_item) for item in items]

    meal_totals = {
        "calories": round(sum(i["calories"] for i in scaled), 1),
        "protein_g": round(sum(i["protein_g"] for i in scaled), 1),
        "carbs_g": round(sum(i["carbs_g"] for i in scaled), 1),
        "fat_g": round(sum(i["fat_g"] for i in scaled), 1),
        "fiber_g": round(sum(i["fiber_g"] for i in scaled), 1),
    }

    return {
        "meal_name": slot.capitalize(),
        "items": scaled,
        "meal_totals": meal_totals,
    }


def _rescale_item(item: dict, scale: float) -> dict:
    """Return a new item dict with gram quantity multiplied by scale (clamped [20, 600])."""
    new_grams = max(20.0, min(600.0, item["grams"] * scale))
    factor = new_grams / 100.0
    # Look up per-100g values from original item ratios
    original_factor = item["grams"] / 100.0
    def _per100(val: float) -> float:
        return val / original_factor if original_factor else 0.0

    return {
        "food_name": item["food_name"],
        "fdc_id": item.get("fdc_id"),
        "grams": round(new_grams, 1),
        "calories": round(_per100(item["calories"]) * factor, 2),
        "protein_g": round(_per100(item["protein_g"]) * factor, 2),
        "carbs_g": round(_per100(item["carbs_g"]) * factor, 2),
        "fat_g": round(_per100(item["fat_g"]) * factor, 2),
        "fiber_g": round(_per100(item.get("fiber_g", 0)) * factor, 2),
    }


def _recompute_meal_totals(meal: dict) -> dict:
    """Return meal dict with meal_totals recomputed from items."""
    totals = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "fiber_g": 0.0}
    for item in meal["items"]:
        for k in totals:
            totals[k] += item.get(k, 0)
    return {**meal, "meal_totals": {k: round(v, 1) for k, v in totals.items()}}


def _build_day(
    day_num: int,
    macro_targets,
    restrictions: list[str],
    foods: list[dict],
    rng: random.Random,
) -> dict:
    """Build a single day's meals with caloric correction to stay within ±5% of target."""
    slot_items = list(MEAL_SLOT_RATIOS.items())
    meals = []
    for slot, ratio in slot_items:
        available = _filter_foods(foods, slot, restrictions)
        meal = _build_meal(slot, ratio, macro_targets, available, rng)
        meals.append(meal)

    # FR-005: redistribute caloric share of empty slots to non-empty slots
    empty_cal = sum(
        macro_targets.calories * ratio
        for meal, (slot, ratio) in zip(meals, slot_items)
        if not meal["items"]
    )
    non_empty_indices = [i for i, m in enumerate(meals) if m["items"]]
    if empty_cal > 0 and non_empty_indices:
        non_empty_ratios = [slot_items[i][1] for i in non_empty_indices]
        total_non_empty_ratio = sum(non_empty_ratios)
        for i, r in zip(non_empty_indices, non_empty_ratios):
            extra_cal = empty_cal * (r / total_non_empty_ratio)
            actual_cal = meals[i]["meal_totals"]["calories"]
            if actual_cal > 0:
                scale = (actual_cal + extra_cal) / actual_cal
                meals[i] = _recompute_meal_totals({
                    **meals[i],
                    "items": [_rescale_item(item, scale) for item in meals[i]["items"]],
                })

    # Day-level correction pass: iteratively scale items toward caloric target.
    # Up to 5 passes handle cases where floor/ceiling clamping prevents full correction
    # in a single step.
    for _pass in range(5):
        actual_total = sum(m["meal_totals"]["calories"] for m in meals)
        if actual_total <= 0:
            break
        scale = macro_targets.calories / actual_total
        if 0.998 <= scale <= 1.002:
            break  # within ±0.2% — stop correcting
        new_meals = []
        for meal in meals:
            new_items = [_rescale_item(item, scale) for item in meal["items"]]
            new_meals.append(_recompute_meal_totals({**meal, "items": new_items}))
        meals = new_meals

    # If still over target after scaling (all items floor-clamped), drop lowest-cal
    # item from the most over-allocated meal until within ±5%.
    for _guard in range(20):
        actual_total = sum(m["meal_totals"]["calories"] for m in meals)
        if actual_total <= 0 or actual_total <= macro_targets.calories * 1.049:
            break
        # Find the meal with the most items (most room to drop)
        drop_idx = max(
            (i for i, m in enumerate(meals) if m["items"]),
            key=lambda i: len(meals[i]["items"]),
            default=None,
        )
        if drop_idx is None:
            break
        # Drop the highest-calorie item from that meal
        items = meals[drop_idx]["items"]
        drop_item_idx = max(range(len(items)), key=lambda j: items[j].get("calories", 0))
        new_items = [item for k, item in enumerate(items) if k != drop_item_idx]
        meals[drop_idx] = _recompute_meal_totals({**meals[drop_idx], "items": new_items})

    # Recompute day totals from corrected meals
    day_totals: dict[str, float] = {"calories": 0.0, "protein_g": 0.0, "carbs_g": 0.0, "fat_g": 0.0, "fiber_g": 0.0}
    for meal in meals:
        for k in day_totals:
            day_totals[k] += meal["meal_totals"].get(k, 0)
    day_totals = {k: round(v, 1) for k, v in day_totals.items()}

    return {
        "day": day_num,
        "meals": meals,
        "day_totals": day_totals,
    }


def generate_diet_plan(
    macro_targets,
    restrictions: list[str],
    goal_type: str,
) -> dict:
    """
    Generate a 7-day diet plan algorithmically.

    Args:
        macro_targets: MacroTargets dataclass with calories/protein_g/carbs_g/fat_g
        restrictions: list of dietary restriction keys (e.g. ["vegetarian", "gluten_free"])
        goal_type: goal string (lose_fat, build_muscle, etc.)

    Returns:
        dict matching the structured_plan JSON schema
    """
    foods = _load_foods()

    # Use a deterministic seed based on macro targets so same inputs → same plan
    seed = int(macro_targets.calories) + int(macro_targets.protein_g * 10)
    rng = random.Random(seed)

    days = []
    for day_num in range(1, 8):
        day = _build_day(day_num, macro_targets, restrictions, foods, rng)
        days.append(day)

    plan_explanation = build_diet_explanation(macro_targets, goal_type)

    return {
        "days": days,
        "plan_explanation": plan_explanation,
        "goal_type": goal_type,
        "restrictions": restrictions,
    }
