import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

from config import load_config
from adapters import get_adapter
from scorer import score_entities
from dedupe import dedupe
from storage import store, _get_overall_score


def publish_results(cfg, scored: list[dict], publish_dir: str) -> None:
    """
    Writes the scored results out to a folder meant to be served as a static
    site (e.g. GitHub Pages via /docs or a subpage of it). Writes two files:
      - results.json       the scored entity data, read by index.html
      - results.meta.json  profile name/description/timestamp for the header
    Does NOT touch index.html itself — that stays hand-authored in the repo.
    """
    out_dir = Path(publish_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    results_path = out_dir / "results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(scored, f, indent=4, ensure_ascii=False)

    meta = {
        "name": cfg.profile.name,
        "description": cfg.profile.description,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    meta_path = out_dir / "results.meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=4, ensure_ascii=False)

    print(f"PUBLISH: Wrote {results_path} and {meta_path}")
    print(f"PUBLISH: Commit and push the '{publish_dir}/' folder to update GitHub Pages.")


async def run_pipeline(config_path: str, publish_dir: str | None = None):
    cfg = load_config(config_path)

    print("\n", "="*60)
    print(f"CloudMatchAI v2 Pipeline Execution")
    print("="*60)
    print(f"Profile: {cfg.profile.name}")
    print(f"Description: {cfg.profile.description[:80]}{'...' if len(cfg.profile.description) > 80 else ''}")
    print("="*60)

    adapter = get_adapter(cfg)
    print("\n📥 Fetching data...")
    items = await adapter.fetch()
    print(f"✅ Fetched {len(items)} items from {cfg.source.adapter} source")

    print("\n🔍 Deduplicating entities...")
    unique = dedupe(items)
    print(f"✅ Deduplication complete: {len(unique)} unique items")

    print("\n🧠 Scoring items with LLM...")
    scored = await score_entities(cfg, unique)
    print(f"✅ Scoring complete: {len(scored)} items scored")

    print("\n💾 Saving results...")
    store(scored, cfg.storage.path, min_score=cfg.storage.min_score)
    print(f"✅ Results saved to '{cfg.storage.path}'")

    if publish_dir:
        # Publish uses the same min_score filter and sort order as the
        # local save, applied fresh here since this receives the full
        # `scored` list, not whatever store() already filtered internally.
        publish_scored = scored
        if cfg.storage.min_score is not None:
            publish_scored = [
                item for item in scored
                if _get_overall_score(item) >= cfg.storage.min_score
            ]
        publish_scored = sorted(publish_scored, key=_get_overall_score, reverse=True)
        publish_results(cfg, publish_scored, publish_dir)
        print(f"✅ Published results to '{publish_dir}'")

    print("\n" + "="*60)
    print("📊 PIPELINE SUMMARY")
    print("="*60)
    print(f"📥 Fetched:  {len(items):>5} items")
    print(f"🔍 Deduped:  {len(unique):>5} items")  
    print(f"🧠 Scored:   {len(scored):>5} items")
    print("="*60)

    # Show top 3 results if any scored items exist
    if scored:
        print("\n🏆 TOP SCORED RESULTS")
        print("─"*60)
        for i, item in enumerate(scored[:3]):  # Show top 3
            analysis = item.get('_match_analysis', {})
            score = analysis.get('overall_score', -1)
            if score >= 0:
                print(f"{i+1}. {item.get('name', 'Unknown')}")
                print(f"   Score: {score:.2f}")
                # Show key criteria scores in a compact way
                scores = analysis.get('scores', {})
                if scores:
                    score_items = [f'{k}: {v:.1f}' for k, v in list(scores.items())[:3]]  # Show first 3 criteria
                    print(f"   Criteria: {', '.join(score_items)}")
            else:
                print(f"   Error: {analysis.get('error', 'Unknown error')}")
            print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="CloudMatchAI v2.0")
    parser.add_argument("config", type=str, help="Path to YAML config")
    parser.add_argument(
        "--publish",
        nargs="?",
        const="docs",
        default=None,
        metavar="DIR",
        help="Also write results.json + results.meta.json for the static site. "
             "Defaults to 'docs' if no directory is given — pass a subfolder "
             "(e.g. --publish docs/jobs) to publish to a subpage instead of "
             "overwriting the homepage.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    asyncio.run(run_pipeline(str(config_path), publish_dir=args.publish))


if __name__ == "__main__":
    main()