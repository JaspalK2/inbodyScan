"""Unit tests for food_seeder.py (013-algorithmic-plan-engine)."""
from __future__ import annotations
import json
import pytest
import pathlib
import tempfile
from unittest.mock import AsyncMock, patch


_MOCK_SEARCH_RESPONSE = {
    "foods": [
        {
            "fdcId": 171705,
            "description": "Chicken breast, raw",
            "foodCategory": "Poultry Products",
            "foodNutrients": [
                {"nutrientId": 1008, "nutrientName": "Energy", "value": 120.0, "unitName": "KCAL"},
                {"nutrientId": 1003, "nutrientName": "Protein", "value": 22.5, "unitName": "G"},
                {"nutrientId": 1005, "nutrientName": "Carbohydrate, by difference", "value": 0.0, "unitName": "G"},
                {"nutrientId": 1004, "nutrientName": "Total lipid (fat)", "value": 2.6, "unitName": "G"},
                {"nutrientId": 1079, "nutrientName": "Fiber, total dietary", "value": 0.0, "unitName": "G"},
            ],
        },
        {
            "fdcId": 169704,
            "description": "Oats, rolled, dry",
            "foodCategory": "Cereal Grains and Pasta",
            "foodNutrients": [
                {"nutrientId": 1008, "nutrientName": "Energy", "value": 379.0, "unitName": "KCAL"},
                {"nutrientId": 1003, "nutrientName": "Protein", "value": 13.2, "unitName": "G"},
                {"nutrientId": 1005, "nutrientName": "Carbohydrate, by difference", "value": 67.7, "unitName": "G"},
                {"nutrientId": 1004, "nutrientName": "Total lipid (fat)", "value": 6.5, "unitName": "G"},
                {"nutrientId": 1079, "nutrientName": "Fiber, total dietary", "value": 10.1, "unitName": "G"},
            ],
        },
    ]
}


@pytest.mark.asyncio
async def test_seed_extracts_macros_correctly():
    """Macros are correctly extracted from the search response."""
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
    from src.services.food_seeder import seed_food_database

    with tempfile.TemporaryDirectory() as tmp:
        out = pathlib.Path(tmp) / "foods.json"

        from unittest.mock import MagicMock
        mock_resp = MagicMock()
        mock_resp.raise_for_status = lambda: None
        mock_resp.json.return_value = _MOCK_SEARCH_RESPONSE

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            count = await seed_food_database("test_key", out)

        assert count == 2
        data = json.loads(out.read_text())
        chicken = next(f for f in data if "Chicken" in f["name"])
        assert chicken["protein_per_100g"] == 22.5
        assert chicken["calories_per_100g"] == 120.0
        assert chicken["carbs_per_100g"] == 0.0


@pytest.mark.asyncio
async def test_seed_restriction_flags_poultry():
    """Poultry category → vegetarian=False, vegan=False, gluten_free=True."""
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
    from src.services.food_seeder import seed_food_database

    with tempfile.TemporaryDirectory() as tmp:
        out = pathlib.Path(tmp) / "foods.json"

        from unittest.mock import MagicMock
        mock_resp = MagicMock()
        mock_resp.raise_for_status = lambda: None
        mock_resp.json.return_value = {"foods": [_MOCK_SEARCH_RESPONSE["foods"][0]]}

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            await seed_food_database("test_key", out)

        data = json.loads(out.read_text())
        chicken = data[0]
        assert chicken["restrictions"]["vegetarian"] is False
        assert chicken["restrictions"]["vegan"] is False
        assert chicken["restrictions"]["gluten_free"] is True


@pytest.mark.asyncio
async def test_seed_returns_correct_count():
    """seed_food_database returns the number of unique foods written."""
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
    from src.services.food_seeder import seed_food_database

    with tempfile.TemporaryDirectory() as tmp:
        out = pathlib.Path(tmp) / "foods.json"

        from unittest.mock import MagicMock
        mock_resp = MagicMock()
        mock_resp.raise_for_status = lambda: None
        mock_resp.json.return_value = _MOCK_SEARCH_RESPONSE

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            count = await seed_food_database("test_key", out)

        assert count == 2


@pytest.mark.asyncio
async def test_seed_deduplicates_by_fdc_id():
    """Duplicate fdc_ids from multiple search queries are deduplicated."""
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
    from src.services.food_seeder import seed_food_database

    # Return same food twice (as if two queries returned same item)
    duplicate_response = {"foods": [_MOCK_SEARCH_RESPONSE["foods"][0], _MOCK_SEARCH_RESPONSE["foods"][0]]}

    with tempfile.TemporaryDirectory() as tmp:
        out = pathlib.Path(tmp) / "foods.json"

        from unittest.mock import MagicMock
        mock_resp = MagicMock()
        mock_resp.raise_for_status = lambda: None
        mock_resp.json.return_value = duplicate_response

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_resp)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            count = await seed_food_database("test_key", out)

        assert count == 1  # deduplicated
