"""
rag.py - Coach Spark Retrieval Engine

Reads every .txt manual in knowledge_base/, splits each into paragraph
chunks, and answers questions with a simple weighted keyword search.
No external libraries: only os, re, json, pathlib, collections, string.
"""
import os
import re
import string
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE = BASE_DIR / "knowledge_base"

TOP_K = 3
DEBUG_MODE = True  # set False to silence retrieval debug prints

STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "how", "what", "when", "where", "why", "who",
    "which", "can", "could", "should", "would", "to", "of", "for", "in",
    "on", "at", "by", "with", "and", "or", "but", "if", "it", "its",
    "this", "that", "these", "those", "i", "you", "we", "they", "my",
    "your", "our", "their", "me", "us", "them", "as", "from", "about",
}

SECTION_KEYWORDS = {
    "Safety": ["safety", "ppe", "fire", "chemical", "electrical", "lockout", "emergency", "incident", "hazard"],
    "Maintenance": ["maintenance", "machine", "conveyor", "cnc", "tool", "repair", "hydraulic"],
    "Quality": ["quality", "inspection", "inspector", "defect"],
    "Warehouse": ["forklift", "warehouse", "logistics", "material handling"],
    "Learning": ["learning", "training", "catalog", "induction", "digital"],
    "Leadership": ["career", "leadership", "management"],
}

# --------------------------------------------------------------------
# In-memory index
# --------------------------------------------------------------------

_chunks = []  # list of {"filename": str, "text": str, "section": str}


def _clean_text(text: str) -> str:
    text = text.replace("\r", "").replace("\t", " ")
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _tokenize(text: str) -> list:
    text = text.lower().translate(str.maketrans("", "", string.punctuation))
    words = [w for w in text.split() if w and w not in STOP_WORDS]
    return words


def _detect_section(filename: str, text: str) -> str:
    haystack = f"{filename} {text}".lower()
    for section, keywords in SECTION_KEYWORDS.items():
        if any(keyword in haystack for keyword in keywords):
            return section
    return "General"


def _load_manuals() -> list:
    manuals = []
    if not KNOWLEDGE_BASE.exists():
        print("Knowledge base folder not found:", KNOWLEDGE_BASE)
        return manuals

    for path in sorted(KNOWLEDGE_BASE.glob("*.txt")):
        try:
            content = _clean_text(path.read_text(encoding="utf-8"))
            manuals.append({"filename": path.name, "content": content})
        except Exception as error:
            print(f"Could not read {path.name}: {error}")
    return manuals


def _chunk_manual(manual: dict) -> list:
    seen_paragraphs = set()
    chunks = []
    for paragraph in manual["content"].split("\n\n"):
        paragraph = paragraph.strip()
        if len(paragraph) < 40 or paragraph in seen_paragraphs:
            continue
        seen_paragraphs.add(paragraph)
        chunks.append({
            "filename": manual["filename"],
            "text": paragraph,
            "section": _detect_section(manual["filename"], paragraph),
        })
    return chunks


def build_index() -> None:
    """Read every manual and rebuild the in-memory paragraph index."""
    global _chunks
    manuals = _load_manuals()

    seen_filenames = set()
    unique_manuals = []
    for manual in manuals:
        if manual["filename"] not in seen_filenames:
            seen_filenames.add(manual["filename"])
            unique_manuals.append(manual)

    _chunks = []
    for manual in unique_manuals:
        _chunks.extend(_chunk_manual(manual))

    print(f"Loaded {len(unique_manuals)} manuals | Indexed {len(_chunks)} paragraphs")


def _score_chunk(question_words: list, chunk: dict) -> int:
    """
    Weighted keyword scoring:
      +5  a question word appears in the filename
      +3  each distinct question word found in the paragraph
      +1  each extra repeat of a matched word
      +2  a question word matches the detected section name
    """
    score = 0
    filename_lower = chunk["filename"].lower()
    section_lower = chunk["section"].lower()
    paragraph_words = _tokenize(chunk["text"])
    word_counts = Counter(paragraph_words)

    for word in set(question_words):
        if word in filename_lower:
            score += 5
        if word in section_lower:
            score += 2
        occurrences = word_counts.get(word, 0)
        if occurrences == 1:
            score += 3
        elif occurrences > 1:
            score += 3 + (occurrences - 1)

    return score


def retrieve_context(question: str) -> dict:
    """
    Search the indexed manuals for the best matching paragraphs.

    Returns:
        {"context": str, "sources": [str], "score": int, "section": str}
    """
    empty_result = {"context": "", "sources": [], "score": 0, "section": "General"}

    if not question or not question.strip():
        return empty_result

    question_words = _tokenize(question)
    if not question_words:
        return empty_result

    scored = []
    for chunk in _chunks:
        score = _score_chunk(question_words, chunk)
        if score > 0:
            scored.append({**chunk, "score": score})

    if not scored:
        return empty_result

    scored.sort(key=lambda c: c["score"], reverse=True)

    selected, seen_text = [], set()
    for chunk in scored:
        if chunk["text"] in seen_text:
            continue
        seen_text.add(chunk["text"])
        selected.append(chunk)
        if len(selected) == TOP_K:
            break

    top_score = selected[0]["score"]
    context = "\n\n".join(chunk["text"] for chunk in selected)

    sources = []
    for chunk in selected:
        if chunk["filename"] not in sources:
            sources.append(chunk["filename"])

    section = selected[0]["section"]

    if DEBUG_MODE:
        print("----- RAG DEBUG -----")
        print("Question   :", question)
        print("Top score  :", top_score)
        print("Matched    :", sources)
        print("Section    :", section)
        print("----------------------")

    return {
        "context": context,
        "sources": sources,
        "score": top_score,
        "section": section,
    }


# Build the index once, when the module is first imported.
build_index()