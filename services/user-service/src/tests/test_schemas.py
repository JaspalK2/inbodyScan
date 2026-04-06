"""Tests for user-service schema validators."""
import pytest
from pydantic import ValidationError
from ..schemas.user import ProfileUpdate, ProfileOut, HealthGoalSet, HealthGoalOut, DietaryRestrictionAdd, DietaryRestrictionOut


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

    def test_valid_activity_level(self):
        for level in ["sedentary", "lightly_active", "moderately_active", "very_active", "extra_active"]:
            p = ProfileUpdate(activity_level=level)
            assert p.activity_level == level

    def test_invalid_activity_level_raises(self):
        with pytest.raises(ValidationError):
            ProfileUpdate(activity_level="super_active")  # type: ignore

    def test_activity_level_optional(self):
        p = ProfileUpdate(age=25)
        assert p.activity_level is None


class TestProfileOut:
    def test_includes_activity_level_field(self):
        p = ProfileOut(
            id="abc", user_id="xyz",
            first_name=None, last_name=None,
            age=None, height_cm=None, weight_kg=None,
            gender=None, activity_level=None,
        )
        assert hasattr(p, "activity_level")
        assert p.activity_level is None

    def test_activity_level_set(self):
        p = ProfileOut(
            id="abc", user_id="xyz",
            first_name="Test", last_name=None,
            age=30, height_cm=175.0, weight_kg=70.0,
            gender="male", activity_level="very_active",
        )
        assert p.activity_level == "very_active"


class TestHealthGoalOut:
    def test_includes_goal_type(self):
        g = HealthGoalOut(id="abc", user_id="xyz", goal_type="build_muscle")
        assert g.goal_type == "build_muscle"


class TestDietaryRestrictionOut:
    def test_includes_required_fields(self):
        r = DietaryRestrictionOut(id="abc", user_id="xyz", restriction_type="vegan", notes=None)
        assert r.id == "abc"
        assert r.restriction_type == "vegan"
        assert r.notes is None
