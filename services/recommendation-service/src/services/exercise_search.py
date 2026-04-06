"""Exercise search service — filters the CC0 exercise dataset by name.

Dataset: yuhonas/free-exercise-db
License: CC0 1.0 Universal (Public Domain Dedication)
Source: https://github.com/yuhonas/free-exercise-db
"""
from __future__ import annotations
import json
import os

# Load dataset once at module import time (873 exercises, ~150 KB — negligible memory)
_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "exercises.json")

with open(_DATA_PATH, encoding="utf-8") as _f:
    _EXERCISES: list[dict] = json.load(_f)


def search_exercises(q: str, limit: int = 20) -> list[dict]:
    """Case-insensitive substring search on exercise name.

    Returns up to `limit` results shaped as ExerciseSearchResult dicts.
    """
    q_lower = q.lower()
    results = []
    for ex in _EXERCISES:
        if q_lower in ex.get("name", "").lower():
            results.append({
                "name": ex.get("name", ""),
                "primary_muscles": ex.get("primaryMuscles", []),
                "secondary_muscles": ex.get("secondaryMuscles", []),
                "category": ex.get("category", ""),
                "equipment": ex.get("equipment", ""),
                "level": ex.get("level", ""),
            })
            if len(results) >= limit:
                break
    return results
