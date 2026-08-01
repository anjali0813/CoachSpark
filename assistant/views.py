# import os
# import json
# import traceback
# from dotenv import load_dotenv

# from django.shortcuts import render
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt

# from groq import Groq

# from .rag import retrieve_context
# from .personalize import get_employee_profile
# from .recommender import recommend_next_training


# # =====================================================
# # GROQ INITIALIZATION
# # =====================================================

# load_dotenv()

# GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# if not GROQ_API_KEY:
#     raise ValueError(
#         "GROQ_API_KEY not found. Please set it in .env file."
#     )

# client = Groq(api_key=GROQ_API_KEY)


# # =====================================================
# # AGENT TOOLS
# # =====================================================

# def troubleshoot_machine(machine_name: str, issue_description: str) -> str:
#     """
#     Return troubleshooting steps for known machines.
#     """

#     manuals = {

#         "conveyor belt":
#         (
#             "1. Press the Emergency Stop.\n"
#             "2. Disconnect the power supply.\n"
#             "3. Remove the obstruction safely.\n"
#             "4. Inspect rollers and belt alignment.\n"
#             "5. Restart only after supervisor approval."
#         ),

#         "cnc machine":
#         (
#             "1. Pause machine operation.\n"
#             "2. Check coolant level.\n"
#             "3. Verify spindle temperature.\n"
#             "4. Report overheating if it continues."
#         ),

#         "forklift":
#         (
#             "1. Park safely.\n"
#             "2. Turn off ignition.\n"
#             "3. Tag the vehicle.\n"
#             "4. Report hydraulic leak immediately."
#         )

#     }

#     for machine, solution in manuals.items():

#         if machine in machine_name.lower():
#             return solution

#     return (
#         "Machine not found in troubleshooting manual.\n"
#         "Please contact your supervisor."
#     )


# def recommend_skills(current_role: str) -> str:
#     """
#     Recommend skills based on employee role.
#     """

#     role_skills = {

#         "machine technician": [
#             "PLC Basics",
#             "Machine Maintenance",
#             "Electrical Safety",
#             "Industrial Automation"
#         ],

#         "quality inspector": [
#             "Advanced Quality Control",
#             "Root Cause Analysis",
#             "Six Sigma Basics"
#         ],

#         "forklift operator": [
#             "Warehouse Safety",
#             "Material Handling",
#             "Fire Safety"
#         ],

#         "new employee": [
#             "Factory Induction",
#             "PPE Guidelines",
#             "5S"
#         ]

#     }

#     skills = role_skills.get(
#         current_role.lower(),
#         ["General Workplace Safety"]
#     )

#     return json.dumps({

#         "role": current_role,
#         "recommended_skills": skills

#     })


# def get_practice_quiz(topic: str) -> str:
#     """
#     Return a quick quiz.
#     """

#     quizzes = {

#         "safety":
#         (
#             "Safety Quiz\n\n"
#             "What should you do first before clearing a conveyor belt jam?\n\n"
#             "A. Remove debris\n"
#             "B. Press Emergency Stop\n"
#             "C. Restart machine"
#         ),

#         "quality":
#         (
#             "Quality Quiz\n\n"
#             "When should measuring equipment be calibrated?\n\n"
#             "A. Every shift\n"
#             "B. Monthly\n"
#             "C. Only when broken"
#         )

#     }

#     return quizzes.get(
#         topic.lower(),
#         "Quiz unavailable."
#     )


# # =====================================================
# # TOOL SCHEMA
# # =====================================================

# tools_schema = [

#     {
#         "type": "function",
#         "function": {

#             "name": "troubleshoot_machine",

#             "description":
#                 "Provide machine troubleshooting steps.",

#             "parameters": {

#                 "type": "object",

#                 "properties": {

#                     "machine_name": {
#                         "type": "string"
#                     },

#                     "issue_description": {
#                         "type": "string"
#                     }

#                 },

#                 "required": [
#                     "machine_name",
#                     "issue_description"
#                 ]

#             }

#         }
#     },

#     {
#         "type": "function",
#         "function": {

#             "name": "recommend_skills",

#             "description":
#                 "Recommend training based on employee role.",

#             "parameters": {

#                 "type": "object",

#                 "properties": {

#                     "current_role": {
#                         "type": "string"
#                     }

#                 },

#                 "required": [
#                     "current_role"
#                 ]

#             }

#         }
#     },

#     {
#         "type": "function",
#         "function": {

#             "name": "get_practice_quiz",

#             "description":
#                 "Generate a short practice quiz.",

#             "parameters": {

#                 "type": "object",

#                 "properties": {

#                     "topic": {
#                         "type": "string"
#                     }

#                 },

#                 "required": [
#                     "topic"
#                 ]

#             }

#         }
#     }

# ]
# # =====================================================
# # HOME PAGE
# # =====================================================

# def index(request):
#     """
#     Render the Coach Spark homepage.
#     """
#     return render(request, "assistant/index.html")


# # =====================================================
# # CHAT API
# # =====================================================

# @csrf_exempt
# def chat_api(request):

#     if request.method != "POST":

#         return JsonResponse(
#             {"error": "Only POST requests are allowed."},
#             status=405
#         )

#     try:

#         # ==========================================
#         # Read Request
#         # ==========================================

#         data = json.loads(request.body)

#         user_message = data.get("message", "").strip()

#         if not user_message:

#             return JsonResponse(
#                 {"error": "No message provided."},
#                 status=400
#             )

#         # ==========================================
#         # Employee Selection
#         # ==========================================

