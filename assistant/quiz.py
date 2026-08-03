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