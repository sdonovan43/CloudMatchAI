"""
Runs exactly ONE entity through the scoring pipeline using test.match.yaml.
This lets you check whether Gemini is still rate-limiting you without
burning multiple requests testing it.

Usage:
    python test_single_item.py
"""
import asyncio
from config import load_config
from scorer import score_entities


async def main():
    cfg = load_config("test.match.yaml")

    # Just one minimal item — matches the criteria in test.match.yaml (compute, storage)
    single_item = [
        {
            "name": "AWS",
            "compute": "high",
            "storage": "high",
        }
    ]

    print(f"Sending 1 item to provider: {cfg.llm.provider} / model: {cfg.llm.model}")
    results = await score_entities(cfg, single_item)

    print("\n=== RESULT ===")
    print(results)


if __name__ == "__main__":
    asyncio.run(main())