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
    macro_targets,  # MacroTargets dataclass
) -> str:
    metrics_lines = "\n".join(
        f"  - {k.replace('_', ' ').title()}: {v}" for k, v in metrics.items() if v is not None
    )
    restrictions_str = ", ".join(restrictions) if restrictions else "none"

    return f"""You are a certified sports nutritionist. Based on the following InBody scan metrics, health goal,
and pre-calculated macro targets, create a detailed 7-day meal plan that hits those targets.

BODY METRICS:
{metrics_lines}

HEALTH GOAL: {goal_type.replace('_', ' ')}

DIETARY RESTRICTIONS: {restrictions_str}

CALCULATED MACRO TARGETS (hit these exactly — within ±5% per day):
  - Calories:  {macro_targets.calories} kcal/day
  - Protein:   {macro_targets.protein_g}g/day  ({macro_targets.protein_ratio})
  - Carbs:     {macro_targets.carbs_g}g/day
  - Fat:       {macro_targets.fat_g}g/day
  - Fiber:     {macro_targets.fiber_g}g/day

INSTRUCTIONS:
- Create a 7-day meal plan (breakfast, lunch, dinner, snack for each day)
- Each day MUST hit the macro targets above within ±5%
- Strictly respect all dietary restrictions
- Include specific portion sizes (e.g. "150g chicken breast", "1 cup oats")
- Include micronutrient highlights and meal prep tips
- Return JSON with EXACTLY this structure (no other keys):
{{
  "summary": "brief explanation of approach and why these macros suit the goal",
  "daily_targets": {{"calories": {macro_targets.calories}, "protein_g": {macro_targets.protein_g}, "carbs_g": {macro_targets.carbs_g}, "fat_g": {macro_targets.fat_g}, "fiber_g": {macro_targets.fiber_g}}},
  "days": [
    {{
      "day": 1,
      "meals": [
        {{"meal": "breakfast", "foods": ["food + portion"], "calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}},
        {{"meal": "lunch", "foods": ["food + portion"], "calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}},
        {{"meal": "dinner", "foods": ["food + portion"], "calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}},
        {{"meal": "snack", "foods": ["food + portion"], "calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}}
      ],
      "day_totals": {{"calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0, "fiber_g": 0}}
    }}
  ],
  "micronutrient_highlights": ["highlight1", "highlight2"],
  "meal_prep_tips": ["tip1", "tip2"]
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
and health goal, create a single-week, high-quality, well-balanced workout program.

BODY METRICS:
{metrics_lines}

HEALTH GOAL: {goal_type.replace('_', ' ')}

INSTRUCTIONS:
- Design ONE week of workouts (5 training days + 2 rest days) — do NOT generate multiple weeks
- This is the user's weekly commitment; make it comprehensive and immediately actionable
- Specify sets, reps, rest periods for each exercise
- Tailor exercise selection to body composition data (e.g. if high body fat, include cardio emphasis)
- REQUIRED: All of the following muscle groups MUST be trained with a minimum of 3 sets per group:
  chest, upper back, lower back, front deltoids, side deltoids, rear deltoids,
  biceps, triceps, quadriceps, hamstrings, glutes, calves, core/abs
- REQUIRED: Include compound movements: squat (or leg press), deadlift (or Romanian deadlift), bench press (or push-up variation), row (barbell or cable), overhead press
- REQUIRED: Include both push movements AND pull movements
- REQUIRED: Include at least 1 dedicated cardio or conditioning session
- REQUIRED: Distribute volume so no muscle group is undertrained — rear deltoids, calves, and lower back must each receive dedicated exercises, not just indirect work
- REQUIRED: Achieve a quality score of 90 or higher across all muscle group coverage, volume, balance, cardio, and frequency dimensions
- Return JSON with this structure:
{{
  "plan_explanation": "2-4 sentences explaining WHY these specific exercises were chosen based on the user's body composition data above. Reference specific metrics (e.g. body fat %, lean mass). Identify which muscle groups need the most work and which are already strong.",
  "summary": "brief explanation of program approach (1 sentence)",
  "days": [
    {{
      "day": 1,
      "focus": "e.g. Upper Body Strength",
      "is_rest": false,
      "exercises": [
        {{"name": "exercise", "sets": 3, "reps": "8-12", "rest_seconds": 90, "notes": "..."}}
      ],
      "estimated_duration_minutes": 60
    }}
  ],
  "progression_notes": "how to progress in subsequent weeks using this template"
}}

Return ONLY the JSON, no markdown, no explanation outside the JSON.
"""
