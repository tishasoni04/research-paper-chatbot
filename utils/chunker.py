def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200):
    """
    Chunk text into word-based overlapping chunks.
    chunk_size and overlap are in WORDS.
    """
    if not text or not text.strip():
        return []

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

        # prevent infinite loop if overlap >= chunk_size
        if overlap >= chunk_size:
            break

    return chunks


def chunk_pages(pages_text, chunk_size: int = 1200, overlap: int = 200):
    """
    pages_text: list[str] (output from pdfplumber extractor)
    Returns list of chunks with page numbers.
    """
    all_chunks = []

    for page_no, text in enumerate(pages_text, start=1):
        page_chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)

        for idx, chunk in enumerate(page_chunks):
            all_chunks.append(
                {
                    "page": page_no,
                    "chunk_id": idx,
                    "text": chunk
                }
            )

    return all_chunks