#         employee_id = data.get("employee_id", "E001")

#         profile = get_employee_profile(employee_id)

#         if profile is None:

#             return JsonResponse(
#                 {"error": "Employee profile not found."},
#                 status=404
#             )

#         recommendations = recommend_next_training(profile)

#         # ==========================================
#         # RAG Retrieval
#         # ==========================================

#         rag_result = retrieve_context(user_message)

#         context = rag_result.get("context", "")
#         sources = rag_result.get("sources", [])
#         score = rag_result.get("score", 0)
#         section = rag_result.get("section", "General")

#         # Debug

#         print("\n========== RAG ==========")
#         print("Question :", user_message)
#         print("Score    :", score)
#         print("Sources  :", sources)
#         print("=========================\n")

#         # ==========================================
#         # Hallucination Prevention
#         # ==========================================

#         if score == 0:

#             return JsonResponse({

#                 "response":
#                 (
#                     "I couldn't find this information "
#                     "in the training documents.\n\n"
#                     "Please contact your supervisor "
#                     "or training coordinator."
#                 ),

#                 "tool_used": None,

#                 "sources": [],

#                 "section": None

#             })

#         # ==========================================
#         # Employee Context
#         # ==========================================

#         employee_context = f"""
# Employee Profile

# Name: {profile['name']}
# Role: {profile['role']}
# Department: {profile['department']}
# Experience: {profile['experience']}

# Completed Training:
# {', '.join(profile['completed_training'])}
# """

#         # ==========================================
#         # System Prompt
#         # ==========================================

#         system_prompt = f"""
# You are Coach Spark, an AI Learning & Development Assistant for manufacturing employees.

# =========================
# EMPLOYEE PROFILE
# =========================

# {employee_context}

# =========================
# TRAINING DOCUMENTS
# =========================

# {context}

# =========================
# YOUR TASK
# =========================

# Answer the user's question ONLY using the TRAINING DOCUMENTS.

# If multiple documents contain relevant information,
# combine them into one complete answer.

# =========================
# STRICT RULES
# =========================

# 1. Never use your own knowledge.

# 2. Never invent procedures.

# 3. Never add maintenance or safety steps
# that are not present in the documents.

# 4. If the documents only partially answer
# the question, state only what exists.

# 5. If the answer is not in the documents,
# reply exactly:

# "I couldn't find this information in the training documents."

# 6. Personalize ONLY the wording.

# Examples:

# • New Employee
# Explain simply.

# • Machine Technician
# Use technical terminology.

# • Quality Inspector
# Focus on inspection and compliance.

# • Forklift Operator
# Focus on safe operation.

# Never personalize by adding technical
# information that is not present.

# 7. Safety always comes first.

# 8. Keep answers concise.

# 9. Use bullet points whenever appropriate.

# 10. End with a brief safety reminder only if
# the retrieved documents contain one.
# """

#                 # ==========================================
#         # Build Conversation
#         # ==========================================

#         messages = [
#             {
#                 "role": "system",
#                 "content": system_prompt
#             },
#             {
#                 "role": "user",
#                 "content": user_message
#             }
#         ]

#         tool_used = None

#         # ==========================================
#         # First LLM Call
#         # ==========================================

#         response = client.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=messages,
#             tools=tools_schema,
#             tool_choice="auto"
#         )

#         msg = response.choices[0].message

#         # ==========================================
#         # Tool Calling
#         # ==========================================

#         if msg.tool_calls:

#             messages.append(msg)

#             for tool_call in msg.tool_calls:

#                 func_name = tool_call.function.name
#                 args = json.loads(tool_call.function.arguments)

#                 tool_used = func_name

#                 if func_name == "troubleshoot_machine":

#                     result = troubleshoot_machine(
#                         args.get("machine_name", ""),
#                         args.get("issue_description", "")
#                     )

#                 elif func_name == "recommend_skills":

#                     result = recommend_skills(profile["role"])

#                 elif func_name == "get_practice_quiz":

#                     result = get_practice_quiz(
#                         args.get("topic", "safety")
#                     )

#                 else:

#                     result = "Tool not found."

#                 messages.append({
#                     "tool_call_id": tool_call.id,
#                     "role": "tool",
#                     "name": func_name,
#                     "content": result
#                 })

#             # ==========================================
#             # Second LLM Call
#             # ==========================================

#             final_response = client.chat.completions.create(
#                 model="llama-3.3-70b-versatile",
#                 messages=messages
#             )

#             final_text = final_response.choices[0].message.content

#         else:

#             final_text = msg.content

#         # ==========================================
#         # Append Sources
#         # ==========================================

#         if sources:

#             final_text += "\n\n📘 Sources:\n"

#             for src in sources:
#                 final_text += f"• {src}\n"

#         # ==========================================
#         # Append Section
#         # ==========================================

#         final_text += f"\n📑 Section: {section}"

#         # ==========================================
#         # Append Recommended Training
#         # ==========================================

#         if recommendations:

#             final_text += "\n\n📚 Recommended Next Training:\n"

#             for course in recommendations:
#                 final_text += f"• {course}\n"

#         # ==========================================
#         # Return Response
#         # ==========================================

#         return JsonResponse({

#             "response": final_text,

#             "tool_used": tool_used,

#             "sources": sources,

#             "section": section

#         })

#     except Exception as e:

#         traceback.print_exc()

#         return JsonResponse({

#             "error": str(e)

#         }, status=500)


#     return JsonResponse(
#         {"error": "Invalid request method"},
#         status=405
#     )




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