"""Tests for DELETE /api/recommendations/workout/{rec_id} endpoint (US4)."""
from __future__ import annotations
import pytest


def test_delete_workout_route_exists():
    """The workout router must include a DELETE route for /{rec_id}."""
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from src.routers.recommendations import router
    routes = [(r.path, list(r.methods)) for r in router.routes]  # type: ignore[attr-defined]
    delete_routes = [path for path, methods in routes if "DELETE" in methods and "workout" in path and "{rec_id}" in path]
    assert len(delete_routes) > 0, "No DELETE /workout/{rec_id} route found in recommendations router"


def test_delete_workout_path_matches_diet_pattern():
    """Workout delete path must follow the same pattern as diet delete."""
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from src.routers.recommendations import router
    routes = {r.path: list(r.methods) for r in router.routes}  # type: ignore[attr-defined]

    diet_delete = "/api/recommendations/diet/{rec_id}"
    workout_delete = "/api/recommendations/workout/{rec_id}"

    assert diet_delete in routes and "DELETE" in routes[diet_delete], \
        "Diet DELETE route expected as reference pattern"
    assert workout_delete in routes and "DELETE" in routes[workout_delete], \
        "Workout DELETE route must mirror the diet DELETE pattern"


def test_workout_router_has_no_extra_delete_routes():
    """Only one workout DELETE route should exist (/{rec_id}), no wildcard extras."""
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from src.routers.recommendations import router
    workout_deletes = [
        r.path for r in router.routes  # type: ignore[attr-defined]
        if "DELETE" in list(r.methods) and "workout" in r.path  # type: ignore[attr-defined]
    ]
    assert len(workout_deletes) == 1, \
        f"Expected exactly 1 workout DELETE route, found: {workout_deletes}"
