# import os

# import streamlit as st
# from dotenv import load_dotenv
# from groq import Groq

# from assistant.personalize import get_user_profile
# from assistant.rag import retrieve_context
# from assistant.recommender import get_recommendations

# # --------------------------------------------------
# # Load API Key
# # --------------------------------------------------

# load_dotenv()

# api_key = os.getenv("GROQ_API_KEY")

# if not api_key:
#     try:
#         api_key = st.secrets["GROQ_API_KEY"]
#     except Exception:
#         api_key = None

# if not api_key:
#     st.error("GROQ_API_KEY not found.")
#     st.stop()

# client = Groq(api_key=api_key)

# # --------------------------------------------------
# # Page Configuration
# # --------------------------------------------------

# st.set_page_config(
#     page_title="Coach Spark",
#     page_icon="🤖",
#     layout="centered"
# )

# st.title("🤖 Coach Spark")
# st.caption("AI Learning & Development Assistant")

# # --------------------------------------------------
# # User Selection
# # --------------------------------------------------

# user_id = st.selectbox(
#     "Employee",
#     [
#         "worker001",
#         "worker002",
#         "worker003"
#     ]
# )

# question = st.text_input(
#     "Ask a training question"
# )

# # --------------------------------------------------
# # Ask Button
# # --------------------------------------------------

# if st.button("Ask"):

#     if not question.strip():
#         st.warning("Please enter a question.")
#         st.stop()

#     with st.spinner("Searching training manuals..."):

#         rag = retrieve_context(question)

#     if rag["score"] == 0:

#         st.warning(
#             "No relevant information was found in the knowledge base."
#         )

#         st.stop()

#     profile = get_user_profile(user_id)

#     recommendations = get_recommendations(
#         profile,
#         rag["section"]
#     )

#     system_prompt = """
# You are Coach Spark.

# Answer ONLY using the retrieved training manual context.

# Keep answers:

# - practical
# - worker friendly
# - concise
# - easy to understand

# Never invent company policies.

# If information is missing,
# say it was not found in the manuals.
# """

#     prompt = f"""
# Training Manual Context

# {rag["context"]}

# Question

# {question}
# """

#     response = client.chat.completions.create(

#         model="llama-3.3-70b-versatile",

#         temperature=0.2,

#         messages=[
#             {
#                 "role": "system",
#                 "content": system_prompt
#             },
#             {
#                 "role": "user",
#                 "content": prompt
#             }
#         ]
#     )

#     answer = response.choices[0].message.content

#     # --------------------------------------------------
#     # Display Response
#     # --------------------------------------------------

#     st.subheader("Answer")

#     st.write(answer)

#     st.subheader("Training Section")

#     st.info(rag["section"])

#     st.subheader("Sources")

#     for source in rag["sources"]:
#         st.write(f"• {source}")

#     st.subheader("Recommended Next Training")

#     if recommendations:

#         for item in recommendations:
#             st.write(f"• {item}")

#     else:

#         st.write("No recommendations available.")



"""
app.py - Coach Spark Streamlit Frontend

Reuses the exact same backend logic as the Django app:
assistant.rag, assistant.personalize, assistant.recommender.
"""
import os

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from assistant.rag import retrieve_context
from assistant.personalize import get_user_profile
from assistant.recommender import get_recommendations

# --------------------------------------------------
# Load API Key
# --------------------------------------------------

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        api_key = None

if not api_key:
    st.error("GROQ_API_KEY not found. Add it to your .env file or Streamlit secrets.")
    st.stop()

client = Groq(api_key=api_key)

MODEL_NAME = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are Coach Spark, an AI Learning & Development Assistant
for manufacturing employees.

Answer ONLY using the retrieved manual context provided below.
Never invent company policies or procedures.
Use clear, worker-friendly language.
Keep the answer under 150 words and use bullet points where useful.

If the manual context does not fully answer the question, say so clearly
instead of guessing."""

# --------------------------------------------------
# Page Configuration
# --------------------------------------------------

st.set_page_config(page_title="Coach Spark", page_icon="🤖", layout="centered")

st.title("🤖 Coach Spark")
st.caption("AI Learning & Development Assistant")

# --------------------------------------------------
# Employee Selection
# --------------------------------------------------

EMPLOYEES = {
    "E001": "Rahul Kumar - Machine Technician",
    "E002": "Priya Sharma - New Employee",
    "E003": "Arjun Nair - Quality Inspector",
    "E004": "Sneha Das - Forklift Operator",
}

employee_id = st.selectbox(
    "Employee",
    options=list(EMPLOYEES.keys()),
    format_func=lambda eid: EMPLOYEES[eid],
)

question = st.text_input("Ask a training question")

# --------------------------------------------------
# Ask Button
# --------------------------------------------------

if st.button("Ask"):

    if not question.strip():
        st.warning("Please enter a question.")
        st.stop()

    with st.spinner("Searching training manuals..."):
        rag_result = retrieve_context(question)

    if rag_result["score"] == 0:
        st.warning("No relevant information was found in the knowledge base.")
        st.stop()

    profile = get_user_profile(employee_id)
    recommendations = get_recommendations(profile, rag_result["section"])

    user_prompt = f"""Training Manual Context
{rag_result["context"]}

Question
{question}"""

    with st.spinner("Generating answer..."):
        response = client.chat.completions.create(
            model=MODEL_NAME,
            temperature=0.2,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )

    answer = response.choices[0].message.content

    # --------------------------------------------------
    # Display Response
    # --------------------------------------------------

    st.subheader("Answer")
    st.write(answer)

    st.subheader("Training Section")
    st.info(rag_result["section"])

    st.subheader("Sources")
    for source in rag_result["sources"]:
        st.write(f"• {source}")

    st.subheader("Recommended Next Training")
    if recommendations:
        for item in recommendations:
            st.write(f"• {item}")
    else:
        st.write("No recommendations available.")