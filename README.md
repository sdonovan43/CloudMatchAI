# CloudMatchAI

CloudMatchAI is an automated job‑intelligence pipeline that scrapes, scores, stores, and visualizes top engineering roles across multiple platforms. It runs continuously, updates a live dashboard, and deploys automatically via GitHub Actions.

---

## 🚦 Status

| Workflow | Status |
|---------|--------|
| CI / Scraper | ![CI](https://github.com/sdonovan43/CloudMatchAI/actions/workflows/cloudmatchai.yml/badge.svg) |
| Deployment | ![CD](https://github.com/sdonovan43/CloudMatchAI/actions/workflows/deploy.yml/badge.svg) |

---

## 📌 Overview

CloudMatchAI automates the entire job‑search intelligence workflow:

- Scrapes job listings using Playwright  
- Scores and deduplicates results  
- Stores structured job data in Cosmos DB  
- Generates a dashboard data file (`docs/data.json`)  
- Publishes a live dashboard via GitHub Pages  
- Deploys backend services to Azure Container Apps  

Everything runs on a 6‑hour schedule or on demand.

---

1. Scraper (Playwright)
      ↓
2. Dedupe Engine
      ↓
3. Cosmos DB (store jobs)
      ↓
4. Dashboard Generator (creates data.json)
      ↓
5. GitHub Pages (dashboard UI)

Meanwhile:
      ↘
       GitHub Actions CI/CD → Azure Container Apps (backend deployment)

