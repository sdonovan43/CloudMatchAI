import hashlib
import json


def _hash_item(item: dict) -> str:
    """
    Compute a stable SHA-256 hash of the entire item.
    Used as the fallback dedupe key for entity types that don't have
    a more specific identity (e.g. cloud providers, generic entities).
    """
    raw = json.dumps(item, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def _dedupe_key(item: dict) -> str:
    """
    Picks the best available identity key for an item.

    Job listings (from adapters like Adzuna) commonly get re-posted per
    city under one requisition — same title, same company, same
    description, different `location`. A full-item hash treats those as
    distinct because the location field differs, even though they're the
    same underlying opportunity. When an item looks like a job listing
    (has both `title` and `company`), dedupe on those two fields instead
    so re-posted-per-city listings collapse into one entry.

    Anything without that shape (cloud providers, generic entities) falls
    back to the original full-item hash — unchanged behavior.
    """
    if "title" in item and "company" in item:
        title = (item.get("title") or "").strip().lower()
        company = (item.get("company") or "").strip().lower()
        return f"title_company::{title}::{company}"

    return _hash_item(item)


def dedupe(items: list[dict]) -> list[dict]:
    """
    Return a list of unique items. Uses a job-aware identity key when the
    item looks like a job listing (title + company), otherwise falls back
    to full-item hashing — same as before.
    """
    seen = set()
    unique = []

    for item in items:
        key = _dedupe_key(item)
        if key not in seen:
            seen.add(key)
            unique.append(item)

    return unique