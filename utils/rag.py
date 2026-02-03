import os
import re
from groq import Groq
from sentence_transformers import SentenceTransformer
from ingest import ingest_pdf as ingest_pdf_function

from utils.vectordb import get_chroma_collection

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def format_context(results, max_chars_per_chunk=1200):
    """
    Converts chroma results into a context string WITHOUT source/page text.
    Keeps citations metadata separately.
    """
    docs = results["documents"][0]
    metas = results["metadatas"][0]

    context_blocks = []
    citations = []

    for i, (doc, meta) in enumerate(zip(docs, metas), start=1):
        source = meta.get("source", "unknown")
        page = meta.get("page", "?")
        chunk_id = meta.get("chunk_id", "?")

        doc = doc.strip()
        if len(doc) > max_chars_per_chunk:
            doc = doc[:max_chars_per_chunk] + "..."

        tag = f"[{i}]"

        # store metadata separately (not in context)
        citations.append({
            "tag": tag,
            "source": source,
            "page": page,
            "chunk_id": chunk_id
        })

        # context only contains chunk text
        context_blocks.append(f"{tag}\n{doc}")

    context = "\n\n".join(context_blocks)
    return context, citations


class PaperRAG:
    def ingest_pdf(self, pdf_path):
        return ingest_pdf_function(pdf_path)
    
    def __init__(self, collection_name="papers", persist_dir="data/chroma_db"):
        self.collection = get_chroma_collection(collection_name, persist_dir)
        self.embedder = SentenceTransformer(EMBED_MODEL_NAME, local_files_only=True)

        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise ValueError("GROQ_API_KEY not found. Set it in environment variables.")

        self.client = Groq(api_key=groq_key)

    def retrieve(self, query: str, top_k: int = 8, pdf_filter: str = None):
        q_emb = self.embedder.encode([query])[0].tolist()

        where_filter = None
        if pdf_filter:
            where_filter = {"source": pdf_filter}

        results = self.collection.query(
            query_embeddings=[q_emb],
            n_results=max(top_k, 15),
            include=["documents", "metadatas"],
            where=where_filter
        )
        return results



    def answer(self, query: str, top_k: int = 8, model="llama-3.1-8b-instant", pdf_filter: str = None):
        results = self.retrieve(query, top_k=top_k, pdf_filter=pdf_filter)
        context, citations = format_context(results)

        with open("C:\\Users\\Tisha\\OneDrive\\المستندات\\Research Paper summarizer\\utils\\Instructions\\System_instructions.md", "r", encoding="utf-8") as f:
            system_prompt = f.read()

        user_prompt = f"""
You are a research paper assistant.

Use ONLY the context below to answer.
If the context is insufficient, say: "Not enough context from the paper."

Context:
{context}

User question: {query}

Answer:
"""


        completion = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )

        answer_original = completion.choices[0].message.content.strip()

        # remove inline citations like [1], [2]
        answer_clean = re.sub(r"\[\d+\]", "", answer_original)

        # remove "Citations:" or "References:" blocks if model still outputs
        answer_clean = re.sub(
            r"(?is)\n*(citations|references|sources)\s*:.*$", "", answer_clean
        ).strip()

        # normalize spacing
        answer_clean = "\n".join(
            [line.strip() for line in answer_clean.splitlines() if line.strip()]
        )

        # detect citations used from original answer
        citations_used = sorted(set(re.findall(r"\[(\d+)\]", answer_original)), key=int)

        # if model didn't cite anything, fallback to top chunks
        if not citations_used:
            citations_used = [str(i) for i in range(1, min(top_k, len(citations)) + 1)]

        return {
        "query": query,
        "answer_original": answer_original,
        "answer_clean": answer_clean,
    }