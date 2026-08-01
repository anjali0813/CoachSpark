"""
recommender.py - Coach Spark Training Recommendations

Loads learning_paths.json and recommends the next three training
courses for an employee, based on their role and, when their role
has no dedicated path, the section of the question they just asked.
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
    Return up to three recommended courses for this employee.
    """
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as file:
            learning_paths = json.load(file)
    except Exception as error:
        print(f"Could not load learning paths: {error}")
        return []

    role = profile.get("role", "")

    recommendations = learning_paths.get(role)

    if not recommendations:
        recommendations = learning_paths.get(section)

    if not recommendations:
        recommendations = learning_paths.get("default", DEFAULT_PATH)

    return recommendations[:3]