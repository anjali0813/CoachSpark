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
from assistant.quiz import generate_question
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

MODEL_NAME = "openai/gpt-oss-120b"

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

PERSONALIZE the answer to the employee profile below. This must change
HOW you present the same manual content, never WHAT facts you include --
you may never add a fact, step, or warning that isn't in the manual
context, but you must adjust:

- New employees (experience under 6 months) or anyone whose completed
  training does not include this topic: use more explicit, step-by-step
  phrasing, briefly explain WHY each safety step matters, and do not
  assume they know shop-floor terms or abbreviations.
- Experienced employees whose completed training already covers this
  topic: be more concise, skip explaining basics they've already been
  trained on, and lead with anything that's easy to overlook rather
  than re-teaching fundamentals.
- Always keep every safety-critical step from the manual regardless of
  experience level -- conciseness must never drop a safety instruction.
- If the employee's role is different from who the manual content is
  clearly written for (e.g. a Quality Inspector asking a Maintenance
  question), briefly note that this falls outside their usual role and
  they should coordinate with the responsible team.
- When answering a question about recommended, next, or suggested
  training or courses: NEVER list a course that already appears in the
  employee's Completed Training. List only courses they have not yet
  completed. This is a strict rule, not a stylistic preference -- check
  the Completed Training list explicitly before naming any course.
- ALWAYS open the response by addressing the employee by their first
  name in a sentence (e.g. "Rahul, ..." or "Hi Priya, ..."). This is a
  strict rule, not a formatting choice you may skip -- do not open with
  a title-only header, a bare "Note:", or any other impersonal opener
  that never actually names the employee. The name may appear inside a
  bold header if you use one, but a header alone is not sufficient if
  the body of the response never addresses them by name either.

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

QUIZ_TARGET_QUESTIONS = 5
DIFFICULTY_ORDER = ["easy", "medium", "hard"]


def _next_quiz_difficulty(current_difficulty: str, was_correct: bool) -> str:
    """Step difficulty up after a correct answer, down after a wrong one."""
    idx = DIFFICULTY_ORDER.index(current_difficulty) if current_difficulty in DIFFICULTY_ORDER else 1
    idx = min(idx + 1, len(DIFFICULTY_ORDER) - 1) if was_correct else max(idx - 1, 0)
    return DIFFICULTY_ORDER[idx]

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
/* Tell the browser this page is designed for light mode. Without this,
   Chrome for Android's "force dark" feature will auto-invert colors on
   pages it thinks have no explicit color scheme -- which is exactly
   what was washing out / hiding text on mobile while it looked fine
   on desktop. This single declaration stops the browser from touching
   our colors at all. */
