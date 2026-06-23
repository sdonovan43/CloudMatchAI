from __future__ import annotations
import argparse
from adapters import get_adapter
from config import load_config
from scorer import Scorer


def run(config_path: str):
    # Load YAML config
    cfg = load_config(config_path) 
    print("DEBUG: Using adapter:", cfg.source.adapter)
    print("DEBUG: Adapter class:", get_adapter(cfg.source))
    # Instantiate adapter
    adapter = get_adapter(cfg.source)

    # Fetch data
    items = adapter.fetch()
    if not items:
        print("No data returned from adapter.")
        return

    # Define weights (could be moved into config later)
    weights = {
        "compute": 0.25,
        "storage": 0.25,
        "egress": 0.20,
        "regions": 0.15,
        "compliance": 0.15,
    }

    scorer = Scorer(weights, llm_enabled=False)

    print(f"\n=== CloudMatchAI Results for Profile: {cfg.profile.name} ===\n")

    for item in items:
        result = scorer.score(item, cfg.profile.criteria)

        print(f"Provider: {item.get('name', 'Unknown')}")
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