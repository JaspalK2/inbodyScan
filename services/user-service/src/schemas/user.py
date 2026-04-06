from __future__ import annotations
from pydantic import BaseModel, field_validator
from typing import Literal

VALID_GOALS = {"lose_fat", "build_muscle", "maintain", "improve_endurance", "general_health"}
VALID_RESTRICTIONS = {
    "vegetarian", "vegan", "no_pork", "no_beef", "no_eggs",
    "no_dairy", "nut_allergy", "gluten_free", "halal", "kosher", "other",
}


VALID_ACTIVITY_LEVELS = {"sedentary", "lightly_active", "moderately_active", "very_active", "extra_active"}


class ProfileUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    age: int | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    gender: Literal["male", "female", "other"] | None = None
    activity_level: Literal["sedentary", "lightly_active", "moderately_active", "very_active", "extra_active"] | None = None


class ProfileOut(BaseModel):
    id: str
    user_id: str
    first_name: str | None
    last_name: str | None
    age: int | None
    height_cm: float | None
    weight_kg: float | None
    gender: str | None
    activity_level: str | None

    model_config = {"from_attributes": True}


class HealthGoalSet(BaseModel):
    goal_type: str

    @field_validator("goal_type")
    @classmethod
    def validate_goal(cls, v: str) -> str:
        if v not in VALID_GOALS:
            raise ValueError(f"goal_type must be one of {sorted(VALID_GOALS)}")
        return v


class HealthGoalOut(BaseModel):
    id: str
    user_id: str
    goal_type: str

    model_config = {"from_attributes": True}


class DietaryRestrictionAdd(BaseModel):
    restriction_type: str
    notes: str | None = None

    @field_validator("restriction_type")
    @classmethod
    def validate_restriction(cls, v: str) -> str:
        if v not in VALID_RESTRICTIONS:
            raise ValueError(f"restriction_type must be one of {sorted(VALID_RESTRICTIONS)}")
        return v


class DietaryRestrictionOut(BaseModel):
    id: str
    user_id: str
    restriction_type: str
    notes: str | None

    model_config = {"from_attributes": True}
