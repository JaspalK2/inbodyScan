"""
Build structured prompts for diet and workout recommendations.
No PII (names, emails, IDs) is included in prompts — only health metrics,
goal type, and dietary restriction enums per the constitution's security rules.
"""
from __future__ import annotations


def build_diet_prompt(
    metrics: dict[str, float | None],
    goal_type: str,
    restrictions: list[str],
    sample_foods: list[dict],
) -> str:
    metrics_lines = "\n".join(
        f"  - {k.replace('_', ' ').title()}: {v}" for k, v in metrics.items() if v is not None
    )
    restrictions_str = ", ".join(restrictions) if restrictions else "none"
    foods_sample = "\n".join(
        f"  - {f['food_name']}: {f['calories_kcal']} kcal, "
        f"P:{f['protein_g']}g C:{f['carbs_g']}g F:{f['fat_g']}g"
        for f in sample_foods[:20]
    )

    return f"""You are a certified sports nutritionist. Based on the following InBody scan metrics and user goal,
create a detailed 7-day meal plan.

BODY METRICS:
{metrics_lines}

HEALTH GOAL: {goal_type.replace('_', ' ')}

DIETARY RESTRICTIONS: {restrictions_str}

REFERENCE FOODS (from USDA FoodData Central — use these for accurate macro data):
{foods_sample}

INSTRUCTIONS:
- Create a 7-day meal plan (breakfast, lunch, dinner, snacks)
- For each day provide: total calories, protein (g), carbohydrates (g), fat (g), fiber (g)
- Include vitamins and minerals highlights
- Strictly respect all dietary restrictions
- Align portion sizes and macros with the stated health goal
- Return JSON with this structure:
{{
  "summary": "brief explanation of approach",
  "daily_targets": {{"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "fiber_g": 0}},
  "days": [
    {{
      "day": 1,
      "meals": [
        {{"meal": "breakfast", "foods": ["food1", "food2"], "calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}},
        {{"meal": "lunch", ...}},
        {{"meal": "dinner", ...}},
        {{"meal": "snack", ...}}
      ],
      "day_totals": {{"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "fiber_g": 0}}
    }}
  ],
  "micronutrient_highlights": ["highlight1", "highlight2"]
}}

Return ONLY the JSON, no markdown, no explanation outside the JSON.
"""


def build_workout_prompt(
    metrics: dict[str, float | None],
    goal_type: str,
) -> str:
    metrics_lines = "\n".join(
        f"  - {k.replace('_', ' ').title()}: {v}" for k, v in metrics.items() if v is not None
    )

    return f"""You are a certified personal trainer and sports scientist. Based on the following InBody scan metrics
and health goal, create a structured 4-week progressive workout program.

BODY METRICS:
{metrics_lines}

HEALTH GOAL: {goal_type.replace('_', ' ')}

INSTRUCTIONS:
- Design a 4-week progressive overload program
- Include 5 workout days per week with 2 rest days
- Specify sets, reps, rest periods, and RPE for each exercise
- Include warm-up and cool-down protocols
- Tailor exercise selection to body composition data (e.g. if high body fat, include cardio emphasis)
- Return JSON with this structure:
{{
  "summary": "brief explanation of program approach",
  "weeks": [
    {{
      "week": 1,
      "days": [
        {{
          "day": 1,
          "focus": "e.g. Upper Body Strength",
          "exercises": [
            {{"name": "exercise", "sets": 3, "reps": "8-12", "rest_seconds": 90, "notes": "..."}}
          ],
          "estimated_duration_minutes": 60
        }}
      ]
    }}
  ],
  "progression_notes": "how to progress across weeks"
}}

Return ONLY the JSON, no markdown, no explanation outside the JSON.
"""
