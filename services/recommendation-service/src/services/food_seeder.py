"""
USDA FoodData Central food database seeder.

Fetches Foundation Foods from the USDA free API and writes them to a local
JSON file (src/data/foods.json). Generation reads only the local file —
no live API call at plan generation time.

Data source: USDA FoodData Central (public domain)
https://fdc.nal.usda.gov/
"""
from __future__ import annotations
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

USDA_BASE = "https://api.nal.usda.gov/fdc/v1"
DEFAULT_FOODS_PATH = Path(__file__).parent.parent / "data" / "foods.json"

# Nutrient IDs → macro field names (reuses same mapping as food_search.py)
_NUTRIENT_MAP: dict[int, str] = {
    1008: "calories_per_100g",
    1003: "protein_per_100g",
    1005: "carbs_per_100g",
    1004: "fat_per_100g",
    1079: "fiber_per_100g",
}

# Category string fragments → dietary restriction flags
# If a category contains any of these keywords, the flag is set to False
_RESTRICTION_RULES: dict[str, list[str]] = {
    "vegetarian": ["poultry", "beef", "pork", "lamb", "veal", "game", "sausage",
                   "luncheon", "finfish", "shellfish", "fish", "seafood", "meat"],
    "vegan":      ["poultry", "beef", "pork", "lamb", "veal", "game", "sausage",
                   "luncheon", "finfish", "shellfish", "fish", "seafood", "meat",
                   "dairy", "milk", "cheese", "egg", "cream", "butter", "yogurt",
                   "whey", "casein"],
    "gluten_free": ["wheat", "barley", "rye", "bread", "pasta", "cereal",
                    "flour", "cracker", "pretzel", "biscuit"],
    "dairy_free":  ["dairy", "milk", "cheese", "cream", "butter", "yogurt",
                    "whey", "casein", "ice cream"],
    "halal":       ["pork", "lard", "gelatin", "swine"],
    "kosher":      ["pork", "lard", "shellfish", "swine"],
}

# Category fragments → which meal slots the food suits
_SLOT_MAP: dict[str, list[str]] = {
    "cereal":       ["breakfast", "snack"],
    "grain":        ["breakfast", "lunch", "dinner"],
    "oat":          ["breakfast"],
    "egg":          ["breakfast", "lunch"],
    "dairy":        ["breakfast", "snack"],
    "milk":         ["breakfast", "snack"],
    "cheese":       ["lunch", "dinner", "snack"],
    "yogurt":       ["breakfast", "snack"],
    "fruit":        ["breakfast", "snack"],
    "vegetable":    ["lunch", "dinner"],
    "legume":       ["lunch", "dinner"],
    "bean":         ["lunch", "dinner"],
    "nut":          ["snack"],
    "poultry":      ["lunch", "dinner"],
    "beef":         ["lunch", "dinner"],
    "pork":         ["lunch", "dinner"],
    "fish":         ["lunch", "dinner"],
    "finfish":      ["lunch", "dinner"],
    "shellfish":    ["lunch", "dinner"],
    "seafood":      ["lunch", "dinner"],
    "lamb":         ["lunch", "dinner"],
    "rice":         ["lunch", "dinner"],
    "pasta":        ["lunch", "dinner"],
    "bread":        ["breakfast", "lunch", "snack"],
    "oil":          ["lunch", "dinner"],
    "fat":          ["lunch", "dinner"],
    "sweet":        ["snack"],
    "candy":        ["snack"],
    "snack":        ["snack"],
    "beverage":     ["breakfast", "snack"],
}


def _parse_macros(food: dict) -> dict[str, float]:
    result = {f: 0.0 for f in _NUTRIENT_MAP.values()}
    for n in food.get("foodNutrients") or []:
        # Search endpoint uses nutrientId; list endpoint uses number (string)
        nid = (
            n.get("nutrientId")
            or (n.get("nutrient") or {}).get("id")
        )
        if nid is None:
            # Fall back to converting number string to int
            try:
                nid = int(n.get("number", "0"))
            except (ValueError, TypeError):
                nid = 0
        value = n.get("value") if n.get("value") is not None else n.get("amount")
        if nid in _NUTRIENT_MAP and value is not None:
            field = _NUTRIENT_MAP[nid]
            # Only take KCAL for calories (not kJ — nutrient 1008 is kcal)
            if field == "calories_per_100g" and n.get("unitName", "").upper() not in ("KCAL", ""):
                continue
            if result[field] == 0.0:  # don't overwrite already-set value
                result[field] = float(value)
    return result


