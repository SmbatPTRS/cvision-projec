import asyncio
import logging
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from models.job_models import JobDetails
from models.model_loader import model
from db.db import insert_job, pool
from utils.helpers import clean_text, get_requirements, get_responsibilities
from utils.logging_config import logger


async def scrape_job_links(page,job_set_size):
    job_links = set()

    BASE_URL = "https://staff.am"
    url = f"{BASE_URL}/am/jobs"

    async with async_playwright() as p:
            await page.goto(url)

            while True:

                content = await page.content() # Get page content after scrolling as HTML
                soup = BeautifulSoup(content, 'html.parser') # Parse HTML with BeautifulSoup to make searching easier

                # Extract job links containing '/am/jobs/'
                new_links = [BASE_URL + a["href"] for a in soup.find_all("a", href=True) if "/am/jobs/" in a["href"]]
                job_links.update(new_links) # Add found links to job_links set

                current_page =  page.locator('ul li.active')
                next_page = page.locator('ul li.active + li a')

                # if len(job_links) < job_set_size:
                #     await next_page.click()
                #     await asyncio.sleep(2)
                # else:
                #     break


            return job_links

async def scrape_job_details(page, job_url, model):
    """Scrape job details from a given job URL(title, requirements, responsibilities, etc.)"""
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

    return JobDetails(**job_details),all_text

def save_job_to_db(job_details: JobDetails):
    try:
        insert_job(job_details)
    except Exception as e:
        logger.info(f"Error inserting job into DB: {e}")

async def main():


    async with async_playwright() as p:

        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Example usage
        job_links = await scrape_job_links(page,30)
        logger.info(len(job_links))

        jobs=[]
        texts=[]

        for url in job_links:
            try:
                job_details,all_text = await scrape_job_details(page, url, model)
                jobs.append(job_details)
                texts.append(all_text)
                save_job_to_db(job_details)
            except Exception as e:
                logger.error(f"Error processing job {url}: {e}")

        embeddings = model.encode(
            texts,
            batch_size=32,
            convert_to_tensor=False,
            normalize_embeddings=True
        )

        for job, emb in zip(jobs, embeddings):
            job.embedding = emb.tolist()

        # Save to DB
        for job in jobs:
            save_job_to_db(job)

        pool.closeall()
        await browser.close()




if __name__ == "__main__":
    try:
        asyncio.run(main())  # Use asyncio.run() only when running directly
    except RuntimeError as e:
        if "asyncio.run()" in str(e):
            print("Detected running event loop. Use 'await main()' instead.")





