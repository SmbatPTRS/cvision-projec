import re
import numpy as np


# Helper functions for text cleaning and processing ====================================================================
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

# =====================================================================================================================

def L2_normalize(vector: list[float]) -> list[float]:
    v = vector / np.linalg.norm(vector) if np.linalg.norm(vector) != 0 else vector
    return  v.tolist()