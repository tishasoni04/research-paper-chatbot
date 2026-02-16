import os
from rag import PaperRAG
from ingest import generate_doc_id

if __name__ == "__main__":

    pdf_name = input("Enter PDF file path: ").strip()

    if not os.path.exists(pdf_name):
        raise FileNotFoundError("Research Paper does not exist")

    # generate unique document id
    doc_id = generate_doc_id(pdf_name)

    # create RAG bound to this document
    rag = PaperRAG(collection_name="papers", doc_id=doc_id)

    # prevent re-indexing
    existing = rag.collection.get(where={"doc_id": doc_id})

    if existing["ids"]:
        print("\n📄 Document already indexed. Using existing document.")
    else:
        rag.ingest_pdf(pdf_name)

    print("\n📌 Active Document:", os.path.basename(pdf_name))
    print("🆔 Document ID:", doc_id)

    print("\n✅ Research paper ready.")
    print("You can now ask questions about THIS paper only.")
    print("Type 'exit' to quit.")

    while True:
        q = input("\nAsk a question: ").strip()

        if q.lower() == "exit":
            break

        if not q:
            print("Please type a question.")
            continue

        result = rag.answer(q, top_k=8)

        print("\nANSWER:")
        print(result["answer_original"])
