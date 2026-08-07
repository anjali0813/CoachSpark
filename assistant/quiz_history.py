"""
quiz_history.py - Coach Spark Quiz History

Persists each employee's quiz attempts to disk so training progress
survives across sessions and server restarts. Pure JSON, no database --
same pattern as personalize.py and recommender.py.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "quiz_history.json"

MAX_ATTEMPTS_PER_EMPLOYEE = 50   # keep the file from growing unbounded
WEAK_SECTION_THRESHOLD = 0.6     # below 60% average -> flagged for review


def _load_history() -> dict:
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _save_history(history: dict) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=2)


def record_quiz_result(employee_id: str, section: str, score: int, total: int) -> None:
    """Append one completed quiz attempt to the employee's history."""
    if not employee_id or total <= 0:
        return

    history = _load_history()
    attempts = history.setdefault(employee_id, [])

    attempts.append({
        "section": section or "General",
        "score": score,
        "total": total,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })

    # Trim from the oldest end so the file doesn't grow forever.
    history[employee_id] = attempts[-MAX_ATTEMPTS_PER_EMPLOYEE:]
    _save_history(history)


def get_quiz_history(employee_id: str) -> list:
    """Return all past attempts for an employee, most recent first."""
    history = _load_history()
    attempts = history.get(employee_id, [])
    return list(reversed(attempts))


def get_weak_sections(employee_id: str, threshold: float = WEAK_SECTION_THRESHOLD) -> list:
    """
    Return section names where this employee's average score across all
    attempts is below `threshold`. Useful for nudging recommendations
    toward topics that actually need review, not just their role default.
    """
    attempts = get_quiz_history(employee_id)
    if not attempts:
        return []

    totals_by_section = {}
    for attempt in attempts:
        section = attempt["section"]
        bucket = totals_by_section.setdefault(section, {"score": 0, "total": 0})
        bucket["score"] += attempt["score"]
        bucket["total"] += attempt["total"]

    return [
        section for section, bucket in totals_by_section.items()
        if bucket["total"] > 0 and (bucket["score"] / bucket["total"]) < threshold
    ]