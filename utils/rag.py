import os
import re
from groq import Groq
from sentence_transformers import SentenceTransformer
from ingest import ingest_pdf as ingest_pdf_function
from vectordb import get_chroma_collection

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def format_context(results, max_chars_per_chunk=1200):
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

        citations.append({
            "tag": tag,
            "source": source,
            "page": page,
            "chunk_id": chunk_id
        })

        context_blocks.append(f"{tag}\n{doc}")

    context = "\n\n".join(context_blocks)
    return context, citations


class PaperRAG:
    def ingest_pdf(self, pdf_path):
        return ingest_pdf_function(pdf_path)

    def __init__(self, collection_name="papers", doc_id=None, persist_dir="data/chroma_db"):
        self.collection = get_chroma_collection(collection_name, persist_dir)
        self.embedder = SentenceTransformer(EMBED_MODEL_NAME, local_files_only=True)
        self.doc_id = doc_id

        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            raise ValueError("GROQ_API_KEY not found. Set it in environment variables.")

        self.client = Groq(api_key=groq_key)

    def retrieve(self, query, top_k=5):
        if not self.doc_id:
            raise ValueError("doc_id is required for retrieval")

        query_embedding = self.embedder.encode([query]).tolist()[0]

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where={"doc_id": self.doc_id}
        )

        return results
    
    def get_document_title(self):
        results = self.collection.get(
            where={"doc_id": self.doc_id},
            limit=1
        )

        if results["metadatas"]:
            return results["metadatas"][0].get("title", "Not found")

        return "Not found"


    def answer(self, query: str, top_k: int = 8, model="llama-3.1-8b-instant"):

        # ⭐ STEP 1 — intercept title queries FIRST
        title_patterns = [
            "title",
            "paper title",
            "title of the paper"
        ]

        if query.lower().strip() in title_patterns:
            title = self.get_document_title()
            return {
                "query": query,
                "answer_original": f"Title: {title}",
                "answer_clean": f"Title: {title}",
            }

        # ⭐ STEP 2 — normal retrieval flow continues
        results = self.retrieve(query, top_k=top_k)
        context, citations = format_context(results)

        with open(
            "C:\\Users\\Tisha\\OneDrive\\المستندات\\Research Paper summarizer\\utils\\Instructions\\System_instructions.md",
            "r",
            encoding="utf-8"
        ) as f:
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

        answer_clean = re.sub(r"\[\d+\]", "", answer_original)
        answer_clean = re.sub(
            r"(?is)\n*(citations|references|sources)\s*:.*$", "",
            answer_clean
        ).strip()

        answer_clean = "\n".join(
            [line.strip() for line in answer_clean.splitlines() if line.strip()]
        )

        return {
            "query": query,
            "answer_original": answer_original,
            "answer_clean": answer_clean,
        }

