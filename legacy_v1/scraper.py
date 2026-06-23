import asyncio
import random
from datetime import datetime
from playwright.async_api import async_playwright

KEYWORDS = {
    "azure": 15, "aws": 15, "gcp": 15, "terraform": 15,
    "kubernetes": 15, "k8s": 15, "bicep": 15, "arm template": 15,
    "cloud": 10, "docker": 10, "devops": 10, "infrastructure": 10,
    "architect": 10, "platform engineer": 10, "sre": 10,
    "ci/cd": 5, "site reliability": 5, "ansible": 5, "jenkins": 5,
}

REMOTE_KEYWORDS = ["remote", "work from home", "wfh", "anywhere", "fully remote"]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

STEALTH_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
window.chrome = { runtime: {} };
"""


def score_job(job: dict) -> int:
    score = 0
    text = f"{job['title']} {job['description']} {job['location']}".lower()

    for kw, pts in KEYWORDS.items():
        if kw in text:
            score += pts

    for rk in REMOTE_KEYWORDS:
        if rk in text:
            score += 25
            break

    try:
        delta = datetime.utcnow() - datetime.fromisoformat(job.get("scraped_at", ""))
        if delta.days == 0:
            score += 20
        elif delta.days <= 3:
            score += 10
    except Exception:
        pass

    return score


async def new_stealth_page(browser):
    ua = random.choice(USER_AGENTS)
    context = await browser.new_context(
        user_agent=ua,
        viewport={"width": 1280, "height": 800},
        locale="en-US",
        timezone_id="America/New_York",
    )
    page = await context.new_page()
    await page.add_init_script(STEALTH_SCRIPT)
    return page, context


async def scrape_indeed(browser, query="cloud azure engineer", location="United States", max_jobs=20):
    jobs = []
    page, context = await new_stealth_page(browser)
    try:
        url = f"https://www.indeed.com/jobs?q={query.replace(' ', '+')}&l={location.replace(' ', '+')}"
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(random.randint(2000, 4000))
        cards = await page.query_selector_all("[data-jk]")
        for card in cards[:max_jobs]:
            try:
                title_el   = await card.query_selector("h2 span")
                company_el = await card.query_selector("[data-testid='company-name']")
                loc_el     = await card.query_selector("[data-testid='text-location']")
                desc_el    = await card.query_selector(".job-snippet")
                job_key    = await card.get_attribute("data-jk")
                job = {
                    "title":       (await title_el.inner_text()).strip()  if title_el   else "Unknown",
                    "company":     (await company_el.inner_text()).strip() if company_el else "Unknown",
                    "location":    (await loc_el.inner_text()).strip()     if loc_el     else "Unknown",
                    "url":         f"https://www.indeed.com/viewjob?jk={job_key}",
                    "description": (await desc_el.inner_text()).strip()    if desc_el    else "",
                    "score":       0,
                    "scraped_at":  datetime.utcnow().isoformat()
                }
                job["score"] = score_job(job)
                jobs.append(job)
                await asyncio.sleep(random.uniform(0.3, 0.8))
            except Exception:
                continue
    except Exception as e:
        print(f"[Indeed] Error: {e}")
    finally:
        await context.close()
    return jobs


async def scrape_linkedin(browser, query="cloud azure engineer", location="United States", max_jobs=20):
    jobs = []
    page, context = await new_stealth_page(browser)
    try:
        url = f"https://www.linkedin.com/jobs/search/?keywords={query.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(random.randint(2000, 4000))
        cards = await page.query_selector_all(".base-card")
        for card in cards[:max_jobs]:
            try:
                title_el   = await card.query_selector(".base-search-card__title")
                company_el = await card.query_selector(".base-search-card__subtitle")
                loc_el     = await card.query_selector(".job-search-card__location")
                link_el    = await card.query_selector("a.base-card__full-link")
                href       = await link_el.get_attribute("href") if link_el else ""
                job = {
                    "title":       (await title_el.inner_text()).strip()   if title_el   else "Unknown",
                    "company":     (await company_el.inner_text()).strip()  if company_el else "Unknown",
                    "location":    (await loc_el.inner_text()).strip()      if loc_el     else "Unknown",
                    "url":         href.split("?")[0] if href else "",
                    "description": "",
                    "score":       0,
                    "scraped_at":  datetime.utcnow().isoformat()
                }
                job["score"] = score_job(job)
                jobs.append(job)
                await asyncio.sleep(random.uniform(0.3, 0.8))
            except Exception:
                continue
    except Exception as e:
        print(f"[LinkedIn] Error: {e}")
    finally:
        await context.close()
    return jobs


async def run_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        print("[*] Scraping Indeed...")
        indeed_jobs = await scrape_indeed(browser)
        print(f"    -> {len(indeed_jobs)} jobs found")
        print("[*] Scraping LinkedIn...")
        linkedin_jobs = await scrape_linkedin(browser)
        print(f"    -> {len(linkedin_jobs)} jobs found")
        await browser.close()
        return indeed_jobs + linkedin_jobs


def get_jobs():
    return asyncio.run(run_scraper())
