"""
Workout split quality scorer.

Evaluates a user's workout split across 5 independent dimensions:
  1. Muscle group coverage  — which of 7 major groups are trained
  2. Volume adequacy        — weekly sets per muscle group vs evidence-based minimums
  3. Push/pull balance      — ratio of anterior-to-posterior work
  4. Cardio inclusion       — aerobic capacity and fat-loss support
  5. Structural balance     — frequency distribution across the week

Returns an overall score 0-100 and per-dimension subscores with actionable feedback.

References (all publicly available):
  - Schoenfeld et al. (2016): minimum effective volume ~10 sets/muscle/week
  - Krieger (2010): dose-response for strength, 2-4 sessions/muscle/week optimal
  - ACSM Position Stand (2009): 150 min/week moderate cardio for health
"""
from __future__ import annotations
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Muscle-group keyword lookup
# ---------------------------------------------------------------------------
# Maps exercise name keywords → muscle group(s) they primarily train.
# Deliberately based on well-known exercise science categorisations.

_MUSCLE_KEYWORDS: dict[str, list[str]] = {
    # CHEST
    "chest": ["chest"],
    "bench press": ["chest", "shoulders", "triceps"],
    "bench": ["chest", "shoulders", "triceps"],
    "push-up": ["chest", "shoulders", "triceps"],
    "pushup": ["chest", "shoulders", "triceps"],
    "dumbbell fly": ["chest"],
    "cable fly": ["chest"],
    "incline press": ["chest", "shoulders"],
    "decline press": ["chest"],
    "pec": ["chest"],
    # BACK
    "pull-up": ["back", "biceps"],
    "pullup": ["back", "biceps"],
    "chin-up": ["back", "biceps"],
    "chinup": ["back", "biceps"],
    "row": ["back", "biceps"],
    "deadlift": ["back", "glutes", "hamstrings"],
    "lat pulldown": ["back", "biceps"],
    "seated cable row": ["back", "biceps"],
    "t-bar": ["back"],
    "back": ["back"],
    "rhomboid": ["back"],
    "trap": ["back"],
    "shrug": ["back"],
    # SHOULDERS
    "overhead press": ["shoulders", "triceps"],
    "shoulder press": ["shoulders", "triceps"],
    "ohp": ["shoulders", "triceps"],
    "lateral raise": ["shoulders"],
    "front raise": ["shoulders"],
    "face pull": ["shoulders", "back"],
    "arnold press": ["shoulders"],
    "shoulder": ["shoulders"],
    "delt": ["shoulders"],
    # ARMS (biceps)
    "curl": ["biceps"],
    "bicep": ["biceps"],
    "hammer curl": ["biceps"],
    "preacher": ["biceps"],
    # ARMS (triceps)
    "tricep": ["triceps"],
    "skull crusher": ["triceps"],
    "skullcrusher": ["triceps"],
    "triceps pushdown": ["triceps"],
    "close grip": ["triceps", "chest"],
    "dip": ["triceps", "chest"],
    # LEGS
    "squat": ["quads", "glutes", "hamstrings"],
    "leg press": ["quads", "glutes"],
    "lunge": ["quads", "glutes", "hamstrings"],
    "leg extension": ["quads"],
    "quad": ["quads"],
    "leg curl": ["hamstrings"],
    "romanian deadlift": ["hamstrings", "glutes"],
    "rdl": ["hamstrings", "glutes"],
    "hamstring": ["hamstrings"],
    "calf raise": ["calves"],
    "calf": ["calves"],
    "glute": ["glutes"],
    "hip thrust": ["glutes", "hamstrings"],
    "step-up": ["quads", "glutes"],
    "leg": ["quads"],
    # CORE
    "plank": ["core"],
    "crunch": ["core"],
    "ab": ["core"],
    "sit-up": ["core"],
    "situp": ["core"],
    "russian twist": ["core"],
    "hanging leg raise": ["core"],
    "cable crunch": ["core"],
    "oblique": ["core"],
    "core": ["core"],
    # CARDIO
    "run": ["cardio"],
    "running": ["cardio"],
    "jog": ["cardio"],
    "treadmill": ["cardio"],
    "cycling": ["cardio"],
    "bike": ["cardio"],
    "row machine": ["cardio", "back"],
    "elliptical": ["cardio"],
    "hiit": ["cardio"],
    "jump rope": ["cardio", "calves"],
    "stair": ["cardio", "quads", "glutes"],
    "swim": ["cardio"],
    "sprint": ["cardio"],
    "cardio": ["cardio"],
}