def _restriction_flags(category: str) -> dict[str, bool]:
    cat_lower = (category or "").lower()
    flags: dict[str, bool] = {}
    for restriction, keywords in _RESTRICTION_RULES.items():
        flags[restriction] = not any(kw in cat_lower for kw in keywords)
    return flags


def _meal_slots(category: str) -> list[str]:
    cat_lower = (category or "").lower()
    for kw, slots in _SLOT_MAP.items():
        if kw in cat_lower:
            return slots
    return ["lunch", "dinner", "snack"]


def _food_tags(category: str, macros: dict) -> list[str]:
    tags = []
    cat_lower = (category or "").lower()
    protein = macros.get("protein_per_100g", 0)
    carbs = macros.get("carbs_per_100g", 0)
    fat = macros.get("fat_per_100g", 0)
    if protein >= 15:
        tags.append("protein_source")
    if carbs >= 30:
        tags.append("carb_source")
    if fat >= 15:
        tags.append("fat_source")
    if any(kw in cat_lower for kw in ["vegetable", "fruit", "legume", "bean"]):
        tags.append("vegetable" if "vegetable" in cat_lower else "produce")
    if any(kw in cat_lower for kw in ["dairy", "milk", "cheese", "yogurt"]):
        tags.append("dairy")
    if any(kw in cat_lower for kw in ["poultry", "beef", "pork", "fish", "seafood", "lamb"]):
        tags.append("meat")
    return tags


# Curated search queries covering all major food groups needed for plan generation
_SEED_QUERIES = [
    "chicken breast", "chicken thigh", "turkey breast", "ground beef", "salmon fillet",
    "tuna canned", "tilapia", "shrimp", "egg whole", "egg white",
    "greek yogurt", "cottage cheese", "milk whole", "cheddar cheese",
    "oats rolled", "brown rice", "white rice", "quinoa", "whole wheat bread",
    "sweet potato", "potato", "pasta whole wheat",
    "broccoli", "spinach", "kale", "mixed greens", "tomato", "cucumber",
    "avocado", "olive oil", "almonds", "walnuts", "peanut butter",
    "black beans", "lentils", "chickpeas", "tofu",
    "banana", "apple", "blueberries", "strawberries", "orange",
    "whey protein", "casein protein",
    "beef steak", "pork tenderloin", "lamb chop",
]


async def seed_food_database(
    usda_api_key: str,
    output_path: Path = DEFAULT_FOODS_PATH,
) -> int:
    """Fetch whole foods from USDA search API and write to output_path as JSON.

    Uses curated search queries to get nutrient-rich, categorised foods.
    Returns the number of unique foods written.
    """
    logger.info("Seeding food database from USDA FoodData Central...")

    foods_raw: list[dict] = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for query in _SEED_QUERIES:
            params = {
                "query": query,
                "dataType": "Foundation,SR Legacy",
                "pageSize": 5,
                "api_key": usda_api_key,
            }
            try:
                resp = await client.get(f"{USDA_BASE}/foods/search", params=params)
                resp.raise_for_status()
                data = resp.json()
                foods_raw.extend(data.get("foods") or [])
            except httpx.HTTPError as exc:
                logger.warning("USDA search failed for '%s': %s", query, exc)

    now = datetime.now(timezone.utc).isoformat()
    foods_out = []

    for food in foods_raw:
        category = (food.get("foodCategory") or food.get("foodCategoryLabel") or "").strip()
        macros = _parse_macros(food)

        # Skip foods with no meaningful macro data
        if macros["calories_per_100g"] == 0 and macros["protein_per_100g"] == 0:
            continue

        entry = {
            "fdc_id": food.get("fdcId", 0),
            "name": food.get("description") or "",
            "category": category,
            "meal_slots": _meal_slots(category),
            "tags": _food_tags(category, macros),
            "restrictions": _restriction_flags(category),
            "last_updated": now,
            **macros,
        }
        foods_out.append(entry)

    # Deduplicate by fdc_id
    seen: set[int] = set()
    unique: list[dict] = []
    for f in foods_out:
        if f["fdc_id"] not in seen:
            seen.add(f["fdc_id"])
            unique.append(f)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as fp:
        json.dump(unique, fp, indent=2)

    logger.info("Food database seeded: %d foods written to %s", len(unique), output_path)
    return len(unique)


async def refresh_food_db_job() -> int:
    """Entry point for the weekly APScheduler job and the manual refresh endpoint."""
    api_key = os.environ.get("USDA_API_KEY", "")
    if not api_key:
        logger.warning("USDA_API_KEY not set — skipping food database refresh")
        return 0
    return await seed_food_database(api_key, DEFAULT_FOODS_PATH)
