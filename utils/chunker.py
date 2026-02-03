def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200):
    """
    Simple word-based chunking.
    chunk_size and overlap are in WORDS.
    """
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk = " ".join(chunk_words).strip()

        if chunk:
            chunks.append(chunk)

        start = end - overlap  # overlap

        if start < 0:
            start = 0

    return chunks


def chunk_pages(pages, chunk_size: int = 1200, overlap: int = 200):
    """
    Input: [{"page": 1, "text": "..."}]
    Output: [{"page": 1, "chunk_id": 0, "text": "..."}]
    """
    all_chunks = []

    for page_data in pages:
        page_no = page_data["page"]
        text = page_data["text"]

        chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)

        for idx, chunk in enumerate(chunks):
            all_chunks.append(
                {
                    "page": page_no,
                    "chunk_id": idx,
                    "text": chunk
                }
            )

    return all_chunks
