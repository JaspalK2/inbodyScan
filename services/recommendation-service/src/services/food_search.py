"""
USDA FoodData Central food search.
Data source: https://fdc.nal.usda.gov/
The FoodData Central dataset is produced by the USDA and is in the public domain.
"""
from __future__ import annotations
import os
import httpx
from dataclasses import dataclass

USDA_BASE = "https://api.nal.usda.gov/fdc/v1"

# Nutrient ID → field name mapping
_NUTRIENT_MAP: dict[int, str] = {
    1008: "calories_kcal",
    1003: "protein_g",
    1005: "carbs_g",
    1004: "fat_g",
    1079: "fiber_g",
    2000: "sugar_g",
    1063: "sugar_g",
    1093: "sodium_mg",
    1092: "potassium_mg",
    1087: "calcium_mg",
    1089: "iron_mg",
    1162: "vitamin_c_mg",
    1114: "vitamin_d_ug",
}

_NAME_FRAGMENTS: dict[str, str] = {
    "energy": "calories_kcal",
    "protein": "protein_g",
    "carbohydrate": "carbs_g",
    "total lipid": "fat_g",
    "fiber": "fiber_g",
    "sugars": "sugar_g",
    "sodium": "sodium_mg",
    "potassium": "potassium_mg",
    "calcium": "calcium_mg",
    "iron": "iron_mg",
    "vitamin c": "vitamin_c_mg",
    "vitamin d": "vitamin_d_ug",
}


@dataclass
class FoodResult:
    fdc_id: int
    name: str
    brand: str | None
    category: str | None
    calories_kcal: float | None
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None
    fiber_g: float | None
    sugar_g: float | None
    sodium_mg: float | None
    potassium_mg: float | None
    calcium_mg: float | None
    iron_mg: float | None
    vitamin_c_mg: float | None
    vitamin_d_ug: float | None
    serving_size: float | None
    serving_unit: str | None


def _parse_nutrients(food: dict) -> dict[str, float | None]:
    result: dict[str, float | None] = {
        "calories_kcal": None,
        "protein_g": None,
        "carbs_g": None,
        "fat_g": None,
        "fiber_g": None,
        "sugar_g": None,
        "sodium_mg": None,
        "potassium_mg": None,
        "calcium_mg": None,
        "iron_mg": None,
        "vitamin_c_mg": None,
        "vitamin_d_ug": None,
    }

    nutrients = food.get("foodNutrients") or []
    for n in nutrients:
        # nutrientId may be nested under "nutrient" key (detail endpoint)
        nutrient_id = n.get("nutrientId") or (n.get("nutrient") or {}).get("id")
        nutrient_name = (n.get("nutrientName") or (n.get("nutrient") or {}).get("name") or "").lower()
        value = n.get("value") or n.get("amount")

        if value is None:
            continue

        field = None
        if nutrient_id and nutrient_id in _NUTRIENT_MAP:
            field = _NUTRIENT_MAP[nutrient_id]
        else:
            for frag, fname in _NAME_FRAGMENTS.items():
                if frag in nutrient_name:
                    field = fname
                    break

        if field and result.get(field) is None:
            result[field] = float(value)

    return result


def _build_food_result(food: dict) -> FoodResult:
    nutrients = _parse_nutrients(food)
    return FoodResult(
        fdc_id=food.get("fdcId", 0),
        name=food.get("description") or food.get("lowercaseDescription") or "",
        brand=food.get("brandOwner") or food.get("brandName"),
        category=food.get("foodCategory") or food.get("foodCategoryLabel"),
        serving_size=food.get("servingSize"),
        serving_unit=food.get("servingSizeUnit"),
        **nutrients,  # type: ignore[arg-type]
    )


async def search_foods(query: str, page_size: int = 25) -> list[FoodResult]:
    api_key = os.environ["USDA_API_KEY"]
    params = {
        "query": query,
        "pageSize": page_size,
        "api_key": api_key,
        "dataType": "Foundation,SR Legacy,Branded",
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(f"{USDA_BASE}/foods/search", params=params)
        response.raise_for_status()
        data = response.json()

    foods = data.get("foods") or []
    return [_build_food_result(f) for f in foods]


async def get_food_detail(fdc_id: int) -> FoodResult | None:
    api_key = os.environ["USDA_API_KEY"]
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.get(
            f"{USDA_BASE}/food/{fdc_id}",
            params={"api_key": api_key},
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()

    return _build_food_result(data)
