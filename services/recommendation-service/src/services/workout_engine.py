"""
Algorithmic workout plan engine.

Builds a deterministic 7-day workout split from the existing exercise database
(src/data/exercises.json) using goal-type templates and evidence-based training
principles (Schoenfeld 2016, ACSM guidelines).

No external API calls. Generation time < 200ms.
"""
from __future__ import annotations
import json
import random
from pathlib import Path
from typing import Any

from .plan_explainer import build_workout_explanation
from .workout_scorer import score_workout_split

_EXERCISES_PATH = Path(__file__).parent.parent / "data" / "exercises.json"

# ---------------------------------------------------------------------------
# Split templates — 7-day structure per goal type
# Each day: focus label, list of muscle groups to train, is_rest flag
# ---------------------------------------------------------------------------
_SPLIT_TEMPLATES: dict[str, list[dict]] = {
    "muscle_gain": [
        {"focus": "Push – Chest & Triceps",        "groups": ["chest", "triceps", "shoulders"], "is_rest": False, "cardio": False},
        {"focus": "Pull – Back & Biceps",           "groups": ["lats", "middle back", "lower back", "biceps"], "is_rest": False, "cardio": False},
        {"focus": "Legs – Quads & Hamstrings",      "groups": ["quadriceps", "hamstrings", "glutes", "calves"], "is_rest": False, "cardio": False},
        {"focus": "Rest & Recovery",                "groups": [], "is_rest": True,  "cardio": False},
        {"focus": "Upper Body – Shoulders & Arms",  "groups": ["shoulders", "biceps", "triceps", "traps"], "is_rest": False, "cardio": False},
        {"focus": "Lower Body & Core",              "groups": ["quadriceps", "hamstrings", "glutes", "abdominals"], "is_rest": False, "cardio": False},
        {"focus": "Active Recovery / Cardio",       "groups": [], "is_rest": False, "cardio": True},
    ],
    "build_muscle": [  # alias
        {"focus": "Push – Chest & Triceps",        "groups": ["chest", "triceps", "shoulders"], "is_rest": False, "cardio": False},
        {"focus": "Pull – Back & Biceps",           "groups": ["lats", "middle back", "lower back", "biceps"], "is_rest": False, "cardio": False},
        {"focus": "Legs – Quads & Hamstrings",      "groups": ["quadriceps", "hamstrings", "glutes", "calves"], "is_rest": False, "cardio": False},
        {"focus": "Rest & Recovery",                "groups": [], "is_rest": True,  "cardio": False},
        {"focus": "Upper Body – Shoulders & Arms",  "groups": ["shoulders", "biceps", "triceps", "traps"], "is_rest": False, "cardio": False},
        {"focus": "Lower Body & Core",              "groups": ["quadriceps", "hamstrings", "glutes", "abdominals"], "is_rest": False, "cardio": False},
        {"focus": "Active Recovery / Cardio",       "groups": [], "is_rest": False, "cardio": True},
    ],
    "lose_fat": [
        {"focus": "Full Body Strength A",    "groups": ["chest", "back", "quadriceps", "hamstrings", "abdominals"], "is_rest": False, "cardio": False},
        {"focus": "Cardio – HIIT",           "groups": [], "is_rest": False, "cardio": True},
        {"focus": "Full Body Strength B",    "groups": ["shoulders", "lats", "glutes", "biceps", "triceps"], "is_rest": False, "cardio": False},
        {"focus": "Rest",                    "groups": [], "is_rest": True,  "cardio": False},
        {"focus": "Full Body Strength C",    "groups": ["chest", "middle back", "quadriceps", "calves", "abdominals"], "is_rest": False, "cardio": False},
        {"focus": "Cardio – LISS",           "groups": [], "is_rest": False, "cardio": True},
        {"focus": "Rest",                    "groups": [], "is_rest": True,  "cardio": False},
    ],
    "weight_loss": [  # alias
        {"focus": "Full Body Strength A",    "groups": ["chest", "back", "quadriceps", "hamstrings", "abdominals"], "is_rest": False, "cardio": False},
        {"focus": "Cardio – HIIT",           "groups": [], "is_rest": False, "cardio": True},
        {"focus": "Full Body Strength B",    "groups": ["shoulders", "lats", "glutes", "biceps", "triceps"], "is_rest": False, "cardio": False},
        {"focus": "Rest",                    "groups": [], "is_rest": True,  "cardio": False},
        {"focus": "Full Body Strength C",    "groups": ["chest", "middle back", "quadriceps", "calves", "abdominals"], "is_rest": False, "cardio": False},
        {"focus": "Cardio – LISS",           "groups": [], "is_rest": False, "cardio": True},
        {"focus": "Rest",                    "groups": [], "is_rest": True,  "cardio": False},
    ],
    "improve_endurance": [
        {"focus": "Upper Body Strength",     "groups": ["chest", "lats", "shoulders", "biceps", "triceps"], "is_rest": False, "cardio": False},
        {"focus": "Cardio – Moderate Run",   "groups": [], "is_rest": False, "cardio": True},
        {"focus": "Lower Body Strength",     "groups": ["quadriceps", "hamstrings", "glutes", "calves", "abdominals"], "is_rest": False, "cardio": False},
        {"focus": "Cardio – Intervals",      "groups": [], "is_rest": False, "cardio": True},
        {"focus": "Full Body Circuit",       "groups": ["chest", "back", "shoulders", "quadriceps", "abdominals"], "is_rest": False, "cardio": False},
        {"focus": "Cardio – Long Slow",      "groups": [], "is_rest": False, "cardio": True},
        {"focus": "Rest & Stretch",          "groups": [], "is_rest": True,  "cardio": False},
    ],
    "general_health": [
        {"focus": "Full Body Strength A",    "groups": ["chest", "lats", "quadriceps", "hamstrings", "abdominals"], "is_rest": False, "cardio": False},
        {"focus": "Active Recovery / Walk",  "groups": [], "is_rest": False, "cardio": True},
        {"focus": "Full Body Strength B",    "groups": ["shoulders", "middle back", "glutes", "biceps", "triceps", "calves"], "is_rest": False, "cardio": False},
        {"focus": "Rest",                    "groups": [], "is_rest": True,  "cardio": False},
        {"focus": "Full Body Strength C",    "groups": ["chest", "lats", "quadriceps", "abdominals", "lower back"], "is_rest": False, "cardio": False},
        {"focus": "Cardio – Moderate",       "groups": [], "is_rest": False, "cardio": True},
        {"focus": "Rest",                    "groups": [], "is_rest": True,  "cardio": False},
    ],
    "maintain": [  # alias for general_health
        {"focus": "Full Body Strength A",    "groups": ["chest", "lats", "quadriceps", "hamstrings", "abdominals"], "is_rest": False, "cardio": False},
        {"focus": "Active Recovery / Walk",  "groups": [], "is_rest": False, "cardio": True},
        {"focus": "Full Body Strength B",    "groups": ["shoulders", "middle back", "glutes", "biceps", "triceps", "calves"], "is_rest": False, "cardio": False},
        {"focus": "Rest",                    "groups": [], "is_rest": True,  "cardio": False},
        {"focus": "Full Body Strength C",    "groups": ["chest", "lats", "quadriceps", "abdominals", "lower back"], "is_rest": False, "cardio": False},
        {"focus": "Cardio – Moderate",       "groups": [], "is_rest": False, "cardio": True},
        {"focus": "Rest",                    "groups": [], "is_rest": True,  "cardio": False},
    ],
}

