# """
# views.py - Coach Spark Django Views

# Workflow for every chat request:
#     user question -> retrieve_context() -> get_user_profile()
#     -> get_recommendations() -> Groq -> JSON response
# """
# import os
# import json
# import traceback

# from dotenv import load_dotenv
# from django.shortcuts import render
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from groq import Groq

# from .rag import retrieve_context
# from .personalize import get_user_profile
# from .recommender import get_recommendations
# from .quiz import generate_quiz
# from .escalation import apply_escalation_guard

# load_dotenv()

# GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# if not GROQ_API_KEY:
#     raise ValueError("GROQ_API_KEY not found. Please set it in your .env file.")

# client = Groq(api_key=GROQ_API_KEY)

# MODEL_NAME = "llama-3.3-70b-versatile"

# SYSTEM_PROMPT = """You are Coach Spark, an AI Learning & Development Assistant
# for manufacturing employees.

# Answer ONLY using the retrieved manual context provided below.
# Never invent procedures, safety steps, or company policy -- including
# general safety knowledge that sounds reasonable (e.g. lockout/tagout,
# PPE requirements) if it does not literally appear in the context below.

# If the context only partially answers the question, state clearly and
# plainly what the manual does NOT cover, then tell the employee to
# contact their supervisor or the maintenance team for that specific gap.
# Do not suggest "referring to a different document" or guess at what
# that document might say -- just say the manual doesn't cover it and
# point to a supervisor.

# Use clear, worker-friendly language, personalized to the employee's role.
# Keep the answer under 150 words and use bullet points where useful."""

# NOT_FOUND_MESSAGE = "I couldn't find relevant information in the training manuals."

# QUIZ_SESSION_KEY = "coach_spark_quiz"
# QUIZ_NOT_FOUND_MESSAGE = (
#     "I don't have enough manual content on that topic to build a quiz. "
#     "Try a topic like safety, PPE, maintenance, or quality."
# )
# QUIZ_GENERATION_FAILED_MESSAGE = "I couldn't generate a quiz right now. Please try again."


# def index(request):
#     """Render the Coach Spark homepage."""
#     return render(request, "assistant/index.html")


# @csrf_exempt
# def chat_api(request):
#     """Handle a chat question and return an answer with sources."""
#     if request.method != "POST":
#         return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

#     try:
#         data = json.loads(request.body)
#         question = data.get("message", "").strip()
#         employee_id = data.get("employee_id", "")

#         if not question:
#             return JsonResponse({"error": "No message provided."}, status=400)

#         profile = get_user_profile(employee_id)
#         rag_result = retrieve_context(question)

#         context = rag_result["context"]
#         sources = rag_result["sources"]
#         score = rag_result["score"]
#         section = rag_result["section"]

#         if score == 0:
#             return JsonResponse({
#                 "response": NOT_FOUND_MESSAGE,
#                 "sources": [],
#                 "section": None,
#                 "recommendations": [],
#             })

#         recommendations = get_recommendations(profile, section)

#         employee_summary = (
#             f"Employee: {profile.get('name', 'Unknown')}\n"
#             f"Role: {profile.get('role', 'Unknown')}\n"
#             f"Department: {profile.get('department', 'Unknown')}"
#         ) if profile else "Employee: Unknown"

#         user_prompt = f"""Employee Profile
# {employee_summary}

# Training Manual Context
# {context}

# Question
# {question}"""

#         completion = client.chat.completions.create(
#             model=MODEL_NAME,
#             temperature=0.2,
#             messages=[
#                 {"role": "system", "content": SYSTEM_PROMPT},
#                 {"role": "user", "content": user_prompt},
#             ],
#         )

#         answer = completion.choices[0].message.content
#         answer = apply_escalation_guard(answer)

#         return JsonResponse({
#             "response": answer,
#             "sources": sources,
#             "section": section,
#             "recommendations": recommendations,
#         })

#     except Exception as error:
#         traceback.print_exc()
#         return JsonResponse({"error": str(error)}, status=500)


# # =====================================================
# # INTERACTIVE QUIZ
# # =====================================================
# # Questions and correct answers live server-side in the Django
# # session. Only the question text and options are ever sent to the
# # browser -- the answer key never leaves the server.

# def _public_question(question: dict, number: int, total: int) -> dict:
#     """Strip the correct answer / explanation before sending to the client."""
#     return {
#         "number": number,
#         "total": total,
#         "question": question["question"],
#         "options": question["options"],
#     }


# @csrf_exempt
# def quiz_start(request):
#     """Generate a quiz for a topic and store it in the session."""
#     if request.method != "POST":
#         return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

#     try:
#         data = json.loads(request.body)
#         topic = data.get("topic", "").strip()

#         if not topic:
#             return JsonResponse({"error": "Please tell me a topic to quiz you on."}, status=400)

#         rag_result = retrieve_context(topic)

