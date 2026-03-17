import re
import asyncio
from playwright.async_api import async_playwright

# -----------------------------
# REGEX FILTERS
# -----------------------------

REJECT_PATTERNS = [
    r"\b(onsite|on-site|hybrid|in[-\s]?office|local\s+candidates|relocation\s+required|relocate\s+at\s+own\s+expense|commute)\b",
    r"\b(competitive\s+pay|market\s+rate|DOE|commensurate\s+with\s+experience|budget\s+is\s+limited)\b",
    r"\b(junior|jr\.?|mid[-\s]?level|analyst|bi\s+developer|power\s*bi\s+developer|data\s+specialist)\b",
    r"\b(legacy\s+ssis|on[-\s]?prem\s+only|no\s+cloud\s+strategy|exploring\s+azure|learning\s+fabric)\b",
    r"\b(wear\s+many\s+hats|fast[-\s]?paced\s+startup|limited\s+resources|solo\s+data\s+engineer)\b"
]

ACCEPT_PATTERNS = [
    r"\b(principal|senior|sr\.?|lead|staff|architect|head\s+of|director)\b",
    r"\b(fabric|onelake|medallion|delta\s+lake|azure\s+data\s+factory|synapse|pyspark|dataops|ci[-/]cd)\b"
]

# -----------------------------
# SCORING MODEL
# -----------------------------

def score_job(text: str) -> int:
    score = 0

    # Seniority (0–20)
    if re.search(r"\b(principal|staff|architect|lead|senior|sr\.?)\b", text, re.I):
        score += 20

    # Remote (0–20)
    if re.search(r"\b(remote|work\s*from\s*home)\b", text, re.I):
        score += 20
    elif re.search(r"\b(hybrid|onsite|on-site|in office)\b", text, re.I):
        score -= 50

    # Compensation (0–15)
    if re.search(r"\b(\$165|170|180|190|200|220|240|250)k\b", text, re.I):
        score += 15
    elif re.search(r"\bsalary\b", text, re.I):
        score += 5
    elif re.search(r"\b(competitive pay|DOE|market rate)\b", text, re.I):
        score -= 10

    # Modern tech (0–15)
    modern = r"\b(fabric|onelake|medallion|delta lake|synapse|data factory|pyspark|dataops|ci/cd)\b"
    hits = len(re.findall(modern, text, re.I))
    score += min(hits * 3, 15)

    # Role scope (0–10)
    if re.search(r"\b(architect|platform|ownership|strategy|governance|standards)\b", text, re.I):
        score += 10

    # Company maturity (0–10)
    if re.search(r"\b(roadmap|mature|enterprise|governance|data team|modernization)\b", text, re.I):
        score += 10
    elif re.search(r"\b(greenfield|starting|exploring|learning fabric)\b", text, re.I):
        score -= 10

    # Red flags (0–10)
    if re.search(r"\b(relocation|relocate|onsite|hybrid|wear many hats|limited resources|solo data engineer)\b", text, re.I):
        score -= 20
    else:
        score += 10

    return max(0, min(score, 100))


# -----------------------------
# PLAYWRIGHT SCRAPER
# -----------------------------

async def scrape_linkedin_jobs():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto("https://www.linkedin.com/jobs")
        await page.wait_for_load_state("networkidle")

        # Scroll to load more jobs
        for _ in range(10):
            await page.mouse.wheel(0, 2000)
            await page.wait_for_timeout(800)

        job_cards = await page.locator("ul.jobs-search__results-list li").all()

        results = []

        for card in job_cards:
            try:
                title = await card.locator("h3").inner_text()
                company = await card.locator("h4").inner_text()
                location = await card.locator(".job-search-card__location").inner_text()
                url = await card.locator("a").get_attribute("href")

                await card.click()
                await page.wait_for_timeout(500)

                description = await page.locator(".jobs-description-content__text").inner_text()

                text = f"{title} {company} {location} {description}"

                # Reject if any reject pattern matches
                if any(re.search(p, text, re.I) for p in REJECT_PATTERNS):
                    continue

                # Accept only if at least one accept pattern matches
                if not any(re.search(p, text, re.I) for p in ACCEPT_PATTERNS):
                    continue

                job_score = score_job(text)

                results.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": url,
                    "score": job_score,
                    "description": description
                })

            except Exception:
                continue

        await browser.close()
        return results


# -----------------------------
# RUN SCRAPER
# -----------------------------

if __name__ == "__main__":
    jobs = asyncio.run(scrape_linkedin_jobs())
    for job in sorted(jobs, key=lambda x: x["score"], reverse=True):
        print(f"{job['score']} — {job['title']} @ {job['company']} ({job['location']})")
        print(job["url"])
        print("-" * 80)
