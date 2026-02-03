import fitz  # PyMuPDF
import re


def clean_text(text: str) -> str:
    # remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def load_pdf_pages(pdf_path: str):
    """
    Returns list of dict:
    [{"page": 1, "text": "..."}]
    """
    doc = fitz.open(pdf_path)
    pages = []

    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text("text")
        text = clean_text(text)

        if text:
            pages.append({"page": i + 1, "text": text})

    return pages

if __name__ == "__main__":
    pdf_path = "C:\Users\Tisha\OneDrive\المستندات\Research Paper summarizer\data\pdfs\A Straightforward Pipeline for Targeted Entailment and Contradiction Detection.pdf"   # change to your pdf name
    pages = load_pdf_pages(pdf_path)

    print("Total pages extracted:", len(pages))

    # Print first page preview
    if pages:
        print("\n--- PAGE 1 TEXT (first 500 chars) ---")
        print(pages[0]["text"][:500])

