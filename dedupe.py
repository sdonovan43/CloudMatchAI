import hashlib
import json


def _hash_item(item: dict) -> str:
    """
    Compute a stable SHA-256 hash of the entire item.
    Ensures dedupe works for any entity type.
    """
    raw = json.dumps(item, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def dedupe(items: list[dict]) -> list[dict]:
    """
    Return a list of unique items based on full-item hashing.
    No assumptions about fields or structure.
    """
    seen = set()
    unique = []

    for item in items:
        h = _hash_item(item)
        if h not in seen:
            seen.add(h)
            unique.append(item)

    return unique