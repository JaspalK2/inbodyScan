"""Tests for user-service schema validators."""
import pytest
from pydantic import ValidationError
from ..schemas.user import ProfileUpdate, HealthGoalSet, DietaryRestrictionAdd


class TestHealthGoalSet:
    def test_valid_goal(self):
        g = HealthGoalSet(goal_type="lose_fat")
        assert g.goal_type == "lose_fat"

    def test_all_valid_goals(self):
        for goal in ["lose_fat", "build_muscle", "maintain", "improve_endurance", "general_health"]:
            HealthGoalSet(goal_type=goal)

    def test_invalid_goal_raises(self):
        with pytest.raises(ValidationError):
            HealthGoalSet(goal_type="get_ripped")


class TestDietaryRestrictionAdd:
    def test_valid_restriction(self):
        r = DietaryRestrictionAdd(restriction_type="vegan")
        assert r.restriction_type == "vegan"

    def test_invalid_restriction_raises(self):
        with pytest.raises(ValidationError):
            DietaryRestrictionAdd(restriction_type="no_pineapple")

    def test_notes_optional(self):
        r = DietaryRestrictionAdd(restriction_type="halal")
        assert r.notes is None


class TestProfileUpdate:
    def test_valid_profile_partial(self):
        p = ProfileUpdate(age=30, height_cm=175.0)
        assert p.age == 30

    def test_invalid_gender(self):
        with pytest.raises(ValidationError):
            ProfileUpdate(gender="unknown")  # type: ignore
