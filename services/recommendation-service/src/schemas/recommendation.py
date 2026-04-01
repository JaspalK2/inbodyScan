from __future__ import annotations
import json
from datetime import datetime
from pydantic import BaseModel, model_validator


class GenerateDietRequest(BaseModel):
    scan_id: str
    metrics: dict[str, float | None]
    goal_type: str
    dietary_restrictions: list[str] = []


class GenerateWorkoutRequest(BaseModel):
    scan_id: str
    metrics: dict[str, float | None]
    goal_type: str


class DietRecommendationOut(BaseModel):
    id: str
    user_id: str
    scan_id: str
    goal_type: str
    structured_plan: dict
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def parse_structured_plan(cls, values):
        if hasattr(values, "__dict__"):
            plan = values.structured_plan
        else:
            plan = values.get("structured_plan")
        if isinstance(plan, str):
            try:
                if hasattr(values, "__dict__"):
                    object.__setattr__(values, "structured_plan", json.loads(plan))
                else:
                    values["structured_plan"] = json.loads(plan)
            except json.JSONDecodeError:
                pass
        return values


class WorkoutRecommendationOut(BaseModel):
    id: str
    user_id: str
    scan_id: str
    goal_type: str
    structured_plan: dict
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def parse_structured_plan(cls, values):
        if hasattr(values, "__dict__"):
            plan = values.structured_plan
        else:
            plan = values.get("structured_plan")
        if isinstance(plan, str):
            try:
                if hasattr(values, "__dict__"):
                    object.__setattr__(values, "structured_plan", json.loads(plan))
                else:
                    values["structured_plan"] = json.loads(plan)
            except json.JSONDecodeError:
                pass
        return values