#         if rag_result["score"] == 0:
#             return JsonResponse({"error": QUIZ_NOT_FOUND_MESSAGE}, status=404)

#         questions = generate_quiz(client, MODEL_NAME, rag_result["context"])

#         if not questions:
#             return JsonResponse({"error": QUIZ_GENERATION_FAILED_MESSAGE}, status=500)

#         request.session[QUIZ_SESSION_KEY] = {
#             "questions": questions,
#             "current": 0,
#             "score": 0,
#         }
#         request.session.modified = True

#         return JsonResponse({
#             "started": True,
#             "section": rag_result["section"],
#             "sources": rag_result["sources"],
#             "total": len(questions),
#             "question": _public_question(questions[0], 1, len(questions)),
#         })

#     except Exception as error:
#         traceback.print_exc()
#         return JsonResponse({"error": str(error)}, status=500)


# @csrf_exempt
# def quiz_answer(request):
#     """Grade the selected option, update the score, and return the next question."""
#     if request.method != "POST":
#         return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

#     try:
#         quiz_state = request.session.get(QUIZ_SESSION_KEY)

#         if not quiz_state:
#             return JsonResponse({"error": "No active quiz. Please start a new one."}, status=400)

#         data = json.loads(request.body)
#         selected = data.get("selected", "").strip().upper()

#         questions = quiz_state["questions"]
#         current_index = quiz_state["current"]

#         if current_index >= len(questions):
#             return JsonResponse({"error": "This quiz has already finished."}, status=400)

#         current_question = questions[current_index]
#         correct_letter = current_question["correct"]
#         is_correct = selected == correct_letter

#         if is_correct:
#             quiz_state["score"] += 1

#         quiz_state["current"] += 1
#         total = len(questions)

#         response_data = {
#             "correct": is_correct,
#             "correct_answer": correct_letter,
#             "explanation": current_question.get("explanation", ""),
#             "score": quiz_state["score"],
#             "total": total,
#         }

#         if quiz_state["current"] < total:
#             response_data["finished"] = False
#             response_data["next_question"] = _public_question(
#                 questions[quiz_state["current"]], quiz_state["current"] + 1, total
#             )
#             request.session[QUIZ_SESSION_KEY] = quiz_state
#         else:
#             response_data["finished"] = True
#             del request.session[QUIZ_SESSION_KEY]

#         request.session.modified = True

#         return JsonResponse(response_data)

#     except Exception as error:
#         traceback.print_exc()
#         return JsonResponse({"error": str(error)}, status=500)






"""
views.py - Coach Spark Django Views

Workflow for every chat request:
    user question -> retrieve_context() -> get_user_profile()
    -> get_recommendations() -> Groq -> JSON response
"""
import os
import json
import traceback

from dotenv import load_dotenv
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from groq import Groq

from .rag import retrieve_context
from .personalize import get_user_profile
from .recommender import get_recommendations
from .quiz import generate_quiz
from .escalation import apply_escalation_guard
from . import quiz_history

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found. Please set it in your .env file.")

client = Groq(api_key=GROQ_API_KEY)

MODEL_NAME = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are Coach Spark, an AI Learning & Development Assistant
for manufacturing employees.

Answer ONLY using the retrieved manual context provided below.
Never invent procedures, safety steps, or company policy -- including
general safety knowledge that sounds reasonable (e.g. lockout/tagout,
PPE requirements) if it does not literally appear in the context below.

If the context only partially answers the question, state clearly and
plainly what the manual does NOT cover, then tell the employee to
contact their supervisor or the maintenance team for that specific gap.
Do not suggest "referring to a different document" or guess at what
that document might say -- just say the manual doesn't cover it and
point to a supervisor.

Use clear, worker-friendly language, personalized to the employee's role.
Keep the answer under 150 words and use bullet points where useful."""

NOT_FOUND_MESSAGE = "I couldn't find relevant information in the training manuals."

QUIZ_SESSION_KEY = "coach_spark_quiz"
QUIZ_NOT_FOUND_MESSAGE = (
    "I don't have enough manual content on that topic to build a quiz. "
    "Try a topic like safety, PPE, maintenance, or quality."
)
QUIZ_GENERATION_FAILED_MESSAGE = "I couldn't generate a quiz right now. Please try again."


def index(request):
    """Render the Coach Spark homepage."""
    return render(request, "assistant/index.html")


@csrf_exempt
def chat_api(request):
    """Handle a chat question and return an answer with sources."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

    try:
        data = json.loads(request.body)
        question = data.get("message", "").strip()
        employee_id = data.get("employee_id", "")

        if not question:
            return JsonResponse({"error": "No message provided."}, status=400)

        profile = get_user_profile(employee_id)
        rag_result = retrieve_context(question)

        context = rag_result["context"]
        sources = rag_result["sources"]
        score = rag_result["score"]
        section = rag_result["section"]

        if score == 0:
            return JsonResponse({
                "response": NOT_FOUND_MESSAGE,
                "sources": [],
                "section": None,
                "recommendations": [],
            })

        recommendations = get_recommendations(profile, section)

        employee_summary = (
            f"Employee: {profile.get('name', 'Unknown')}\n"
            f"Role: {profile.get('role', 'Unknown')}\n"
            f"Department: {profile.get('department', 'Unknown')}"
        ) if profile else "Employee: Unknown"

        user_prompt = f"""Employee Profile
{employee_summary}

Training Manual Context
{context}

Question
{question}"""

        completion = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )

        answer = completion.choices[0].message.content
        answer = apply_escalation_guard(answer)

        return JsonResponse({
            "response": answer,
            "sources": sources,
            "section": section,
            "recommendations": recommendations,
        })

    except Exception as error:
        traceback.print_exc()
        return JsonResponse({"error": str(error)}, status=500)


