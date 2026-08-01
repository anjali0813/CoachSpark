import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "employee_profiles.json")


def get_employee_profile(employee_id):
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as file:
            profiles = json.load(file)

        return profiles.get(employee_id)

    except Exception:
        return None


# def get_employee_profile(employee_id):
#     """
#     Return an employee profile.
#     Falls back to E001 if the ID is unknown.
#     """
#     return EMPLOYEES.get(employee_id, EMPLOYEES["E001"])


# def get_all_employees():
#     """Return all employee profiles."""
#     return EMPLOYEES