:root{
    color-scheme: light only;
    --cs-primary:#14487e;
    --cs-accent:#2e7bc3;
    --cs-bg:#eef2f6;
    --cs-text:#1e2733;
}
html, body{
    color-scheme: light only;
}
.stApp{
    background:linear-gradient(180deg, #e9f1fb 0%, #eef2f6 45%);
    color: var(--cs-text) !important;
}
/* Explicitly pin chat message text color -- st.write() output inherits
   theme text color, which is the exact element that was disappearing
   on mobile. Pinning it here means it no longer depends on Streamlit's
   theme resolution or the device's dark-mode setting. */
[data-testid="stChatMessageContent"],
[data-testid="stChatMessageContent"] p,
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p{
    color: var(--cs-text) !important;
}
/* Native Streamlit buttons (quiz options, New Session) are separate
   elements from the chat text above and were still rendering as solid
   dark bars with invisible text on mobile. Pin their colors explicitly
   too, in both default and hover states. */
.stButton button,
[data-testid="stButton"] button{
    background-color: #ffffff !important;
    color: var(--cs-text) !important;
    border: 1px solid #dce3ea !important;
}
.stButton button:hover,
[data-testid="stButton"] button:hover{
    background-color: #f5f9fd !important;
    border-color: var(--cs-accent) !important;
    color: var(--cs-text) !important;
}
.stButton button p,
.stButton button div,
[data-testid="stButton"] button p,
[data-testid="stButton"] button div{
    color: var(--cs-text) !important;
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
/* The employee picker is a plain "choose from a list" control. Streamlit's
   selectbox is built on a searchable text input under the hood, and that
   input can still show a focus caret even with caret-color hidden. Instead,
   stop the input from ever being clickable/focusable -- clicks fall through
   to the dropdown control underneath, which still opens the list normally,
   but the input itself can never show a cursor. Two selector patterns are
   included since the exact DOM attributes vary slightly across Streamlit
   versions. */
div[data-baseweb="select"] input,
[data-testid="stSelectbox"] input{
    caret-color: transparent !important;
    cursor: default !important;
    pointer-events: none !important;
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
            _quiz_profile = get_user_profile(employee_id)
            rag_result = retrieve_context(question, profile_hint=_quiz_profile.get("role", ""))

        if rag_result["score"] == 0:
            st.session_state.cs_messages.append({
                "role": "assistant",
                "content": QUIZ_NOT_FOUND_MESSAGE,
                "section": None, "sources": [], "recommendations": [],
            })
        else:
            with st.spinner("📝 Writing your first question..."):
                first_question = generate_question(
                    client, MODEL_NAME, rag_result["context"], difficulty="medium"
                )

            if not first_question:
                st.session_state.cs_messages.append({
                    "role": "assistant",
                    "content": QUIZ_GENERATION_FAILED_MESSAGE,
                    "section": None, "sources": [], "recommendations": [],
                })
            else:
                st.session_state.cs_messages.append({
                    "role": "assistant",
                    "content": (f"🎯 Let's test your knowledge on **{rag_result['section']}**! "
                                f"Questions adapt to how you're doing — good luck."),
                    "section": rag_result["section"],
                    "sources": rag_result["sources"],
                    "recommendations": [],
                })
                st.session_state.cs_quiz = {
                    "employee_id": employee_id,
                    "context": rag_result["context"],
                    "section": rag_result["section"],
                    "difficulty": "medium",
                    "used_questions": [first_question["question"]],
                    "current_question": first_question,
                    "index": 0,
                    "target_total": QUIZ_TARGET_QUESTIONS,
                    "score": 0,
                    "stage": "answering",
                    "selected": None,
                    "correct": None,
                    "wrong_focus_areas": [],
                }
        st.rerun()

    else:
        with st.chat_message("user", avatar="🧑"):
            st.write(question)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🔎 Searching training manuals..."):
                profile = get_user_profile(employee_id)
                rag_result = retrieve_context(question, profile_hint=profile.get("role", ""))

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
                recommendations = get_recommendations(profile, rag_result["section"])

                completed = ", ".join(profile.get("completed_training", [])) or "None recorded"

                user_prompt = f"""Employee Profile
Name: {profile.get('name', 'Unknown')}
Role: {profile.get('role', 'Unknown')}
Department: {profile.get('department', 'Unknown')}
Experience: {profile.get('experience', 'Unknown')}
Completed Training: {completed}

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
    total = quiz["target_total"]
    idx = quiz["index"]
    current_question = quiz["current_question"]

    st.markdown("---")

    if quiz["stage"] == "finished":
        score = quiz["score"]
        answered = idx + (1 if quiz.get("correct") is not None else 0)
        pct = score / answered if answered else 0

        st.markdown(f"### 🏁 Quiz Complete — {score}/{answered}")

        if pct == 1:
            st.success("🏆 Perfect score! You know this material cold.")
        elif pct >= 0.7:
            st.success("🎉 Nice work — solid understanding!")
        elif pct >= 0.4:
            st.info("👍 Good effort — a bit more review will help.")
        else:
            st.warning("📖 Keep practicing — review the manual and try again!")

        if quiz["wrong_focus_areas"]:
            st.markdown("**📌 Areas to revisit:**")
            for area in dict.fromkeys(quiz["wrong_focus_areas"]):  # dedupe, preserve order
                st.write(f"- {area}")

        if st.button("✅ Done", use_container_width=True):
            st.session_state.cs_quiz = None
            st.rerun()

    else:
        difficulty_emoji = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(quiz["difficulty"], "🟡")
        st.markdown(
            f'### 🎯 Question {idx + 1} of {total} '
            f'<span class="cs-chip">{difficulty_emoji} {quiz["difficulty"].title()}</span>',
            unsafe_allow_html=True,
        )
        st.progress(idx / total)
        st.write(current_question["question"])

        if quiz["stage"] == "answering":
            for letter, text in current_question["options"].items():
                if st.button(f"{letter}.  {text}", key=f"quiz_opt_{idx}_{letter}", use_container_width=True):
                    quiz["selected"] = letter
                    quiz["correct"] = (letter == current_question["correct"])
                    if quiz["correct"]:
                        quiz["score"] += 1
                    else:
                        quiz["wrong_focus_areas"].append(
                            current_question.get("focus_area") or quiz["section"]
                        )
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

            # Recommended improvement -- tied to the employee's actual
            # learning path (recommender.py), not a generic "review the
            # manual" message. This is what turns feedback into a next step.
            profile = get_user_profile(quiz["employee_id"])
            recommendations = get_recommendations(profile, quiz["section"])
            focus_label = current_question.get("focus_area") or quiz["section"]

            if quiz["correct"] and recommendations:
                st.info(f"✅ Solid grasp of **{focus_label}**. Keep building on it "
                        f"with **{recommendations[0]}**.")
            elif not quiz["correct"] and recommendations:
                st.warning(f"📌 Recommended focus: review **{recommendations[0]}** "
                           f"to strengthen **{focus_label}**.")

            st.markdown(f"**Score so far: {quiz['score']}/{idx + 1}**")

            next_label = "Next Question ➡️" if idx + 1 < total else "See Results 🏁"
            if st.button(next_label, use_container_width=True):
                if idx + 1 >= total:
                    quiz["stage"] = "finished"
                    st.session_state.cs_quiz = quiz
                else:
                    next_difficulty = _next_quiz_difficulty(quiz["difficulty"], quiz["correct"])
                    with st.spinner("📝 Writing your next question..."):
                        next_question = generate_question(
                            client, MODEL_NAME, quiz["context"],
                            difficulty=next_difficulty,
                            exclude_questions=quiz["used_questions"],
                        )
                    if not next_question:
                        quiz["stage"] = "finished"
                    else:
                        quiz["used_questions"].append(next_question["question"])
                        quiz["current_question"] = next_question
                        quiz["difficulty"] = next_difficulty
                        quiz["index"] += 1
                        quiz["stage"] = "answering"
                        quiz["selected"] = None
                        quiz["correct"] = None
                    st.session_state.cs_quiz = quiz
                st.rerun()
