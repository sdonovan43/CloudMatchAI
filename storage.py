from __future__ import annotations
import json
from pathlib import Path
from typing import Any


def store(data: list[dict[str, Any]], path: str) -> None:
    """
    Saves the scored and ranked entity results to a JSON file.
    Automatically creates any missing parent directories.
    """
    if not path:
        print("STORAGE ERROR: Provided storage path is empty. Falling back to 'output.json'")
        path = "output.json"

    output_path = Path(path)

    try:
        # Automatically create directory structures if they don't exist yet
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write out with clean indentation for readability
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"SUCCESS: Pipeline results successfully saved to {output_path.resolve()}")

    except Exception as e:
        print(f"STORAGE ERROR: Failed to write data to '{path}'. Reason: {e}")