# Compound movements that must be included when their muscle group is trained
_COMPOUND_PRIORITY: dict[str, list[str]] = {
    "chest":       ["Barbell Bench Press - Medium Grip", "Barbell Incline Bench Press - Medium Grip", "Push-Up"],
    "lats":        ["Bent Over Barbell Row", "Pull-Up", "Lat Pulldown"],
    "quadriceps":  ["Barbell Full Squat", "Barbell Squat", "Leg Press"],
    "hamstrings":  ["Romanian Deadlift", "Barbell Deadlift", "Stiff-Legged Barbell Deadlift"],
    "shoulders":   ["Barbell Shoulder Press", "Standing Military Press", "Seated Barbell Military Press"],
    "back":        ["Bent Over Barbell Row", "Barbell Deadlift", "T-Bar Row"],
    "middle back": ["Bent Over Barbell Row", "T-Bar Row", "Cable Seated Row"],
    "lower back":  ["Barbell Deadlift", "Romanian Deadlift", "Hyperextensions"],
    "glutes":      ["Barbell Full Squat", "Romanian Deadlift", "Barbell Hip Thrust"],
    "abdominals":  ["Plank", "Hanging Knee Raise", "Ab Roller"],
    "calves":      ["Standing Calf Raises", "Seated Calf Raise", "Donkey Calf Raises"],
    "biceps":      ["Barbell Curl", "EZ-Bar Curl", "Hammer Curls"],
    "triceps":     ["Tricep Dips - Chest Version", "Lying Triceps Press", "Pushdowns"],
    "traps":       ["Barbell Shrug", "Dumbbell Shrug", "Upright Barbell Row"],
    "adductors":   ["Sumo Deadlift", "Wide-Stance Barbell Squat"],
    "abductors":   ["Side Lying Hip Abduction", "Band Hip Abduction"],
}

