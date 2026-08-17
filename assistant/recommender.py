"""
recommender.py - Coach Spark Training Recommendations

Loads learning_paths.json and recommends the next three training
courses for an employee, based on their role and, when their role
has no dedicated path, the section of the question they just asked.

Courses the employee has already completed are excluded, so the
"Recommended Next Training" chips match what the chat answer already
says in words -- previously these two surfaces could disagree, since
the chips were generated from the raw role list with no awareness of
completed_training.
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "learning_paths.json"

# Used only when neither the employee's role nor the question
# section has a matching learning path.
DEFAULT_PATH = [
    "Factory Induction",
    "PPE Guidelines",
    "General Workplace Safety",
]


def get_recommendations(profile: dict, section: str = "General") -> list:
    """
    Return up to three recommended courses for this employee, excluding
    anything already in their completed_training.
    """
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as file:
            learning_paths = json.load(file)
    except Exception as error:
        print(f"Could not load learning paths: {error}")
        return []

    role = profile.get("role", "")
    completed = set(profile.get("completed_training", []))

    candidates = learning_paths.get(role)
    if not candidates:
        candidates = learning_paths.get(section)
    if not candidates:
        candidates = learning_paths.get("default", DEFAULT_PATH)

    # Filter out completed courses, preserving original order, then cap
    # at 3. Deliberately NOT topped up with unrelated default courses
    # when fewer than 3 remain (e.g. an employee close to finishing
    # their path) -- padding with an unrelated course would just
    # recreate the same text/chip mismatch this fix is meant to remove,
    # since the chat answer has no reason to mention a padded-in course.
    recommendations = [course for course in candidates if course not in completed]
    return recommendations[:3]