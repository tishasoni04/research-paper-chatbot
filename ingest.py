import os
import re
import fitz  # PyMuPDF
from utils.vectordb import get_chroma_collection
from sentence_transformers import SentenceTransformer

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_pdf_pages(pdf_path: str):
    doc = fitz.open(pdf_path)
    pages = []

    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text("text")
        text = clean_text(text)

        if text:
            pages.append({"page": i + 1, "text": text})

    return pages


def chunk_text(text: str, chunk_size=800, overlap=150):
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def ingest_pdf(pdf_path: str, collection_name="papers", persist_dir="data/chroma_db"):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    collection = get_chroma_collection(collection_name, persist_dir)
    embedder = SentenceTransformer(EMBED_MODEL_NAME)

    pages = load_pdf_pages(pdf_path)
    source_name = os.path.basename(pdf_path)

    all_texts = []
    all_metas = []
    all_ids = []

    chunk_global_id = 0

    for p in pages:
        page_no = p["page"]
        chunks = chunk_text(p["text"])

        for ci, chunk in enumerate(chunks):
            chunk_global_id += 1
            all_texts.append(chunk)

            all_metas.append({
                "source": source_name,
                "page": page_no,
                "chunk_id": ci
            })

            all_ids.append(f"{source_name}_p{page_no}_c{ci}_{chunk_global_id}")

    embeddings = embedder.encode(all_texts).tolist()

    collection.add(
        documents=all_texts,
        metadatas=all_metas,
        ids=all_ids,
        embeddings=embeddings
    )

    print(f"\n✅ Ingested PDF: {source_name}")
    print(f"📄 Pages extracted: {len(pages)}")
    print(f"🧩 Total chunks stored: {len(all_texts)}")


if __name__ == "__main__":
    pdf_path = input("Enter PDF file path: ").strip()
    ingest_pdf(pdf_path)