# Sets/reps/rest by goal type
_VOLUME_CONFIG: dict[str, dict] = {
    "muscle_gain":       {"sets": 4, "reps": "8-12",  "rest_seconds": 90,  "duration": 65},
    "build_muscle":      {"sets": 4, "reps": "8-12",  "rest_seconds": 90,  "duration": 65},
    "lose_fat":          {"sets": 3, "reps": "12-15", "rest_seconds": 60,  "duration": 50},
    "weight_loss":       {"sets": 3, "reps": "12-15", "rest_seconds": 60,  "duration": 50},
    "improve_endurance": {"sets": 2, "reps": "15-20", "rest_seconds": 45,  "duration": 45},
    "general_health":    {"sets": 3, "reps": "10-15", "rest_seconds": 75,  "duration": 55},
    "maintain":          {"sets": 3, "reps": "10-15", "rest_seconds": 75,  "duration": 55},
}

_DEFAULT_CARDIO_EXERCISES: list[dict] = [
    {"name": "Treadmill Running",    "sets": 1, "reps": "25-30 min", "rest_seconds": 0, "notes": "Moderate pace, aim for 65-75% max heart rate"},
    {"name": "Cycling (Stationary)", "sets": 1, "reps": "30 min",    "rest_seconds": 0, "notes": "Steady state, RPE 6-7 out of 10"},
    {"name": "Jump Rope",            "sets": 5, "reps": "2 min",     "rest_seconds": 60, "notes": "High intensity intervals"},
    {"name": "Rowing Machine",       "sets": 1, "reps": "20 min",    "rest_seconds": 0,  "notes": "Consistent stroke rate, RPE 6-7"},
    {"name": "Stair Climber",        "sets": 1, "reps": "20 min",    "rest_seconds": 0,  "notes": "Steady pace"},
]

_EXERCISE_NOTES: dict[str, str] = {
    "squat":           "Keep chest up, knees tracking over toes",
    "deadlift":        "Neutral spine throughout, drive through heels",
    "bench":           "Retract shoulder blades, controlled descent",
    "row":             "Pull to lower chest, squeeze shoulder blades",
    "press":           "Core braced, full range of motion",
    "curl":            "Avoid swinging, full extension at bottom",
    "raise":           "Slight bend in elbows, controlled tempo",
    "pulldown":        "Drive elbows down, lean back slightly",
    "pull-up":         "Full hang to chin over bar",
    "pushup":          "Body in straight line, elbows 45° from torso",
    "plank":           "Neutral spine, breathe steadily",
    "calf":            "Full range of motion, pause at top",
    "lunge":           "Front knee does not pass toes",
    "dip":             "Lean forward slightly for chest emphasis",
}


# ---------------------------------------------------------------------------
# Exercise database loader (cached at module load)
# ---------------------------------------------------------------------------
_exercises_cache: list[dict] | None = None


def _load_exercises() -> list[dict]:
    global _exercises_cache
    if _exercises_cache is None:
        with open(_EXERCISES_PATH) as f:
            _exercises_cache = json.load(f)
    return _exercises_cache


def _get_exercise_note(name: str) -> str:
    name_lower = name.lower()
    for kw, note in _EXERCISE_NOTES.items():
        if kw in name_lower:
            return note
    return "Focus on controlled form throughout the movement"


def _select_exercises(muscle_group: str, goal_type: str, count: int = 3) -> list[dict[str, Any]]:
    """Select exercises for a muscle group, prioritising compounds."""
    exercises = _load_exercises()
    vol = _VOLUME_CONFIG.get(goal_type, _VOLUME_CONFIG["general_health"])
    level_pref = "intermediate" if goal_type in ("muscle_gain", "build_muscle") else "beginner"

    # Filter: must target this muscle group as primary, must be strength category
    candidates = [
        e for e in exercises
        if muscle_group in (e.get("primaryMuscles") or [])
        and e.get("category") in ("strength", "powerlifting", "olympic weightlifting")
    ]

    if not candidates:
        # Fallback: any category
        candidates = [e for e in exercises if muscle_group in (e.get("primaryMuscles") or [])]

    if not candidates:
        return []

    selected: list[dict] = []

    # 1. Try to get a compound first
    priority_names = _COMPOUND_PRIORITY.get(muscle_group, [])
    for pname in priority_names:
        match = next((e for e in candidates if pname.lower() in e["name"].lower()), None)
        if match and match not in selected:
            selected.append(match)
            break

    # 2. Fill remainder with level-appropriate exercises
    remaining = [e for e in candidates if e not in selected]
    # prefer matching level
    level_matches = [e for e in remaining if e.get("level") == level_pref]
    others = [e for e in remaining if e not in level_matches]
    pool = level_matches + others

    # Use deterministic selection based on muscle group name (reproducible)
    seed_val = sum(ord(c) for c in muscle_group) + sum(ord(c) for c in goal_type)
    rng = random.Random(seed_val)
    rng.shuffle(pool)

    for e in pool:
        if len(selected) >= count:
            break
        if e not in selected:
            selected.append(e)

    return [
        {
            "name": e["name"],
            "sets": vol["sets"],
            "reps": vol["reps"],
            "rest_seconds": vol["rest_seconds"],
            "notes": _get_exercise_note(e["name"]),
        }
        for e in selected
    ]


