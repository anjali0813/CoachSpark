import json
import os

# Path to the data folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "employee_profiles.json")


def get_user_profile(user_id):
    """
    Return the employee profile for the given user ID.
    """

    try:
        with open(DATA_PATH, "r", encoding="utf-8") as file:
            profiles = json.load(file)

        return profiles.get(user_id, {})

    except Exception:
        return {}