<div align="center">

<img src="https://img.shields.io/badge/CloudMatchAI-v2.0.0-4F8EF7?style=for-the-badge&logo=amazonaws&logoColor=white"/>
<img src="https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge"/>
<img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
<img src="https://img.shields.io/badge/CLI-Tool-0A84FF?style=for-the-badge"/>
<img src="https://img.shields.io/badge/Adapters-Pluggable-8B5CF6?style=for-the-badge"/>

<h1>☁️ CloudMatchAI v2.0</h1>

<p>
<strong>Lightweight, adapter‑driven cloud provider scoring engine.</strong><br/>
Define your criteria in YAML. Plug in any provider adapter. Get ranked, explainable results instantly.
</p>

<p>
<a href="#-overview">Overview</a> •
<a href="#-features">Features</a> •
<a href="#-architecture">Architecture</a> •
<a href="#-usage">Usage</a> •
<a href="#-configuration">Configuration</a> •
<a href="#-adapters">Adapters</a> •
<a href="#-roadmap">Roadmap</a>
</p>

</div>

🌐 Overview
CloudMatchAI v2.0 is a simple, transparent, extensible scoring engine for evaluating cloud providers.

Where v1 was a full FastAPI + GPT‑powered recommendation platform, v2.0 is a clean, dependency‑free CLI tool designed for:

quick comparisons

reproducible scoring

adapter‑based provider data

YAML‑driven criteria

explainable results

It’s perfect for:

architecture teams

cloud cost reviews

vendor evaluations

internal tooling

demos and prototypes

✨ Features
Feature	Description
🔌 Adapter System	Plug in any provider source (static, API, DB, custom)
📊 Weighted Scoring	Cost, performance, support, or any custom metric
🧩 YAML Profiles	Define criteria and weights in a simple config file
🧠 Explainability	Every score includes a human‑readable explanation
🛠 Zero Dependencies	Pure Python — no FastAPI, no DB, no Redis
🚀 CLI‑First	Run evaluations instantly from the command line


🏗️ Architecture
CloudMatchAI v2.0 is intentionally minimal:

Code
┌───────────────────────────────────────────────┐
│                 CloudMatchAI CLI              │
│                                               │
│   ┌──────────────┐    ┌────────────────────┐ │
│   │  YAML Config  │───▶│   Scoring Engine   │ │
│   └──────────────┘    └─────────┬──────────┘ │
│                                  │            │
│                         ┌────────▼────────┐   │
│                         │   Adapter Layer  │   │
│                         │ (Static / API /  │   │
│                         │   Custom Data)   │   │
│                         └────────┬────────┘   │
│                                  │            │
│                         ┌────────▼────────┐   │
│                         │ Provider Dataset │   │
│                         └──────────────────┘   │
└───────────────────────────────────────────────┘
Scoring Formula
Code
score = Σ (provider_metric × weight)
Every provider receives:

total score

per‑criterion breakdown

explanation

🚀 Usage
Run the CLI
Code
python cli.py test.match.yaml
Example Output
Code
Provider: AWS
Score: 0.87
Breakdown:
  - cost: 0.8
  - performance: 0.9
  - support: 0.7
Explanation:
AWS performs strongly in performance and cost efficiency...
----------------------------------------
⚙️ Configuration
A scoring profile is defined in YAML:

yaml
profile:
  adapter: static
  criteria:
    cost: 0.4
    performance: 0.4
    support: 0.2
🔌 Adapters
Adapters live in adapters.py and must implement:

python
class BaseAdapter:
    def load(self):
        raise NotImplementedError
Static Adapter Example
python
class StaticAdapter(BaseAdapter):
    def load(self):
        return [
            {"name": "AWS", "cost": 0.8, "performance": 0.9, "support": 0.7},
            {"name": "Azure", "cost": 0.7, "performance": 0.85, "support": 0.8},
            {"name": "GCP", "cost": 0.75, "performance": 0.88, "support": 0.65},
        ]
You can add:

API adapters

database adapters

CSV adapters

scraped data adapters

internal enterprise adapters

🧪 Testing
Code
python cli.py test.match.yaml
(Yes — that’s the whole test.)

🗺️ Roadmap
[ ] v2.1 — Real cloud provider adapters

[ ] v2.2 — Visualization output (charts, radar plots)

[ ] v2.3 — Web UI wrapper

[ ] v3.0 — Unified engine replacing legacy v1 folder

📄 License
MIT License.

<div align="center">

Built with ☁️ and 🔧 by the CloudMatchAI team.<br/>
<a href="https://github.com/sdonovan43/CloudMatchAI/issues">Report a Bug</a> •
<a href="https://github.com/sdonovan43/CloudMatchAI/issues">Request a Feature</a>

</div>