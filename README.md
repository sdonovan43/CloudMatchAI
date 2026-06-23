⚡ CloudMatchAI v2
A precision-built, YAML‑driven scoring engine for anything worth ranking.
CloudMatchAI v2 is the clean reboot — a modular, adapter‑based engine that takes structured input, applies weighted logic, and lets an LLM do the heavy lifting on evaluation.
It’s lean. It’s sharp. It’s not here to hold your hand.

If v1 was a job scraper with opinions,
v2 is a scalpel.

🚀 Why v2 Exists
Because the world doesn’t need another bloated “AI platform.”
It needs a simple, composable engine that can score:

cloud providers

job listings

apartments

tequila brands

dogs

anything with attributes

Change the YAML → change the universe.
No rewrites. No drama.

🧩 Core Concepts (No BS)
YAML is the source of truth
Profiles, criteria, adapters — all defined in .yaml.
You don’t touch Python unless you want to.

Adapters do the fetching
Static, REST, Playwright — or whatever you write next.
One class = one data source.

LLM does the scoring
Weighted criteria + GPT‑4o = ranked, explained results.

CLI runs the whole thing
Code
python cli.py <profile.yaml>
That’s it.
No flags. No 14‑step onboarding ritual.

🧱 Architecture (The 10‑second mental model)
Code
   YAML Profile
       │
       ▼
   config.py
   (validation + loading)
       │
       ▼
   adapters.py
   (data source plug-ins)
       │
       ▼
   scorer.py
   (LLM scoring engine)
       │
       ▼
   cli.py
   (execution + output)
Everything is explicit.
Everything is traceable.
Everything is replaceable.

📂 Repo Layout (v2‑clean, no dead weight)
Code
CloudMatchAI/
│
├── adapters.py          # pluggable data sources
├── cli.py               # command-line runner
├── config.py            # YAML loader + validation
├── scorer.py            # LLM scoring engine
├── clouds.match.yaml    # example cloud scoring profile
├── test.match.yaml      # minimal static test profile
├── requirements.txt
├── README.md
│
├── legacy_v1/           # entire v1 system quarantined
├── docs/                # optional docs
└── logs/                # runtime logs
If it’s not part of the v2 engine, it lives in legacy_v1/ where it can’t hurt anyone.

📝 Example Profile (test.match.yaml)
yaml
profile:
  adapter: static
  criteria:
    cost: 0.4
    performance: 0.4
    support: 0.2
This is the “does the engine even run” profile.
It does.

▶️ Run It
Code
python cli.py test.match.yaml
You’ll get output like:

Code
Provider: AWS
Score: 0.87
Breakdown:
  cost: 0.8
  performance: 0.9
  support: 0.7

Explanation:
AWS performs strongly in performance and cost efficiency...
----------------------------------------
Swap the YAML → score something else.
The engine doesn’t care.

🔌 Adapters (The Real Power Move)
StaticAdapter
For testing. Zero dependencies. Zero excuses.

RestAPIAdapter
Point it at an API.
It fetches. You score.

PlaywrightAdapter
For dynamic sites.
Use it when the data refuses to sit still.

Write your own
One class.
One method.
Infinite possibilities.

🧠 Scoring Engine (LLM‑backed, not LLM‑bloated)
scorer.py handles:

weighted scoring

structured breakdowns

LLM‑generated explanations

consistent ranking

It’s intentionally small.
If you want to tweak the logic, you won’t need a machete.

🗂️ Legacy v1 (Quarantined, but preserved)
Everything from the old job‑scraper era lives in:

Code
legacy_v1/
It’s not loaded.
It’s not imported.
It’s not part of v2.
It’s just there in case you ever want to remember how chaotic things used to be.

🤝 Contributing
If you want to add:

new adapters

new scoring profiles

better docs

performance improvements

…go for it.
The engine is built to be extended.

📜 License
MIT.
Do whatever you want — just don’t blame me if you point it at tequila brands and start a bar fight.