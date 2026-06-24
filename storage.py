import json
from pathlib import Path


def store(items: list[dict], path: str | Path = None):
    """
    Store scored items to a JSON file.
    Path is provided by YAML config.
    """
    if path is None:
        raise ValueError("Storage path must be provided by config.")

    path = Path(path)
    path.write_text(json.dumps(items, indent=2))
