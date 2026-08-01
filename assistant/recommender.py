import json
import os

# Path to learning paths data
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "learning_paths.json")


def get_recommendations(profile, section):
    """
    Return recommended training based on the employee role
    and the detected knowledge section.
    """

    try:
        with open(DATA_PATH, "r", encoding="utf-8") as file:
            learning_paths = json.load(file)
    except Exception:
        return []

    role = profile.get("role", "").lower()

    recommendations = learning_paths.get(role, [])

    if not recommendations:
        recommendations = learning_paths.get("default", [])

    return recommendations[:3]