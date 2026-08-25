from __future__ import annotations
import json
from pathlib import Path
from typing import Any


def _get_overall_score(item: dict[str, Any]) -> float:
    """
    Pulls the overall score out of an item's _match_analysis block for
    sorting. Handles the different key names that have shown up across
    scorer.py's history (overall_score is current/expected; the others
    are defensive fallbacks for older or malformed entries). Items that
    failed scoring (no usable score) sort to the bottom via -1.
    """
    analysis = item.get("_match_analysis", {})
    if "error" in analysis and "overall_score" not in analysis:
        return -1.0
    return analysis.get("overall_score", analysis.get("total_weighted_score", analysis.get("score", -1.0)))


def store(data: list[dict[str, Any]], path: str, min_score: float | None = None) -> None:
    """
    Saves the scored and ranked entity results to a JSON file, sorted by
    overall_score descending (best matches first). If min_score is set,
    items scoring below it (or that failed scoring entirely) are dropped
    before saving. Automatically creates any missing parent directories.
    """
    if not path:
        print("STORAGE ERROR: Provided storage path is empty. Falling back to 'output.json'")
        path = "output.json"

    working_data = data
    if min_score is not None:
        before_count = len(working_data)
        working_data = [item for item in working_data if _get_overall_score(item) >= min_score]
        dropped = before_count - len(working_data)
        if dropped:
            print(f"STORAGE: Filtered out {dropped} item(s) scoring below {min_score}.")

    sorted_data = sorted(working_data, key=_get_overall_score, reverse=True)

    output_path = Path(path)

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(sorted_data, f, indent=4, ensure_ascii=False)

        print(f"SUCCESS: Pipeline results successfully saved to {output_path.resolve()}")

    except Exception as e:
        print(f"STORAGE ERROR: Failed to write data to '{path}'. Reason: {e}")