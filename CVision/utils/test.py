import re
import fitz
import asyncio
import numpy as np
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from scipy.spatial.distance import cosine
from sentence_transformers import SentenceTransformer


model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

def make_list(text: str) -> list[str]:
    return [clean_text(text_item.strip()) for text_item in text.split('\n') if text_item.strip()]
def clean_text(text: str) -> str:
    return normalize_whitespace(remove_line_endings(text))
def normalize_whitespace(text: str) -> str:
    return re.sub(r"[^\S\n]+", " ", text or "").strip()
def remove_line_endings(text: str) -> str:
    return re.sub(r"^[-•]|[-՝,;:]$", "", text or "").strip()
def get_responsibilities(soup) -> list[str] | None:
    responsibilities = None
    resp_section_names = ['Աշխատանքային պարտականություններ', 'Job responsibilities']

    resp_section = soup.find('div', string=lambda text: text and text in resp_section_names)

    if resp_section:
        sibling_div = resp_section.find_next_sibling("div")

        if sibling_div:
            ul = sibling_div.find("ul")

            if ul:
                return [clean_text(li.text) for li in ul.find_all("li")]

            else:
                print("No unordered list found in sibling div.")

                return make_list(sibling_div.text)
        else:
            print("No sibling div found for responsibilities section.")
    else:
        print("Responsibilities section not found.")

    return responsibilities

def get_requirements(soup) -> list[str] | None:
    requirements = None
    req_section_names = ['Required qualifications', 'Անհրաժեշտ հմտություններ']
    req_section = soup.find('div', string=lambda text: text and text in req_section_names)

    if req_section:
        sibling_div = req_section.find_next_sibling("div")

        if sibling_div:
            ul = sibling_div.find("ul")

            if ul:
                return [clean_text(li.text) for li in ul.find_all("li")]
            else:
                print("No unordered list found in sibling div.")

                return make_list(sibling_div.text)
        else:
            print("No sibling div found for requirements section.")
    else:
        print("Requirements section not found.")

    return requirements

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

async def scrape_job_details(job_url):

    """Scrape job details from a given job URL(title, requirements, responsibilities, etc.)"""
    async with async_playwright() as p:
        print("Starting job scraping...")

        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto(job_url)

        await page.wait_for_timeout(3000)
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')

        # Lists of possible section names in both Armenian and English in Website
        skill_section_names = ['Professional Skills', 'Մասնագիտական Հմտություններ']
        category_names = ['Category', 'Կատեգորիա']
        work_cond_names = ['Employment term', 'Աշխատանքի պայմաններ']
        seniority_names = ['Required candidate level', 'Պահանջվող թեկնածուի մակարդակը']

        skill_section = soup.find('div', string=lambda text: text and text in skill_section_names)

        # Extracting job details into a dictionary
        job_details = {
            "url": job_url,
            "title": soup.find('h1', class_='css-146c3p1').text.strip(),
            "company": soup.find_all("a", href=lambda href: href and "/company/" in href)[1].text.strip(),
            "country": soup.find('img', srcset=lambda src: src and "locationGreenBig.png" in src).parent.find_next_sibling('div').text.strip(),
            "category": soup.find('div', string=lambda text: text and clean_text(text.strip()) in category_names).find_next_sibling('a').get_text().strip(),
            "employment_type": soup.find('img',srcset=lambda src: src and "greenClockBig.png" in src).parent.find_next_sibling('div').text.strip(),
            "employment_term": soup.find('div', string=lambda text: text and clean_text(text) in work_cond_names).find_next_sibling('div').text.strip(),
            "seniority": soup.find('div', string=lambda text: text and text in seniority_names).find_next_sibling('div').text.strip(),
            "responsibilities": get_responsibilities(soup),
            "requirements": get_requirements(soup),
            "skills": skill_section.find_next_sibling("div").get_text(",").split(",") if skill_section else [],
        }

        # Combine all text for embedding
        parts = [
            job_details["title"],
            job_details["company"],
            job_details["country"],
            job_details["category"],
            job_details["seniority"],
            job_details["employment_type"],
            job_details["employment_term"],
            "Responsibilities: " + ", ".join(job_details["responsibilities"] or []),
            "Requirements: " + ", ".join(job_details["requirements"] or []),
            "Skills: " + ", ".join(job_details["skills"] or []),
        ]
        all_text = "\n".join(parts)

        # Generate embedding
        job_details["embedding"] = model.encode(all_text, convert_to_tensor=False)

        return job_details

with open("S.pdf", "rb") as file:
    # Read file bytes
    pdf_bytes = file.read()

    cv_text = extract_cv_text(pdf_bytes)

    cv_embedding = model.encode(cv_text, convert_to_tensor=False)

    job_details = asyncio.run(scrape_job_details("https://staff.am/am/jobs/software-development/software-developer-233"))


    # Flatten the embeddings to ensure they are 1-D
    job_embedding = np.array(job_details['embedding']).flatten()
    cv_embedding = np.array(cv_embedding).flatten()

    # Compute cosine distance
    cosine_distance = cosine(job_embedding, cv_embedding)

    print(f"Similarity: {1 - cosine_distance}")
