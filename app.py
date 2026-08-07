"""
app.py - Coach Spark Streamlit Frontend

A persistent, multi-turn chat experience. The employee picks their
profile once, then can keep asking questions in the same session --
nothing resets or stops after a single answer. Reuses the exact same
backend logic as the Django app: assistant.rag, assistant.personalize,
assistant.recommender.
"""
import os
import re

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from assistant.rag import retrieve_context
from assistant.personalize import get_user_profile
from assistant.recommender import get_recommendations
from assistant.quiz import generate_quiz
from assistant.escalation import apply_escalation_guard

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
Never invent procedures, safety steps, or company policy -- including
general safety knowledge that sounds reasonable (e.g. lockout/tagout,
PPE requirements) if it does not literally appear in the context below.

If the context only partially answers the question, state clearly and
plainly what the manual does NOT cover, then tell the employee to
contact their supervisor or the maintenance team for that specific gap.
Do not suggest "referring to a different document" or guess at what
that document might say -- just say the manual doesn't cover it and
point to a supervisor.

Use clear, worker-friendly language.
Keep the answer under 150 words and use bullet points where useful."""

NOT_FOUND_MESSAGE = (
    "🤔 I couldn't find this in the training manuals. "
    "Try rephrasing, or check with your supervisor."
)

QUIZ_NOT_FOUND_MESSAGE = (
    "🤔 I don't have enough manual content on that topic for a quiz. "
    "Try safety, PPE, maintenance, or quality."
)
QUIZ_GENERATION_FAILED_MESSAGE = "😕 I couldn't generate a quiz right now. Please try again."

EMPLOYEES = {
    "E001": {"name": "Rahul Kumar", "role": "Machine Technician", "emoji": "🛠️"},
    "E002": {"name": "Priya Sharma", "role": "New Employee", "emoji": "🌱"},
    "E003": {"name": "Arjun Nair", "role": "Quality Inspector", "emoji": "🔍"},
    "E004": {"name": "Sneha Das", "role": "Forklift Operator", "emoji": "📦"},
}

SECTION_EMOJI = {
    "Safety": "🦺",
    "Machine Operation": "⚙️",
    "Maintenance": "🛠️",
    "Quality": "🔍",
    "Warehouse": "📦",
    "Learning": "📘",
    "Leadership": "🌟",
    "General": "📄",
}

# --------------------------------------------------
# Page Configuration + Theming
# --------------------------------------------------

st.set_page_config(page_title="Coach Spark", page_icon="🤖", layout="centered")

st.markdown("""
<style>
:root{
    --cs-primary:#14487e;
    --cs-accent:#2e7bc3;
    --cs-bg:#eef2f6;
}
.stApp{
    background:linear-gradient(180deg, #e9f1fb 0%, #eef2f6 45%);
}
.cs-hero{
    background:linear-gradient(120deg, #14487e 0%, #2e7bc3 100%);
    padding:22px 26px;
    border-radius:16px;
    color:#fff;
    margin-bottom:18px;
    box-shadow:0 6px 20px rgba(20,72,126,0.25);
}
.cs-hero h1{
    margin:0;
    font-size:26px;
}
.cs-hero p{
    margin:4px 0 0;
    opacity:0.9;
    font-size:14px;
}
.cs-chip{
    display:inline-block;
    padding:4px 12px;
    margin:3px 6px 3px 0;
    border-radius:999px;
    font-size:12.5px;
    font-weight:600;
    background:#eaf2fb;
    color:#14487e;
    border:1px solid #cfe1f4;
}
.cs-chip.source{ background:#fff4e5; color:#9a5b00; border-color:#ffe2b3; }
.cs-chip.reco{ background:#e9f9ef; color:#1a7a3d; border-color:#c9eed7; }
.cs-meta-title{
    font-size:12px;
    font-weight:700;
    text-transform:uppercase;
    letter-spacing:0.5px;
    color:#5b6572;
    margin:10px 0 4px;
}
[data-testid="stChatMessage"]{
    animation: cs-fade-in 0.25s ease-in-out;
}
@keyframes cs-fade-in{
    from{ opacity:0; transform:translateY(6px); }
    to{ opacity:1; transform:translateY(0); }
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="cs-hero">
  <h1>🤖 Coach Spark</h1>
  <p>Your AI Learning &amp; Development Assistant &mdash; ask as many questions as you like!</p>
</div>
""", unsafe_allow_html=True)

# --------------------------------------------------
# Sidebar: Employee + Session Controls
# --------------------------------------------------

with st.sidebar:
    st.markdown("### 👤 Employee")
    employee_id = st.selectbox(
        "Choose your profile",
        options=list(EMPLOYEES.keys()),
        format_func=lambda eid: f"{EMPLOYEES[eid]['emoji']} {EMPLOYEES[eid]['name']} — {EMPLOYEES[eid]['role']}",
    )

    st.markdown("---")
    st.caption(f"💬 Questions asked this session: **{len(st.session_state.get('cs_messages', []))//2}**")
    st.caption("💡 Tip: type *\"quiz me on safety\"* to start an interactive practice quiz.")

    if st.button("🔄 New Session", use_container_width=True):
        st.session_state.cs_messages = []
        st.session_state.cs_quiz = None
        st.rerun()

# --------------------------------------------------
# Session State
# --------------------------------------------------

if "cs_messages" not in st.session_state:
    st.session_state.cs_messages = []

if "cs_quiz" not in st.session_state:
    st.session_state.cs_quiz = None  # {"questions", "current", "score", "stage"}

if "cs_employee" not in st.session_state or st.session_state.cs_employee != employee_id:
    st.session_state.cs_employee = employee_id

# --------------------------------------------------
# Render Chat History
# --------------------------------------------------

if not st.session_state.cs_messages:
    with st.chat_message("assistant", avatar="🤖"):
        st.write(
            "Hello! Ask me about safety, PPE, maintenance, machine operation, "
            "quality, or training — I'll answer using our manuals only. 👷"
        )

for message in st.session_state.cs_messages:
    avatar = "🤖" if message["role"] == "assistant" else "🧑"
    with st.chat_message(message["role"], avatar=avatar):
        st.write(message["content"])

        if message["role"] == "assistant" and message.get("section"):
            emoji = SECTION_EMOJI.get(message["section"], "📄")
            st.markdown(f'<div class="cs-meta-title">🗂️ Section</div>'
                        f'<span class="cs-chip">{emoji} {message["section"]}</span>',
                        unsafe_allow_html=True)

        if message["role"] == "assistant" and message.get("sources"):
            chips = "".join(f'<span class="cs-chip source">📘 {s}</span>' for s in message["sources"])
            st.markdown(f'<div class="cs-meta-title">📚 Sources</div>{chips}', unsafe_allow_html=True)

        if message["role"] == "assistant" and message.get("recommendations"):
            chips = "".join(f'<span class="cs-chip reco">🎯 {r}</span>' for r in message["recommendations"])
            st.markdown(f'<div class="cs-meta-title">🚀 Recommended Next Training</div>{chips}',
                        unsafe_allow_html=True)

# --------------------------------------------------
# Chat Input (stays live for the whole session)
# --------------------------------------------------

question = st.chat_input("Ask about safety, maintenance, quality, SOPs...")

if question:
    st.session_state.cs_messages.append({"role": "user", "content": question})

    if re.search(r"\bquiz\b", question, re.IGNORECASE):
        with st.spinner("🔎 Finding relevant manual content..."):
            rag_result = retrieve_context(question)

        if rag_result["score"] == 0:
            st.session_state.cs_messages.append({
                "role": "assistant",
                "content": QUIZ_NOT_FOUND_MESSAGE,
                "section": None, "sources": [], "recommendations": [],
            })
        else:
            with st.spinner("📝 Writing quiz questions..."):
                quiz_questions = generate_quiz(client, MODEL_NAME, rag_result["context"])

            if not quiz_questions:
                st.session_state.cs_messages.append({
                    "role": "assistant",
                    "content": QUIZ_GENERATION_FAILED_MESSAGE,
                    "section": None, "sources": [], "recommendations": [],
                })
            else:
                st.session_state.cs_messages.append({
                    "role": "assistant",
                    "content": (f"🎯 Let's test your knowledge on **{rag_result['section']}**! "
                                f"{len(quiz_questions)} questions — good luck."),
                    "section": rag_result["section"],
                    "sources": rag_result["sources"],
                    "recommendations": [],
                })
                st.session_state.cs_quiz = {
                    "questions": quiz_questions,
                    "current": 0,
                    "score": 0,
                    "stage": "answering",
                }
        st.rerun()

    else:
        with st.chat_message("user", avatar="🧑"):
            st.write(question)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🔎 Searching training manuals..."):
                rag_result = retrieve_context(question)

            if rag_result["score"] == 0:
                st.write(NOT_FOUND_MESSAGE)
                st.session_state.cs_messages.append({
                    "role": "assistant",
                    "content": NOT_FOUND_MESSAGE,
                    "section": None,
                    "sources": [],
                    "recommendations": [],
                })
            else:
                profile = get_user_profile(employee_id)
                recommendations = get_recommendations(profile, rag_result["section"])

                user_prompt = f"""Employee Role: {profile.get('role', 'Unknown')}

Training Manual Context
{rag_result["context"]}

Question
{question}"""

                with st.spinner("🤖 Generating your answer..."):
                    response = client.chat.completions.create(
                        model=MODEL_NAME,
                        temperature=0.2,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                    )

                answer = response.choices[0].message.content
                answer = apply_escalation_guard(answer)
                st.write(answer)

                section = rag_result["section"]
                emoji = SECTION_EMOJI.get(section, "📄")
                st.markdown(f'<div class="cs-meta-title">🗂️ Section</div>'
                            f'<span class="cs-chip">{emoji} {section}</span>', unsafe_allow_html=True)

                if rag_result["sources"]:
                    chips = "".join(f'<span class="cs-chip source">📘 {s}</span>' for s in rag_result["sources"])
                    st.markdown(f'<div class="cs-meta-title">📚 Sources</div>{chips}', unsafe_allow_html=True)

                if recommendations:
                    chips = "".join(f'<span class="cs-chip reco">🎯 {r}</span>' for r in recommendations)
                    st.markdown(f'<div class="cs-meta-title">🚀 Recommended Next Training</div>{chips}',
                                unsafe_allow_html=True)

                st.session_state.cs_messages.append({
                    "role": "assistant",
                    "content": answer,
                    "section": section,
                    "sources": rag_result["sources"],
                    "recommendations": recommendations,
                })

        # Auto-scroll to the newest message.
        st.markdown("""
        <script>
            window.parent.document.querySelector('section.main').scrollTo({
                top: window.parent.document.querySelector('section.main').scrollHeight,
                behavior: 'smooth'
            });
        </script>
        """, unsafe_allow_html=True)

# --------------------------------------------------
# Interactive Quiz Panel
# --------------------------------------------------
# Rendered as a persistent widget (not a chat bubble) because it needs
# real Streamlit buttons to stay clickable across reruns.

quiz = st.session_state.cs_quiz

if quiz:
    total = len(quiz["questions"])
    idx = quiz["current"]

    st.markdown("---")

    if quiz["stage"] == "finished":
        score = quiz["score"]
        pct = score / total

        st.markdown(f"### 🏁 Quiz Complete — {score}/{total}")

        if pct == 1:
            st.success("🏆 Perfect score! You know this material cold.")
        elif pct >= 0.7:
            st.success("🎉 Nice work — solid understanding!")
        elif pct >= 0.4:
            st.info("👍 Good effort — a bit more review will help.")
        else:
            st.warning("📖 Keep practicing — review the manual and try again!")

        if st.button("✅ Done", use_container_width=True):
            st.session_state.cs_quiz = None
            st.rerun()

    else:
        current_question = quiz["questions"][idx]

        st.markdown(f"### 🎯 Question {idx + 1} of {total}")
        st.progress(idx / total)
        st.write(current_question["question"])

        if quiz["stage"] == "answering":
            for letter, text in current_question["options"].items():
                if st.button(f"{letter}.  {text}", key=f"quiz_opt_{idx}_{letter}", use_container_width=True):
                    quiz["selected"] = letter
                    quiz["correct"] = (letter == current_question["correct"])
                    if quiz["correct"]:
                        quiz["score"] += 1
                    quiz["stage"] = "feedback"
                    st.session_state.cs_quiz = quiz
                    st.rerun()

        elif quiz["stage"] == "feedback":
            for letter, text in current_question["options"].items():
                if letter == current_question["correct"]:
                    st.success(f"✅ {letter}.  {text}")
                elif letter == quiz.get("selected"):
                    st.error(f"❌ {letter}.  {text}")
                else:
                    st.write(f"{letter}.  {text}")

            if current_question.get("explanation"):
                st.caption(f"💡 {current_question['explanation']}")

            st.markdown(f"**Score so far: {quiz['score']}/{total}**")

            next_label = "Next Question ➡️" if idx + 1 < total else "See Results 🏁"
            if st.button(next_label, use_container_width=True):
                quiz["current"] += 1
                quiz["stage"] = "finished" if quiz["current"] >= total else "answering"
                st.session_state.cs_quiz = quiz
                st.rerun()