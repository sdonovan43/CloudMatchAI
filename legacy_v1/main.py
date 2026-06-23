from dotenv import load_dotenv
load_dotenv()

from scraper import get_jobs
from dedupe import dedupe_job
from storage import init_storage, save_job, get_top_jobs

def main():
    print("=== CloudMatchAI ===\n")

    print("[*] Initializing storage...")
    init_storage()

    print("[*] Running scraper...")
    results = get_jobs()
    print(f"[*] Total scraped: {len(results)} jobs\n")

    saved = 0
    for job in results:
        if dedupe_job(job):
            save_job(job)
            saved += 1

    print(f"[+] Saved {saved} new unique jobs\n")
    print("=== Top Matches ===\n")

    for row in get_top_jobs(limit=10):
        title, company, location, url, score, scraped_at = row
        print(f"  Score {score:>3} | {title} @ {company}")
        print(f"           {location}")
        print(f"           {url}\n")

if __name__ == "__main__":
    main()