# The 7 major groups we score coverage against (legs = quads+hamstrings+glutes)
_MAJOR_GROUPS = {"chest", "back", "shoulders", "arms", "legs", "core", "cardio"}

# Map detailed groups → major group
_GROUP_ROLLUP = {
    "chest": "chest",
    "back": "back",
    "shoulders": "shoulders",
    "biceps": "arms",
    "triceps": "arms",
    "quads": "legs",
    "hamstrings": "legs",
    "glutes": "legs",
    "calves": "legs",
    "core": "core",
    "cardio": "cardio",
}

# Evidence-based weekly-set minimums per major group (maintenance = 10, growth = 16)
_MIN_WEEKLY_SETS = {"chest": 10, "back": 10, "shoulders": 8, "arms": 8, "legs": 10, "core": 6, "cardio": 3}
_TARGET_WEEKLY_SETS = {"chest": 16, "back": 16, "shoulders": 12, "arms": 12, "legs": 16, "core": 10, "cardio": 5}


@dataclass
class WorkoutScore:
    overall: int                          # 0-100
    coverage_score: int                   # 0-25
    volume_score: int                     # 0-30
    balance_score: int                    # 0-20
    cardio_score: int                     # 0-15
    frequency_score: int                  # 0-10
    covered_groups: list[str]             # major groups hit
    missing_groups: list[str]             # major groups not hit
    weekly_sets_per_group: dict[str, int] # computed volume
    feedback: list[str]                   # actionable messages
    label: str                            # "Excellent" / "Good" / "Moderate" / "Needs Work"


def _extract_muscles(exercise_name: str) -> list[str]:
    """Return list of detailed muscle groups from an exercise name."""
    name_lower = exercise_name.lower()
    found: set[str] = set()
    for kw, muscles in _MUSCLE_KEYWORDS.items():
        if kw in name_lower:
            found.update(muscles)
    return list(found)


def _to_major(detailed: list[str]) -> list[str]:
    return list({_GROUP_ROLLUP.get(d, d) for d in detailed})


