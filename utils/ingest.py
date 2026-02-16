import os
import uuid
from pdf_loader import extract_pdf_with_pdfplumber
import hashlib

from vectordb import get_chroma_collection
from sentence_transformers import SentenceTransformer
from pdf_loader import extract_pdf_with_pdfplumber
from chunker import chunk_text

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def generate_doc_id(pdf_path):
    with open(pdf_path, "rb") as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    return file_hash[:16] 

def ingest_pdf(pdf_path: str, collection_name="papers", persist_dir="data/chroma_db"):
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    collection = get_chroma_collection(collection_name, persist_dir)
    embedder = SentenceTransformer(EMBED_MODEL_NAME)

    pdf_data = extract_pdf_with_pdfplumber(pdf_path)
    pages_text = pdf_data["pages_text"]
    title = pdf_data["title"]
    print("EXTRACTED TITLE:", title)

    source_name = os.path.basename(pdf_path)
    doc_id = generate_doc_id(pdf_path)   # ⭐ NEW

    all_texts = []
    all_metas = []
    all_ids = []

    chunk_global_id = 0

    for page_no, text in enumerate(pages_text, start=1):
        chunks = chunk_text(text)

        for ci, chunk in enumerate(chunks):
            chunk_global_id += 1
            all_texts.append(chunk)

            all_metas.append({
                "source": source_name,
                "doc_id": doc_id,
                "title": title,   # ⭐ ADD THIS
                "page": page_no,
                "chunk_id": ci
            })


            all_ids.append(f"{doc_id}_p{page_no}_c{ci}_{chunk_global_id}")

    embeddings = embedder.encode(all_texts).tolist()

    collection.add(
        documents=all_texts,
        metadatas=all_metas,
        ids=all_ids,
        embeddings=embeddings
    )

    print(f"\n✅ Ingested PDF: {source_name}")
    print(f"🆔 Document ID: {doc_id}")
    print(f"📄 Pages extracted: {len(pages_text)}")
    print(f"🧩 Total chunks stored: {len(all_texts)}")

if __name__ == "__main__":
    pdf_path = input("Enter PDF path: ")
    ingest_pdf(pdf_path)
