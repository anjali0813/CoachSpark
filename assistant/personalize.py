"""
personalize.py - Coach Spark Employee Profiles

Loads employee_profiles.json and returns the profile for a given
employee ID. Pure JSON, no database.
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "employee_profiles.json"


def get_user_profile(user_id: str) -> dict:
    """
    Return the employee profile for the given user ID,
    or an empty dict if the employee is not found.
    """
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as file:
            profiles = json.load(file)
        return profiles.get(user_id, {})
    except Exception as error:
        print(f"Could not load employee profiles: {error}")
        return {}