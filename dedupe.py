import re
import hashlib
from storage import BACKEND
from storage import sqlite_get_top, cosmos_get_top

# ---------------------------------------------------------
# URL HASHING (primary dedupe key)
# ---------------------------------------------------------

def hash_url(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


# ---------------------------------------------------------
# TITLE NORMALIZATION
# Removes fluff like "Sr.", "Lead", punctuation, etc.
# ---------------------------------------------------------

def normalize_title(title: str) -> str:
    title = title.lower()
    title = re.sub(r"\b(sr|senior|lead|principal|staff|architect)\b", "", title)
    title = re.sub(r"[^a-z0-9 ]", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


# ---------------------------------------------------------
# CHECK IF JOB EXISTS (by URL hash)
# ---------------------------------------------------------

def job_exists(url: str) -> bool:
    url_hash = hash_url(url)

    if BACKEND == "cosmos":
        jobs = cosmos_get_top(limit=5000)
        return any(hash_url(j["url"]) == url_hash for j in jobs)

    rows = sqlite_get_top(limit=5000)
    return any(hash_url(r[3]) == url_hash for r in rows)


# ---------------------------------------------------------
# DEEP DUPLICATE CHECK
# Matches by:
# - URL hash
# - Normalized title + company
# ---------------------------------------------------------

def is_duplicate(job: dict) -> bool:
    title_norm = normalize_title(job["title"])
    company = job["company"].lower()

    if BACKEND == "cosmos":
        jobs = cosmos_get_top(limit=5000)
        for j in jobs:
            if hash_url(j["url"]) == hash_url(job["url"]):
                return True
            if normalize_title(j["title"]) == title_norm and j["company"].lower() == company:
                return True
        return False

    rows = sqlite_get_top(limit=5000)
    for r in rows:
        existing_title = normalize_title(r[0])
        existing_company = r[1].lower()
        existing_url = r[3]

        if hash_url(existing_url) == hash_url(job["url"]):
            return True
        if existing_title == title_norm and existing_company == company:
            return True

    return False


# ---------------------------------------------------------
# MAIN ENTRYPOINT
# Returns True if job should be saved
# ---------------------------------------------------------

def dedupe_job(job: dict) -> bool:
    if is_duplicate(job):
        return False
    return True
