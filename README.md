# CloudMatchAI

CloudMatchAI is an automated job‑intelligence pipeline that scrapes, scores, stores, and visualizes top engineering roles across multiple platforms. It runs continuously, updates a live dashboard, and deploys backend services automatically through GitHub Actions.

---

## 🚦 Status

| Workflow | Status |
|---------|--------|
| CI / Scraper | ![CI](https://github.com/sdonovan43/CloudMatchAI/actions/workflows/cloudmatchai.yml/badge.svg?branch=master) |
| Deployment | ![CD](https://github.com/sdonovan43/CloudMatchAI/actions/workflows/deploy.yml/badge.svg?branch=master) |

---

## 🧩 Architecture Diagram

```mermaid
flowchart TD

    A[Playwright Scraper<br/>scraper.py] --> B[Dedupe Engine<br/>dedupe.py]
    B --> C[Cosmos DB<br/>Job Storage]

    C --> D[Dashboard Generator<br/>data.json builder]
    D --> E[GitHub Pages<br/>Live Dashboard]

    C --> F[CI Workflow<br/>cloudmatchai.yml]
    F --> G[CD Workflow<br/>deploy.yml]
    G --> H[Azure Container Apps<br/>Backend Deployment]