def score_workout_split(days: list[dict]) -> WorkoutScore:
    """
    Score a workout split.

    Args:
        days: list of day objects, each with:
              {
                "day_label": str,
                "focus": str | None,
                "is_rest": bool,
                "exercises": [{"exercise_name": str, "sets": int | None, ...}]
              }

    Returns: WorkoutScore dataclass
    """
    # Aggregate weekly sets per major group
    weekly_sets: dict[str, int] = {g: 0 for g in _MAJOR_GROUPS}
    training_days = 0

    for day in days:
        if day.get("is_rest"):
            continue
        training_days += 1
        exercises = day.get("exercises") or []
        for ex in exercises:
            name = ex.get("exercise_name", "")
            sets = int(ex.get("sets") or 3)
            muscles = _extract_muscles(name)
            majors = _to_major(muscles)
            for g in majors:
                if g in weekly_sets:
                    weekly_sets[g] += sets

    covered = [g for g, s in weekly_sets.items() if s > 0]
    missing = [g for g in _MAJOR_GROUPS if g not in covered]
    feedback: list[str] = []

    # --- Dimension 1: Coverage (25 pts) ---
    coverage_score = round(len(covered) / len(_MAJOR_GROUPS) * 25)
    if missing:
        feedback.append(f"Missing muscle groups: {', '.join(missing)}. Add exercises targeting them.")

    # --- Dimension 2: Volume adequacy (30 pts) ---
    volume_pts = 0
    for g in _MAJOR_GROUPS:
        s = weekly_sets.get(g, 0)
        target = _TARGET_WEEKLY_SETS[g]
        minimum = _MIN_WEEKLY_SETS[g]
        if s == 0:
            pts = 0
        elif s >= target:
            pts = 30 / len(_MAJOR_GROUPS)
        elif s >= minimum:
            pts = (s - minimum) / (target - minimum) * (30 / len(_MAJOR_GROUPS)) * 0.75 + (30 / len(_MAJOR_GROUPS)) * 0.25
        else:
            pts = (s / minimum) * (30 / len(_MAJOR_GROUPS)) * 0.25
        volume_pts += pts
        if 0 < s < minimum:
            feedback.append(f"{g.title()}: {s} sets/week — below the recommended minimum of {minimum}. Aim for {target}.")
    volume_score = round(volume_pts)

    # --- Dimension 3: Push/pull balance (20 pts) ---
    push_sets = weekly_sets.get("chest", 0) + weekly_sets.get("shoulders", 0) + weekly_sets.get("arms", 0) // 2
    pull_sets = weekly_sets.get("back", 0) + weekly_sets.get("arms", 0) // 2
    if push_sets + pull_sets == 0:
        balance_score = 0
        feedback.append("No push or pull exercises detected.")
    else:
        ratio = min(push_sets, pull_sets) / max(push_sets, pull_sets) if max(push_sets, pull_sets) > 0 else 0
        balance_score = round(ratio * 20)
        if ratio < 0.7:
            dominant = "push" if push_sets > pull_sets else "pull"
            weak = "pull" if dominant == "push" else "push"
            feedback.append(f"Push/pull imbalance detected (ratio {ratio:.2f}). Add more {weak} exercises to reduce injury risk.")

    # --- Dimension 4: Cardio (15 pts) ---
    cardio_sets = weekly_sets.get("cardio", 0)
    cardio_score = min(round(cardio_sets / _TARGET_WEEKLY_SETS["cardio"] * 15), 15)
    if cardio_sets == 0:
        feedback.append("No cardio detected. Adding 2-3 cardio sessions/week improves cardiovascular health and fat oxidation.")
    elif cardio_sets < _MIN_WEEKLY_SETS["cardio"]:
        feedback.append(f"Cardio volume is low ({cardio_sets} sessions). Aim for at least 3 sessions per week.")

    # --- Dimension 5: Training frequency distribution (10 pts) ---
    total_days = len(days) if days else 7
    rest_days = sum(1 for d in days if d.get("is_rest"))
    if total_days == 0:
        frequency_score = 0
    else:
        # Optimal: 4-5 training days with 2-3 rest days
        rest_ratio = rest_days / total_days
        if 0.25 <= rest_ratio <= 0.43:  # 2-3 rest out of 7
            frequency_score = 10
        elif rest_ratio < 0.25:
            frequency_score = 5
            feedback.append("Very few rest days detected. Recovery is essential — aim for 2-3 rest days per week.")
        else:
            frequency_score = 7
            feedback.append("High number of rest days. Increase training frequency to 4-5 days/week for better results.")

    overall = coverage_score + volume_score + balance_score + cardio_score + frequency_score

    if overall >= 80:
        label = "Excellent"
    elif overall >= 60:
        label = "Good"
    elif overall >= 40:
        label = "Moderate"
    else:
        label = "Needs Work"

    if not feedback:
        feedback.append("Great split! Maintain progressive overload by gradually increasing weights or volume each week.")

    return WorkoutScore(
        overall=overall,
        coverage_score=coverage_score,
        volume_score=volume_score,
        balance_score=balance_score,
        cardio_score=cardio_score,
        frequency_score=frequency_score,
        covered_groups=covered,
        missing_groups=missing,
        weekly_sets_per_group=weekly_sets,
        feedback=feedback,
        label=label,
    )
