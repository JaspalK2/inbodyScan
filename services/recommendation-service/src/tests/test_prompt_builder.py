"""Tests for the LLM prompt builder."""
import pytest
from ..services.prompt_builder import build_diet_prompt, build_workout_prompt


SAMPLE_METRICS = {
    "body_weight_kg": 75.5,
    "body_fat_percentage": 24.3,
    "skeletal_muscle_mass_kg": 32.1,
    "fat_free_mass_kg": 57.2,
    "body_mass_index": 24.5,
}

SAMPLE_FOODS = [
    {"food_name": "Chicken Breast", "calories_kcal": 165, "protein_g": 31, "carbs_g": 0, "fat_g": 3.6},
    {"food_name": "Brown Rice", "calories_kcal": 216, "protein_g": 5, "carbs_g": 45, "fat_g": 1.8},
]


class TestDietPromptBuilder:
    def test_prompt_contains_goal(self):
        prompt = build_diet_prompt(SAMPLE_METRICS, "lose_fat", [], SAMPLE_FOODS)
        assert "lose fat" in prompt.lower()

    def test_prompt_contains_restrictions(self):
        prompt = build_diet_prompt(SAMPLE_METRICS, "build_muscle", ["vegetarian", "no_eggs"], SAMPLE_FOODS)
        assert "vegetarian" in prompt
        assert "no_eggs" in prompt

    def test_prompt_contains_metrics(self):
        prompt = build_diet_prompt(SAMPLE_METRICS, "maintain", [], SAMPLE_FOODS)
        assert "75.5" in prompt
        assert "24.3" in prompt

    def test_prompt_contains_json_instructions(self):
        prompt = build_diet_prompt(SAMPLE_METRICS, "general_health", [], SAMPLE_FOODS)
        assert "JSON" in prompt

    def test_no_pii_in_prompt(self):
        """Verify no user IDs or email patterns appear in prompts."""
        prompt = build_diet_prompt(SAMPLE_METRICS, "lose_fat", [], SAMPLE_FOODS)
        assert "@" not in prompt
        assert "user_id" not in prompt


class TestWorkoutPromptBuilder:
    def test_prompt_contains_goal(self):
        prompt = build_workout_prompt(SAMPLE_METRICS, "build_muscle")
        assert "build muscle" in prompt.lower()

    def test_prompt_contains_metrics(self):
        prompt = build_workout_prompt(SAMPLE_METRICS, "improve_endurance")
        assert "75.5" in prompt

    def test_prompt_requests_json(self):
        prompt = build_workout_prompt(SAMPLE_METRICS, "general_health")
        assert "JSON" in prompt

    def test_no_pii_in_prompt(self):
        prompt = build_workout_prompt(SAMPLE_METRICS, "lose_fat")
        assert "user_id" not in prompt
        assert "@" not in prompt