# =====================================================
# INTERACTIVE QUIZ
# =====================================================
# Questions and correct answers live server-side in the Django
# session. Only the question text and options are ever sent to the
# browser -- the answer key never leaves the server.

def _public_question(question: dict, number: int, total: int) -> dict:
    """Strip the correct answer / explanation before sending to the client."""
    return {
        "number": number,
        "total": total,
        "question": question["question"],
        "options": question["options"],
    }


@csrf_exempt
def quiz_start(request):
    """Generate a quiz for a topic and store it in the session."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

    try:
        data = json.loads(request.body)
        topic = data.get("topic", "").strip()
        employee_id = data.get("employee_id", "").strip()

        if not topic:
            return JsonResponse({"error": "Please tell me a topic to quiz you on."}, status=400)

        rag_result = retrieve_context(topic)

        if rag_result["score"] == 0:
            return JsonResponse({"error": QUIZ_NOT_FOUND_MESSAGE}, status=404)

        questions = generate_quiz(client, MODEL_NAME, rag_result["context"])

        if not questions:
            return JsonResponse({"error": QUIZ_GENERATION_FAILED_MESSAGE}, status=500)

        request.session[QUIZ_SESSION_KEY] = {
            "questions": questions,
            "current": 0,
            "score": 0,
            "employee_id": employee_id,
            "section": rag_result["section"],
        }
        request.session.modified = True

        return JsonResponse({
            "started": True,
            "section": rag_result["section"],
            "sources": rag_result["sources"],
            "total": len(questions),
            "question": _public_question(questions[0], 1, len(questions)),
        })

    except Exception as error:
        traceback.print_exc()
        return JsonResponse({"error": str(error)}, status=500)


@csrf_exempt
def quiz_answer(request):
    """Grade the selected option, update the score, and return the next question."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST requests are allowed."}, status=405)

    try:
        quiz_state = request.session.get(QUIZ_SESSION_KEY)

        if not quiz_state:
            return JsonResponse({"error": "No active quiz. Please start a new one."}, status=400)

        data = json.loads(request.body)
        selected = data.get("selected", "").strip().upper()

        questions = quiz_state["questions"]
        current_index = quiz_state["current"]

        if current_index >= len(questions):
            return JsonResponse({"error": "This quiz has already finished."}, status=400)

        current_question = questions[current_index]
        correct_letter = current_question["correct"]
        is_correct = selected == correct_letter

        if is_correct:
            quiz_state["score"] += 1

        quiz_state["current"] += 1
        total = len(questions)

        response_data = {
            "correct": is_correct,
            "correct_answer": correct_letter,
            "explanation": current_question.get("explanation", ""),
            "score": quiz_state["score"],
            "total": total,
        }

        if quiz_state["current"] < total:
            response_data["finished"] = False
            response_data["next_question"] = _public_question(
                questions[quiz_state["current"]], quiz_state["current"] + 1, total
            )
            request.session[QUIZ_SESSION_KEY] = quiz_state
        else:
            response_data["finished"] = True
            quiz_history.record_quiz_result(
                quiz_state.get("employee_id", ""),
                quiz_state.get("section"),
                quiz_state["score"],
                total,
            )
            del request.session[QUIZ_SESSION_KEY]

        request.session.modified = True

        return JsonResponse(response_data)

    except Exception as error:
        traceback.print_exc()
        return JsonResponse({"error": str(error)}, status=500)


@csrf_exempt
def quiz_history_view(request):
    """Return an employee's past quiz attempts and any weak sections."""
    if request.method != "GET":
        return JsonResponse({"error": "Only GET requests are allowed."}, status=405)

    employee_id = request.GET.get("employee_id", "").strip()

    if not employee_id:
        return JsonResponse({"error": "Please provide an employee_id."}, status=400)

    return JsonResponse({
        "history": quiz_history.get_quiz_history(employee_id),
        "weak_sections": quiz_history.get_weak_sections(employee_id),
    })