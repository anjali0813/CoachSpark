"""Standalone CLI demo for Coach Spark."""

import os
from dotenv import load_dotenv
from groq import Groq
from assistant.rag import retrieve_context
from assistant.personalize import get_user_profile
from assistant.recommender import get_recommendations

load_dotenv()
api_key=os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found.")
client=Groq(api_key=api_key)

SYSTEM_PROMPT="You are Coach Spark. Use only retrieved manual context."

def ask(question,user_id="worker001"):
    rag=retrieve_context(question)
    if rag["score"]==0:
        return "I couldn't find relevant information in the knowledge base."
    profile=get_user_profile(user_id)
    recs=get_recommendations(profile,rag["section"])
    prompt=f"Context:\n{rag['context']}\n\nQuestion:\n{question}"
    res=client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":prompt}],
        temperature=0.2,
    )
    ans=res.choices[0].message.content.strip()
    out="🤖 Coach Spark\n\n"+ans+"\n\n📘 Sources\n"
    out+="\n".join(f"• {s}" for s in rag["sources"])
    out+=f"\n\n📑 Section\n{rag['section']}\n\n📚 Recommended Next Training\n"
    out+="\n".join(f"• {r}" for r in recs)
    return out

if __name__=="__main__":
    print("Coach Spark CLI (type exit to quit)")
    while True:
        q=input("\nAsk: ").strip()
        if q.lower() in ("exit","quit"):
            break
        print(ask(q))