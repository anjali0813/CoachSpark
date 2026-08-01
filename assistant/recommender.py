import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

LEARNING_PATH = os.path.join(
    BASE_DIR,
    "data",
    "learning_paths.json"
)


# def recommend_next_training(profile):
#     try:
#         with open(LEARNING_PATH, "r", encoding="utf-8") as file:
#             learning_paths = json.load(file)

#         role = profile["role"]
#         completed = set(profile["completed_training"])

#         all_courses = learning_paths.get(role, [])

#         recommendations = [
#             course for course in all_courses
#             if course not in completed
#         ]

#         return recommendations[:3]

#     except Exception:
#         return []


"""
recommender.py
Simple role-based training recommender for Coach Spark.
"""

ROLE_RECOMMENDATIONS = {
    "machine technician": [
        "PLC Basics",
        "Electrical Safety",
        "Machine Maintenance",
        "Industrial Automation"
    ],
    "quality inspector": [
        "Advanced Quality Control",
        "Root Cause Analysis",
        "Six Sigma Basics",
        "Measurement System Analysis"
    ],
    "forklift operator": [
        "Warehouse Safety",
        "Material Handling",
        "Fire Safety",
        "Defensive Forklift Driving"
    ],
    "new employee": [
        "PPE Guidelines",
        "5S Workplace Organization",
        "Factory Safety",
        "Emergency Procedures"
    ]
}


def recommend_next_training(profile, limit=3):
    """
    Recommend the next training courses based on an employee profile.

    Parameters
    ----------
    profile : dict
        Employee profile from personalize.py
    limit : int
        Maximum number of recommendations.

    Returns
    -------
    list
        Recommended courses not yet completed.
    """
    role = profile.get("role", "").lower()
    completed = {
        course.strip().lower()
        for course in profile.get("completed_training", [])
    }

    available = ROLE_RECOMMENDATIONS.get(
        role,
        ["General Workplace Safety", "Communication Skills"]
    )

    recommendations = [
        course for course in available
        if course.lower() not in completed
    ]

    return recommendations[:limit]