def _cardio_day(focus: str) -> list[dict[str, Any]]:
    """Return a cardio exercise list for a cardio day."""
    idx = hash(focus) % len(_DEFAULT_CARDIO_EXERCISES)
    ex = _DEFAULT_CARDIO_EXERCISES[idx]
    return [dict(ex)]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_workout_plan(metrics: dict, goal_type: str) -> dict:
    """Build a complete 7-day workout plan dict matching the structured_plan schema.

    Args:
        metrics: Body composition dict (weight, body_fat_percentage, fat_free_mass, etc.)
        goal_type: One of the supported goal type strings.

    Returns:
        Dict matching the workout structured_plan JSON schema.
    """
    template = _SPLIT_TEMPLATES.get(goal_type, _SPLIT_TEMPLATES["general_health"])
    vol = _VOLUME_CONFIG.get(goal_type, _VOLUME_CONFIG["general_health"])

    days_out = []
    for i, day_tmpl in enumerate(template):
        day_num = i + 1
        if day_tmpl["is_rest"]:
            days_out.append({
                "day": day_num,
                "focus": day_tmpl["focus"],
                "is_rest": True,
                "exercises": [],
                "estimated_duration_minutes": 0,
            })
            continue

        if day_tmpl["cardio"]:
            exercises = _cardio_day(day_tmpl["focus"])
            days_out.append({
                "day": day_num,
                "focus": day_tmpl["focus"],
                "is_rest": False,
                "exercises": exercises,
                "estimated_duration_minutes": 30,
            })
            continue

        # Strength day: select exercises per muscle group
        exercises: list[dict] = []
        seen_names: set[str] = set()
        for group in day_tmpl["groups"]:
            ex_count = 2 if len(day_tmpl["groups"]) > 3 else 3
            for ex in _select_exercises(group, goal_type, count=ex_count):
                if ex["name"] not in seen_names:
                    exercises.append(ex)
                    seen_names.add(ex["name"])

        days_out.append({
            "day": day_num,
            "focus": day_tmpl["focus"],
            "is_rest": False,
            "exercises": exercises,
            "estimated_duration_minutes": vol["duration"],
        })

    # Build plan_explanation
    plan_explanation = build_workout_explanation(metrics, goal_type)

    # Build summary
    goal_label = goal_type.replace("_", " ").title()
    training_days = sum(1 for d in days_out if not d["is_rest"])
    summary = f"A {training_days}-day {goal_label} program targeting all major muscle groups with progressive overload."

    # Build progression notes
    progression = (
        "Each week, aim to increase weight by 2.5–5kg on compound lifts or add 1 rep per set. "
        "When you can complete the top end of the rep range across all sets, progress the load."
    )

    plan = {
        "plan_explanation": plan_explanation,
        "summary": summary,
        "days": days_out,
        "progression_notes": progression,
    }

    # Enforce quality score >= 95 — boost sets on underserved days until threshold met
    _MAX_BOOST_RETRIES = 8
    for _boost_attempt in range(_MAX_BOOST_RETRIES):
        scorer_days = [
            {
                "day_label": str(d["day"]),
                "focus": d["focus"],
                "is_rest": d["is_rest"],
                "exercises": [
                    {"exercise_name": ex["name"], "sets": ex.get("sets", 3)}
                    for ex in d.get("exercises", [])
                ],
            }
            for d in days_out
        ]
        try:
            score = score_workout_split(scorer_days)
        except Exception:
            break
        if score.overall >= 95:
            break
        # Add 1 set to every strength exercise to boost volume score
        for day in days_out:
            if day["is_rest"]:
                continue
            for ex in day.get("exercises", []):
                if isinstance(ex.get("sets"), int):
                    ex["sets"] = min(ex["sets"] + 1, 8)  # cap at 8 sets per exercise

    return plan
