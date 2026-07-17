"""
Reads your LinkedIn data export and fills in the `candidate:` block of
jobs.match.yaml automatically.

LinkedIn's "Get a copy of your data" export gives you a folder of CSVs.
This script looks for these specific files inside that folder:

    Profile.csv     -> headline / summary
    Skills.csv      -> skill list
    Positions.csv   -> job history (used to build experience_summary
                       and estimate total years of experience)

If a file is missing, that section is just left blank/skipped rather
than failing the whole script — so a partial export still works.

Usage:
    python update_candidate_from_linkedin.py path/to/linkedin_export_folder

This will back up your existing jobs.match.yaml to
jobs.match.yaml.bak before overwriting it.
"""
import sys
import csv
import shutil
from pathlib import Path
from datetime import datetime

try:
    import yaml
except ImportError:
    print("Missing dependency. Run: pip install pyyaml --break-system-packages")
    sys.exit(1)


def read_csv_safe(path: Path) -> list[dict]:
    if not path.exists():
        print(f"  (skipping {path.name} — not found in export folder)")
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def parse_profile(export_dir: Path) -> dict:
    rows = read_csv_safe(export_dir / "Profile.csv")
    if not rows:
        return {"headline": "", "summary": ""}
    row = rows[0]
    # LinkedIn's export sometimes calls these "Headline" / "Summary"
    return {
        "headline": row.get("Headline", "").strip(),
        "summary": row.get("Summary", "").strip(),
    }


def parse_skills(export_dir: Path) -> list[str]:
    rows = read_csv_safe(export_dir / "Skills.csv")
    skills = []
    for row in rows:
        # column is usually just "Name"
        name = row.get("Name") or row.get("Skill") or ""
        name = name.strip()
        if name:
            skills.append(name)
    return skills


def parse_positions(export_dir: Path) -> tuple[str, float | None]:
    """
    Returns (experience_summary_text, estimated_total_years).
    Estimated years is a rough sum of each position's duration — overlapping
    roles will overcount, so treat it as a ballpark, not a precise figure.
    """
    rows = read_csv_safe(export_dir / "Positions.csv")
    if not rows:
        return "", None

    summary_lines = []
    total_months = 0
    now = datetime.now()

    for row in rows:
        company = (row.get("Company Name") or "").strip()
        title = (row.get("Title") or "").strip()
        started = (row.get("Started On") or "").strip()
        finished = (row.get("Finished On") or "").strip()

        line = f"{title} at {company}" if company else title
        if started:
            line += f" ({started} - {finished or 'Present'})"
        summary_lines.append(line)

        # Try to estimate duration in months. LinkedIn exports dates like "Jan 2021".
        months = _months_between(started, finished, now)
        if months:
            total_months += months

    experience_summary = "; ".join(summary_lines)
    total_years = round(total_months / 12, 1) if total_months else None
    return experience_summary, total_years


def _months_between(started: str, finished: str, now: datetime) -> int | None:
    def parse_month_year(s: str):
        s = s.strip()
        if not s:
            return None
        for fmt in ("%b %Y", "%B %Y"):
            try:
                return datetime.strptime(s, fmt)
            except ValueError:
                continue
        return None

    start_dt = parse_month_year(started)
    if not start_dt:
        return None
    end_dt = parse_month_year(finished) if finished else now

    if not end_dt:
        end_dt = now

    months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
    return max(months, 0)


def update_yaml(yaml_path: Path, profile: dict, skills: list[str],
                 experience_summary: str, experience_years: float | None):
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    summary_text = profile.get("summary") or profile.get("headline") or ""

    data["candidate"] = {
        "summary": summary_text,
        "skills": skills,
        "experience_years": experience_years,
        "experience_summary": experience_summary,
    }

    backup_path = yaml_path.with_suffix(yaml_path.suffix + ".bak")
    shutil.copy(yaml_path, backup_path)
    print(f"Backed up existing file to {backup_path}")

    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True, width=100)

    print(f"Updated {yaml_path} with candidate profile from LinkedIn export.")
    print("NOTE: YAML comments in the original file are not preserved by this "
          "rewrite — review the file afterward to make sure everything still "
          "looks right (env var placeholders like ${GEMINI_API_KEY} are preserved as values, "
          "just double check them).")


def main():
    if len(sys.argv) < 2:
        print("Usage: python update_candidate_from_linkedin.py path/to/linkedin_export_folder")
        sys.exit(1)

    export_dir = Path(sys.argv[1])
    if not export_dir.exists():
        print(f"Folder not found: {export_dir}")
        sys.exit(1)

    yaml_path = Path("jobs.match.yaml")
    if not yaml_path.exists():
        print("jobs.match.yaml not found in the current folder. "
              "Run this script from your CloudMatchAI project root.")
        sys.exit(1)

    print(f"Reading LinkedIn export from: {export_dir}")
    profile = parse_profile(export_dir)
    skills = parse_skills(export_dir)
    experience_summary, experience_years = parse_positions(export_dir)

    print(f"\nFound:")
    print(f"  Headline/summary: {'yes' if (profile.get('summary') or profile.get('headline')) else 'not found'}")
    print(f"  Skills: {len(skills)} found")
    print(f"  Positions: {'yes' if experience_summary else 'not found'}"
          f"{f' (~{experience_years} years estimated)' if experience_years else ''}")

    update_yaml(yaml_path, profile, skills, experience_summary, experience_years)


if __name__ == "__main__":
    main()