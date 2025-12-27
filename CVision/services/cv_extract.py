import fitz  # PyMuPDF
import re

def extract_cv_text(pdf_bytes):
    """Extract and clean text from a PDF byte stream representing a CV."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_blocks = []

    for page_number, page in enumerate(doc, start=1):
        blocks = page.get_text("blocks")  # returns (x0, y0, x1, y1, text, block_no)

        # Sort top-to-bottom, then left-to-right
        blocks = sorted(blocks, key=lambda b: (b[1], b[0]))

        for b in blocks:
            all_blocks.append({
                "page": page_number,
                "x0": b[0],
                "y0": b[1],
                "x1": b[2],
                "y1": b[3],
                "text": b[4].strip()
            })

    # Join all text blocks in order
    full_text = "\n".join([b["text"] for b in all_blocks])
    # print(full_text)


    # ==================== Cleaning =================================================


    # Remove repeated page headers/footers
    text = re.sub(r"Page \d+ of \d+", "", full_text)

    # Remove links, websites
    text = re.sub(r"(https?://\S+|www\.\S+)", "", text)

    # Remove extra newlines
    text = re.sub(r"\n{2,}", "\n", text)

    # Normalize spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Phone number removing
    pattern = r"""
    (
        (\+?374[\s-]?)?          # Optional +374 or 374 country code
        (\(?0?\d{2}\)?[\s-]?)    # Operator code 2 digits with optional 0 and parentheses
        (\d{2,3}[\s-]?\d{2,3}    # Main number part: either 123456, 123 456, 12 34 56
        ([\s-]?\d{2})?)          # Optional last 2 digits if split like 12 34 56
    )
    """

    text = re.sub(pattern, "", text, flags=re.VERBOSE)

    # Regex to remove email addresses
    clean_text = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "", text)

    return clean_text