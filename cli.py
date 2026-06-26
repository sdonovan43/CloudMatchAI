import asyncio
from pathlib import Path

from config import load_config
from adapters import get_adapter
from scorer import score_entities
from dedupe import dedupe
from storage import store


async def run_pipeline(config_path: str):
    cfg = load_config(config_path)

    adapter = get_adapter(cfg)
    items = await adapter.fetch()

    unique = dedupe(items)
    scored = await score_entities(cfg, unique)

    store(scored, cfg.storage.path)

    print(f"Fetched: {len(items)}")
    print(f"Unique: {len(unique)}")
    print(f"Scored: {len(scored)}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="CloudMatchAI v2.0")
    parser.add_argument("config", type=str, help="Path to YAML config")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    asyncio.run(run_pipeline(str(config_path)))


if __name__ == "__main__":
    main()