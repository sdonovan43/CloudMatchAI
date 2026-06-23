from __future__ import annotations
import argparse
from adapters import get_adapter
from config import load_config
from scorer import score_entities


def run(config_path: str):
    # Load YAML config
    cfg = load_config(config_path)

    print("DEBUG: Using adapter:", cfg.source.adapter)
    print("DEBUG: Adapter class:", get_adapter(cfg))


    # Instantiate adapter
    adapter = get_adapter(cfg)


    # Fetch data
    items = adapter.fetch()
    if not items:
        print("No data returned from adapter.")
        return

    print(f"\n=== CloudMatchAI Results for Profile: {cfg.profile.name} ===\n")

    # Run scoring engine (new unified function)
    results = score_entities(cfg, items)

    # Print results
    for result in results:
        entity = result["entity"]
        print(f"Provider: {entity.get('name', 'Unknown')}")
        print(f"Score: {result['score']}")
        print("Breakdown:")
        for k, v in result["breakdown"].items():
            print(f"  - {k}: {v}")
        print("Explanation:")
        print(result["explanation"])
        print("-" * 40)


def main():
    parser = argparse.ArgumentParser(description="CloudMatchAI v2.0 CLI")
    parser.add_argument("config", help="Path to YAML config file")
    config_path = parser.parse_args().config
    run(config_path)


if __name__ == "__main__":
    main()
