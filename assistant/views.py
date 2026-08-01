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

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found. Please set it in your .env file.")

client = Groq(api_key=GROQ_API_KEY)

MODEL_NAME = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are Coach Spark, an AI Learning & Development Assistant
for manufacturing employees.

Answer ONLY using the retrieved manual context provided below.
Never invent company policies or procedures.
Use clear, worker-friendly language, personalized to the employee's role.
Keep the answer under 150 words and use bullet points where useful.

If the manual context does not fully answer the question, say so clearly
instead of guessing."""

NOT_FOUND_MESSAGE = "I couldn't find relevant information in the training manuals."


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

        return JsonResponse({
            "response": answer,
            "sources": sources,
            "section": section,
            "recommendations": recommendations,
        })

    except Exception as error:
        traceback.print_exc()
        return JsonResponse({"error": str(error)}, status=500)