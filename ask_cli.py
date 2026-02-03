from utils.rag import PaperRAG

if __name__ == "__main__":
    rag = PaperRAG(collection_name="papers")

    pdf_name = input("Enter PDF filename: ").strip()

    while True:
        q = input("\nAsk a question (or type exit): ").strip()
        if q.lower() == "exit":
            break

        if not q:
            print("⚠️ Please type a question.")
            continue

        result = rag.answer(q, top_k=8)

        print("\nANSWER:")
        print(result["answer_clean"])
