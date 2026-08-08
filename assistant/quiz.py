"""
quiz.py - Coach Spark Interactive Quiz Generator

Turns retrieved manual context into a short multiple-choice quiz.
Deliberately does not import rag.py directly -- the caller (views.py
or app.py) retrieves the context first, so this module stays a pure
"context in, questions out" function usable from either frontend.
"""
import json
import re

MIN_QUESTIONS = 3
MAX_QUESTIONS = 5
DEFAULT_QUESTIONS = 4

QUIZ_SYSTEM_PROMPT = """You are Coach Spark's quiz generator for manufacturing training.

Create multiple-choice quiz questions using ONLY the manual context provided.
Never invent facts, numbers, or procedures that are not in the context.

Return ONLY valid JSON -- no markdown, no code fences, no commentary.

Format exactly as a JSON array:
[
  {
    "question": "...",
    "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
    "correct": "A",
    "explanation": "One short sentence, grounded in the manual context."
  }
]

Rules:
- Exactly one correct option per question.
- Keep questions short, practical, and worker-friendly.
- Keep each option under 12 words.
- Do not repeat the same question twice.
- Do not number the questions inside the "question" text."""


def _extract_json(raw_text: str) -> str:
    """Strip markdown code fences in case the model added them anyway."""
    text = raw_text.strip()
    text = re.sub(r"^```(json)?", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


def _validate_questions(questions: list) -> list:
    """Keep only well-formed questions with exactly 4 options and a valid answer."""
    valid = []
    for item in questions:
        try:
            options = item["options"]
            correct = item.get("correct", "").strip().upper()
            has_all_options = all(letter in options for letter in ("A", "B", "C", "D"))

            if isinstance(item.get("question"), str) and has_all_options and correct in "ABCD":
                valid.append({
                    "question": item["question"].strip(),
                    "options": {k: str(options[k]).strip() for k in ("A", "B", "C", "D")},
                    "correct": correct,
                    "explanation": str(item.get("explanation", "")).strip(),
                })
        except (KeyError, TypeError, AttributeError):
            continue
    return valid


def generate_quiz(client, model_name: str, context: str, num_questions: int = DEFAULT_QUESTIONS) -> list:
    """
    Generate a validated list of quiz questions grounded in `context`.

    Returns an empty list if generation or validation fails -- the
    caller should treat that as "try again" rather than show a broken quiz.
    """
    num_questions = max(MIN_QUESTIONS, min(MAX_QUESTIONS, num_questions))

    user_prompt = f"""Manual Context
{context}

Generate exactly {num_questions} multiple-choice questions testing understanding
of this content."""

    try:
        completion = client.chat.completions.create(
            model=model_name,
            temperature=0.4,
            messages=[
                {"role": "system", "content": QUIZ_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        raw = completion.choices[0].message.content
        parsed = json.loads(_extract_json(raw))
        questions = _validate_questions(parsed)[:num_questions]
    except Exception as error:
        print(f"Quiz generation failed: {error}")
        questions = []

    return questions


# ==========================================================
# Adaptive single-question generation
# ==========================================================
# Generates ONE question at a time, at a requested difficulty, so the
# caller (app.py) can raise or lower difficulty after every answer --
# turning the quiz into a genuinely adaptive practice loop instead of
# a fixed batch of questions handed out upfront at one difficulty.

DIFFICULTY_LEVELS = ["easy", "medium", "hard"]

QUESTION_SYSTEM_PROMPT = """You are Coach Spark's adaptive quiz generator for manufacturing training.

Create ONE multiple-choice quiz question using ONLY the manual context provided.
Never invent facts, numbers, or procedures that are not in the context.

Return ONLY valid JSON -- no markdown, no code fences, no commentary.

Format exactly as a JSON object:
{
  "question": "...",
  "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
  "correct": "A",
  "explanation": "One short sentence, grounded in the manual context.",
  "focus_area": "A short 2-4 word topic label for what this question tests, e.g. 'Lockout/Tagout' or 'PPE requirements'."
}

Difficulty guide:
- easy: tests a single directly-stated fact or step, worded plainly.
- medium: tests understanding of a step's purpose or order, or connects two related facts.
- hard: tests a subtle detail, an edge case, or a "what should you do if..." scenario, strictly grounded in the context.

Rules:
- Exactly one correct option per question.
- Keep the question short, practical, and worker-friendly.
- Keep each option under 12 words.
- Do not number the question inside the "question" text."""


def _validate_single_question(item: dict):
    """Same validation as _validate_questions, for one question object."""
    try:
        options = item["options"]
        correct = item.get("correct", "").strip().upper()
        has_all_options = all(letter in options for letter in ("A", "B", "C", "D"))

        if isinstance(item.get("question"), str) and has_all_options and correct in "ABCD":
            return {
                "question": item["question"].strip(),
                "options": {k: str(options[k]).strip() for k in ("A", "B", "C", "D")},
                "correct": correct,
                "explanation": str(item.get("explanation", "")).strip(),
                "focus_area": str(item.get("focus_area", "")).strip(),
            }
    except (KeyError, TypeError, AttributeError):
        pass
    return None


def generate_question(client, model_name: str, context: str, difficulty: str = "medium",
                       exclude_questions=None):
    """
    Generate ONE validated quiz question at the given difficulty, grounded
    in `context`. `exclude_questions` is a list of question strings already
    asked this session, so the model doesn't repeat itself as difficulty
    moves up or down. Returns None if generation/validation fails -- the
    caller should treat that as "stop the quiz here" rather than show a
    broken question.
    """
    difficulty = difficulty if difficulty in DIFFICULTY_LEVELS else "medium"
    exclude_questions = exclude_questions or []

    avoid_block = ""
    if exclude_questions:
        avoid_list = "\n".join(f"- {q}" for q in exclude_questions)
        avoid_block = (
            f"\n\nDo NOT repeat or closely rephrase any of these "
            f"already-asked questions:\n{avoid_list}"
        )

    user_prompt = f"""Manual Context
{context}

Generate exactly ONE {difficulty}-difficulty multiple-choice question testing
understanding of this content.{avoid_block}"""

    try:
        completion = client.chat.completions.create(
            model=model_name,
            temperature=0.5,
            messages=[
                {"role": "system", "content": QUESTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        raw = completion.choices[0].message.content
        parsed = json.loads(_extract_json(raw))
        return _validate_single_question(parsed)
    except Exception as error:
        print(f"Adaptive question generation failed: {error}")
        return None