"""
rag.py - Simple keyword-based RAG for Coach Spark
"""
import os
import re

KNOWLEDGE_BASE = os.path.join(os.path.dirname(__file__), "knowledge_base")
TOP_K = 3
MIN_SCORE = 1

documents = []
chunks = []

def clean_text(text):
    text = text.replace("\r", "").replace("\t", " ")
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def load_documents():
    docs = []
    if not os.path.exists(KNOWLEDGE_BASE):
        print("Knowledge base not found.")
        return docs
    for name in sorted(os.listdir(KNOWLEDGE_BASE)):
        if not name.endswith(".txt"):
            continue
        path = os.path.join(KNOWLEDGE_BASE, name)
        try:
            with open(path, encoding="utf-8") as f:
                docs.append({"filename": name, "content": clean_text(f.read())})
        except Exception as e:
            print(f"Failed: {name} -> {e}")
    return docs

def chunk_document(doc):
    out = []
    for p in doc["content"].split("\n\n"):
        p = p.strip()
        if len(p) >= 40:
            out.append({"filename": doc["filename"], "text": p})
    return out

def tokenize(text):
    text = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    return [w for w in text.split() if len(w) > 1]

def keyword_score(query, paragraph):
    return len(set(tokenize(query)) & set(tokenize(paragraph)))

def detect_section(sources):
    names = " ".join(sources).lower()
    if any(k in names for k in ["maintenance","machine","conveyor","cnc","tool"]):
        return "Maintenance"
    if any(k in names for k in ["safety","ppe","fire","chemical","electrical","lockout","emergency","incident"]):
        return "Safety"
    if any(k in names for k in ["quality","inspection"]):
        return "Quality"
    if any(k in names for k in ["forklift","warehouse"]):
        return "Logistics"
    if any(k in names for k in ["learning","training","catalog","digital","induction"]):
        return "Learning"
    if any(k in names for k in ["career","leadership"]):
        return "Career Development"
    return "General"

def retrieve_context(query):
    if not query.strip():
        return {"context":"","sources":[],"score":0,"section":"General"}
    results = []
    for c in chunks:
        s = keyword_score(query, c["text"])
        if s > 0:
            results.append({"filename":c["filename"],"text":c["text"],"score":s})
    results.sort(key=lambda x: x["score"], reverse=True)
    selected, seen = [], set()
    for r in results:
        if r["text"] in seen:
            continue
        seen.add(r["text"])
        selected.append(r)
        if len(selected) == TOP_K:
            break
    if not selected:
        return {"context":"","sources":[],"score":0,"section":"General"}
    avg = sum(r["score"] for r in selected)/len(selected)
    if avg < MIN_SCORE:
        return {"context":"","sources":[],"score":0,"section":"General"}
    context = "\n\n".join(r["text"] for r in selected)
    sources = []
    for r in selected:
        if r["filename"] not in sources:
            sources.append(r["filename"])
    print("\n===== RAG DEBUG =====")
    print("Question:", query)
    print("Score:", round(avg,2))
    print("Sources:", sources)
    print("=====================\n")
    return {
        "context": context,
        "sources": sources,
        "score": avg,
        "section": detect_section(sources)
    }

def rebuild_index():
    global documents, chunks
    documents = load_documents()
    chunks = []
    for d in documents:
        chunks.extend(chunk_document(d))
    print(f"Loaded {len(documents)} manuals | Indexed {len(chunks)} paragraphs")

rebuild_index()
















# import os
# import re

# # Path to the knowledge folder
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# KNOWLEDGE_PATH = os.path.join(BASE_DIR, "knowledge_base")


# def preprocess_text(text):
#     """
#     Convert text to lowercase and remove punctuation.
#     """
#     text = text.lower()
#      # Normalize common spelling variants
#     text = text.replace("conveyer", "conveyor")
#     text = re.sub(r"[^\w\s]", "", text)
#     return text


# def calculate_score(question, document):
#     """
#     Score a document based on keyword matches.
#     """
#     stop_words = {
#         "how", "do", "i", "is", "are", "the", "a", "an",
#         "what", "when", "where", "why", "can", "should",
#         "to", "of", "for", "in", "on"
#     }

#     question_words = preprocess_text(question).split()

#     # Remove common words
#     question_words = [
#         word for word in question_words
#         if word not in stop_words
#     ]   
#     document = preprocess_text(document)

#     score = 0

#     for word in question_words:
#         if word in stop_words:
#             continue
#         if word in document:
#             # Longer words carry more meaning
#             if len(word) >= 8:
#                 score += 4
#             elif len(word) >= 5:
#                 score += 2
#             else:
#                 score += 1

#     return score


# def retrieve_context(question):
#     """
#         Retrieve the Top 3 most relevant documents.
#         """

#     results = []

#     for filename in os.listdir(KNOWLEDGE_PATH):

#             if not filename.endswith(".txt"):
#                 continue

#             filepath = os.path.join(KNOWLEDGE_PATH, filename)

#             with open(filepath, "r", encoding="utf-8") as file:
#                 content = file.read()

#             score = calculate_score(question, content)

#             print(filename, score)

#             results.append({
#                 "filename": filename,
#                 "score": score,
#                 "content": content
#             })

#         # Sort documents by score
#     results.sort(
#             key=lambda x: x["score"],
#             reverse=True
#         )

#         # Keep only documents with score > 0
#     top_results = [
#             doc for doc in results
#             if doc["score"] > 0
#         ][:3]

#     if not top_results:
#             return {
#                 "context": "",
#                 "score": 0,
#                 "sources": []
#             }

#     combined_context = ""

#     for doc in top_results:

#             combined_context += (
#                 f"\n\nDOCUMENT: {doc['filename']}\n\n"
#             )

#             combined_context += doc["content"]

#     return {
#             "context": combined_context,
#             "score": top_results[0]["score"],
#             "sources": [
#                 doc["filename"]
#                 for doc in top_results
#             ]
#         }


#     # """
#     # Search all knowledge files and return
#     # the most relevant document.
#     # """

#     # best_score = -1
#     # best_document = ""
#     # best_filename = ""

#     # for filename in os.listdir(KNOWLEDGE_PATH):

#     #     if not filename.endswith(".txt"):
#     #         continue

#     #     filepath = os.path.join(KNOWLEDGE_PATH, filename)

#     #     with open(filepath, "r", encoding="utf-8") as file:
#     #         content = file.read()

#     #     score = calculate_score(question, content)
#     #     print(filename, score)  # Temporary debugging

#     #     if score > best_score:
#     #         best_score = score
#     #         best_document = content
#     #         best_filename = filename

#     # return {
#     #     "filename": best_filename,
#     #     "section": "General",
#     #     "score": best_score,
#     #     "context": best_document
#     # }