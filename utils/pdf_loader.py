import re
import pdfplumber
from collections import Counter


# ============================================================
# 1) CLEAN TEXT
# ============================================================
def clean_text(text: str) -> str:
    """Basic cleanup."""
    if not text:
        return ""
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def is_probably_title(line: str) -> bool:
    """Heuristic to avoid junk titles."""
    if not line:
        return False
    line = line.strip()

    # too short / too long
    if len(line) < 5 or len(line) > 250:
        return False

    # avoid purely numeric or page numbers
    if re.fullmatch(r"[\d\W_]+", line):
        return False

    # avoid lines that look like headers
    bad_patterns = [
        r"^page\s*\d+",
        r"^www\.",
        r"^http",
        r"copyright",
        r"all rights reserved",
        r"^arxiv\b",
    ]
    for pat in bad_patterns:
        if re.search(pat, line, re.IGNORECASE):
            return False

    return True


# ============================================================
# 2) TITLE EXTRACTION USING FONT SIZE
# ============================================================
def extract_title_from_first_page(page) -> str:
    """
    Extract title using font-size heuristic:
    Title is often the text with the largest font on first page.
    """
    words = page.extract_words(extra_attrs=["size", "fontname"])
    if not words:
        return ""

    # group words by approximate font size (rounded)
    for w in words:
        w["size_rounded"] = round(w["size"], 1)

    # pick top font sizes
    size_counts = Counter([w["size_rounded"] for w in words])
    top_sizes = [s for s, _ in size_counts.most_common(4)]  # top 4 sizes

    candidate_lines = []

    for font_size in top_sizes:
        same_size_words = [w for w in words if w["size_rounded"] == font_size]
        if not same_size_words:
            continue

        # sort by vertical then horizontal position
        same_size_words.sort(key=lambda x: (x["top"], x["x0"]))

        # group into lines by "top"
        lines = []
        current_line = []
        current_top = None

        for w in same_size_words:
            if current_top is None or abs(w["top"] - current_top) <= 3:
                current_line.append(w)
                current_top = w["top"] if current_top is None else current_top
            else:
                lines.append(current_line)
                current_line = [w]
                current_top = w["top"]

        if current_line:
            lines.append(current_line)

        # convert lines to text
        for line_words in lines:
            line_words.sort(key=lambda x: x["x0"])
            line_text = " ".join([w["text"] for w in line_words])
            line_text = clean_text(line_text)

            if is_probably_title(line_text):
                candidate_lines.append((font_size, line_text))

        # if found title candidates at largest font size, stop
        if candidate_lines:
            break

    if not candidate_lines:
        return ""

    # Usually the first big heading is the title
    return candidate_lines[0][1]


# ============================================================
# 3) REMOVE REPEATED HEADERS/FOOTERS (OPTIONAL)
# ============================================================
def remove_repeated_headers_footers(pages_text):
    """
    Optional: remove repeated header/footer lines appearing on many pages.
    Works well for papers/reports.
    """
    if len(pages_text) < 3:
        return pages_text

    first_lines = []
    last_lines = []

    for t in pages_text:
        lines = [l.strip() for l in t.splitlines() if l.strip()]
        if not lines:
            first_lines.append("")
            last_lines.append("")
            continue
        first_lines.append(lines[0])
        last_lines.append(lines[-1])

    first_common = Counter(first_lines).most_common(1)[0]
    last_common = Counter(last_lines).most_common(1)[0]

    header = first_common[0] if first_common[1] >= len(pages_text) * 0.6 else None
    footer = last_common[0] if last_common[1] >= len(pages_text) * 0.6 else None

    cleaned_pages = []
    for t in pages_text:
        lines = t.splitlines()
        lines_clean = []
        for l in lines:
            s = l.strip()
            if header and s == header:
                continue
            if footer and s == footer:
                continue
            lines_clean.append(l)
        cleaned_pages.append("\n".join(lines_clean).strip())

    return cleaned_pages


# ============================================================
# 4) MAIN EXTRACTOR FUNCTION
# ============================================================
def extract_pdf_with_pdfplumber(pdf_path: str, remove_headers_footers_flag: bool = True):
    """
    Extracts:
    - title
    - metadata
    - full_text
    - pages_text
    - num_pages
    """
    with pdfplumber.open(pdf_path) as pdf:
        metadata = pdf.metadata or {}

        # Extract text from pages
        pages_text = []
        for page in pdf.pages:
            txt = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
            pages_text.append(clean_text(txt))

        if remove_headers_footers_flag:
            pages_text = remove_repeated_headers_footers(pages_text)

        full_text = "\n\n".join([t for t in pages_text if t.strip()]).strip()

        # ============================================================
        # TITLE EXTRACTION STRATEGY (ROBUST FOR RESEARCH PAPERS)
        # ============================================================

        title = ""

        # ------------------------------------------------------------
        # 1️⃣ FIRST PRIORITY — TEXT BEFORE "ABSTRACT"
        # ------------------------------------------------------------
        if pages_text:
            first_page = pages_text[0]

            if "abstract" in first_page.lower():
                before_abstract = first_page.split("Abstract")[0]
                before_abstract = before_abstract.split("ABSTRACT")[0]

                lines = [
                    l.strip()
                    for l in before_abstract.splitlines()
                    if l.strip()
                ]

                # remove junk lines (emails, affiliations, very short text)
                cleaned_lines = []
                for l in lines:
                    if len(l) < 8:
                        continue
                    if "@" in l:
                        continue
                    if any(x in l.lower() for x in ["university", "department", "lbnl"]):
                        continue
                    cleaned_lines.append(l)

                if cleaned_lines:
                    # usually title is first line(s)
                    title = " ".join(cleaned_lines[:2])

        # ------------------------------------------------------------
        # 2️⃣ SECOND — FONT SIZE HEURISTIC
        # ------------------------------------------------------------
        if not title and pdf.pages:
            title = extract_title_from_first_page(pdf.pages[0])

        # ------------------------------------------------------------
        # 3️⃣ LAST FALLBACK — FIRST MEANINGFUL LINE
        # ------------------------------------------------------------
        if not title and pages_text:
            first_page_lines = [
                l.strip() for l in pages_text[0].splitlines() if l.strip()
            ]

            for l in first_page_lines[:10]:
                if is_probably_title(l):
                    title = l
                    break

        # ------------------------------------------------------------
        # CLEAN TITLE
        # ------------------------------------------------------------
        title = title.replace("- ", "")   # fix hyphenated breaks
        title = title.replace("\n", " ")
        title = clean_text(title)

        return {
            "title": title,
            "metadata": metadata,
            "full_text": full_text,
            "pages_text": pages_text,
            "num_pages": len(pdf.pages),
        }


# ============================================================
# 5) EXAMPLE USAGE
# ============================================================
if __name__ == "__main__":
    pdf_path = "C:\\Users\\Tisha\\OneDrive\\المستندات\\Research Paper summarizer\\data\\pdfs\\A Straightforward Pipeline for Targeted Entailment and Contradiction Detection.pdf"

    result = extract_pdf_with_pdfplumber(pdf_path)

    print("TITLE:", result["title"])
    print("PAGES:", result["num_pages"])
    print("\n--- First 800 chars ---\n")
    print(result["full_text"][:800])