#!/usr/bin/env bash
# Seed NutritionalFood table from USDA FoodData Central API.
# Usage: USDA_API_KEY=<key> ./scripts/seed-usda-data.sh
# Fetches the 500 most common foods and upserts into the recommendation-service DB.
set -e

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
set -a; source "$ROOT/.env"; set +a

if [ -z "$USDA_API_KEY" ]; then
  echo "ERROR: USDA_API_KEY not set in .env"
  exit 1
fi

VENV="$ROOT/services/recommendation-service/.venv"
if [ ! -d "$VENV" ]; then
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q --upgrade pip
  "$VENV/bin/pip" install -q -r "$ROOT/services/recommendation-service/requirements.txt"
fi

"$VENV/bin/python3" - <<'PYEOF'
import asyncio, os, sys, httpx, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from shared.python.db_utils.session import make_engine, make_session_factory
from services.recommendation_service.src.models.nutritional_food import NutritionalFood
from shared.python.db_utils.session import Base
from sqlalchemy.dialects.postgresql import insert

API_KEY = os.environ["USDA_API_KEY"]
FDC_URL = "https://api.nal.usda.gov/fdc/v1/foods/list"

async def fetch_foods(page: int) -> list[dict]:
    params = {"api_key": API_KEY, "pageSize": 50, "pageNumber": page, "dataType": ["SR Legacy", "Foundation"]}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(FDC_URL, params=params)
        resp.raise_for_status()
        return resp.json()

NUTRIENT_IDS = {
    "calories_kcal": 1008,
    "protein_g": 1003,
    "carbs_g": 1005,
    "fat_g": 1004,
    "fiber_g": 1079,
    "sugar_g": 2000,
    "sodium_mg": 1093,
    "vitamin_a_ug": 1106,
    "vitamin_c_mg": 1162,
    "vitamin_d_ug": 1114,
    "calcium_mg": 1087,
    "iron_mg": 1089,
    "potassium_mg": 1092,
}

def extract_nutrient(food: dict, nutrient_id: int) -> float | None:
    for n in food.get("foodNutrients", []):
        if n.get("nutrientId") == nutrient_id:
            return n.get("value")
    return None

async def main():
    engine = make_engine("RECOMMENDATION_DATABASE_URL")
    session_factory = make_session_factory(engine)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    all_foods = []
    for page in range(1, 11):  # 10 pages × 50 = 500 foods
        print(f"Fetching page {page}/10...")
        foods = await fetch_foods(page)
        all_foods.extend(foods)
        if len(foods) < 50:
            break

    async with session_factory() as session:
        for food in all_foods:
            row = {
                "fdc_id": food["fdcId"],
                "food_name": food.get("description", "")[:255],
                "category": (food.get("foodCategory") or "")[:100],
                **{k: extract_nutrient(food, v) for k, v in NUTRIENT_IDS.items()}
            }
            stmt = insert(NutritionalFood.__table__).values(**row)
            stmt = stmt.on_conflict_do_update(
                index_elements=["fdc_id"],
                set_={k: stmt.excluded[k] for k in row if k != "fdc_id"}
            )
            await session.execute(stmt)
        await session.commit()

    print(f"Seeded {len(all_foods)} foods.")
    await engine.dispose()

asyncio.run(main())
PYEOF
