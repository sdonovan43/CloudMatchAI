<div align="center">

<img src="https://img.shields.io/badge/CloudMatchAI-v1.0.0-4F8EF7?style=for-the-badge&logo=amazonaws&logoColor=white" alt="CloudMatchAI Version"/>
<img src="https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge" alt="License"/>
<img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
<img src="https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
<img src="https://img.shields.io/badge/OpenAI-GPT--4o-412991?style=for-the-badge&logo=openai&logoColor=white" alt="OpenAI"/>
<img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker"/>

<h1>☁️ CloudMatchAI</h1>

<p>
  <strong>AI-powered cloud provider matching engine.</strong><br/>
  Submit your workload, architecture requirements, and budget — CloudMatchAI analyzes them against real-time pricing and capability data across AWS, Azure, GCP, and more to deliver ranked, explainable recommendations.
</p>

<p>
  <a href="#-features">Features</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-how-it-works">How It Works</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-getting-started">Getting Started</a> •
  <a href="#-api-reference">API Reference</a> •
  <a href="#-contributing">Contributing</a>
</p>

</div>

---

## 📋 Table of Contents

1. [Overview](#-overview)
2. [Features](#-features)
3. [Architecture](#-architecture)
   - [System Architecture](#system-architecture)
   - [Data Flow Diagram](#data-flow-diagram)
   - [AI Matching Pipeline](#ai-matching-pipeline)
4. [How It Works](#-how-it-works)
5. [Tech Stack](#-tech-stack)
6. [Getting Started](#-getting-started)
   - [Prerequisites](#prerequisites)
   - [Installation](#installation)
   - [Environment Variables](#environment-variables)
   - [Running Locally](#running-locally)
   - [Running with Docker](#running-with-docker)
7. [API Reference](#-api-reference)
8. [Configuration](#-configuration)
9. [Testing](#-testing)
10. [Roadmap](#-roadmap)
11. [Contributing](#-contributing)
12. [License](#-license)

---

## 🌐 Overview

**CloudMatchAI** is an intelligent recommendation engine that eliminates the friction of cloud provider selection. Organizations waste weeks evaluating cloud options manually — CloudMatchAI compresses that into seconds.

By combining **structured workload analysis**, **real-time pricing APIs**, and a **GPT-4o reasoning layer**, CloudMatchAI produces ranked recommendations complete with cost projections, trade-off explanations, and migration readiness scores.

Whether you're migrating a monolith, launching a greenfield ML platform, or optimizing multi-cloud spend, CloudMatchAI gives your team a defensible, data-backed starting point.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 AI-Powered Matching | GPT-4o analyzes workload profiles against provider capability matrices |
| 💰 Real-Time Pricing | Live cost estimates via AWS, Azure, and GCP pricing APIs |
| 📊 Ranked Recommendations | Scored results with weighted criteria (cost, performance, compliance, latency) |
| 🔍 Explainability | Human-readable rationale for every recommendation |
| 🌍 Multi-Cloud Support | AWS, Azure, GCP, OCI, and DigitalOcean coverage |
| 🔒 Compliance Filters | Filter by SOC 2, HIPAA, GDPR, FedRAMP, and PCI-DSS |
| 🚀 REST API | OpenAPI-spec REST interface for easy CI/CD and toolchain integration |
| 🐳 Docker-Ready | Single-command local deployment |
| 📈 Migration Scoring | Readiness scoring and effort estimation per recommendation |
| 🔗 Webhook Support | Push recommendations to Slack, Jira, or custom endpoints |

---

## 🏗️ Architecture

### System Architecture

The platform is composed of four primary layers: **Ingestion**, **Intelligence**, **Data**, and **Delivery**.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CloudMatchAI Platform                            │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         CLIENT LAYER                                  │  │
│  │   ┌──────────────┐   ┌──────────────┐   ┌───────────────────────┐   │  │
│  │   │  Web UI       │   │  REST Client  │   │  CI/CD Integration    │   │  │
│  │   │  (React)      │   │  (OpenAPI)    │   │  (GitHub Actions /    │   │  │
│  │   │               │   │               │   │   Terraform plugin)   │   │  │
│  │   └──────┬───────┘   └──────┬────────┘   └──────────┬────────────┘   │  │
│  └──────────┼──────────────────┼───────────────────────┼────────────────┘  │
│             │                  │                         │                   │
│  ┌──────────▼──────────────────▼─────────────────────── ▼────────────────┐  │
│  │                       INGESTION LAYER (FastAPI)                        │  │
│  │                                                                        │  │
│  │   ┌─────────────────┐      ┌─────────────────┐      ┌──────────────┐  │  │
│  │   │  /match endpoint │      │  Auth & Rate     │      │  Request     │  │  │
│  │   │  (POST)          │      │  Limiting        │      │  Validator   │  │  │
│  │   └────────┬─────────┘      └─────────────────┘      └──────────────┘  │  │
│  └────────────┼───────────────────────────────────────────────────────────┘  │
│               │                                                               │
│  ┌────────────▼───────────────────────────────────────────────────────────┐  │
│  │                      INTELLIGENCE LAYER                                 │  │
│  │                                                                         │  │
│  │   ┌─────────────────────┐       ┌────────────────────────────────────┐ │  │
│  │   │  Workload Profiler   │──────▶│   GPT-4o Matching Engine           │ │  │
│  │   │  - Compute needs     │       │   - Capability scoring             │ │  │
│  │   │  - Storage patterns  │       │   - Cost/perf weighting            │ │  │
│  │   │  - Network topology  │       │   - Compliance validation          │ │  │
│  │   │  - Compliance reqs   │       │   - Rationale generation           │ │  │
│  │   └─────────────────────┘       └──────────────┬─────────────────────┘ │  │
│  │                                                  │                       │  │
│  │   ┌───────────────────────────────────────────── ▼──────────────────┐  │  │
│  │   │                   Scoring & Ranking Engine                        │  │  │
│  │   │   Score = w₁·Cost + w₂·Performance + w₃·Compliance + w₄·Region │  │  │
│  │   └──────────────────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│               │                                                               │
│  ┌────────────▼───────────────────────────────────────────────────────────┐  │
│  │                          DATA LAYER                                     │  │
│  │                                                                         │  │
│  │  ┌─────────────┐  ┌──────────────────┐  ┌────────────────────────┐   │  │
│  │  │  PostgreSQL  │  │  Redis Cache     │  │  Cloud Pricing APIs    │   │  │
│  │  │  (Profiles & │  │  (Pricing TTL:   │  │  ┌───┐ ┌─────┐ ┌───┐ │   │  │
│  │  │   Results)   │  │   30 min)        │  │  │AWS│ │Azure│ │GCP│ │   │  │
│  │  └─────────────┘  └──────────────────┘  │  └───┘ └─────┘ └───┘ │   │  │
│  │                                          └────────────────────────┘   │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│               │                                                               │
│  ┌────────────▼───────────────────────────────────────────────────────────┐  │
│  │                        DELIVERY LAYER                                   │  │
│  │   ┌─────────────────┐   ┌──────────────────┐   ┌──────────────────┐  │  │
│  │   │  JSON Response   │   │  Webhook Push     │   │  PDF Report Gen  │  │  │
│  │   │  (ranked list)   │   │  (Slack / Jira)   │   │  (optional)      │  │  │
│  │   └─────────────────┘   └──────────────────┘   └──────────────────┘  │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### Data Flow Diagram

```
 User / API Client
        │
        │  POST /api/v1/match
        │  { workload_profile, weights, filters }
        ▼
┌───────────────────┐
│   FastAPI Gateway  │──── JWT Auth ──── Rate Limiter
└────────┬──────────┘
         │
         ▼
┌───────────────────┐       ┌──────────────────────┐
│  Request Validator │──────▶  Workload Profiler     │
│  (Pydantic schema) │       │  Normalizes & encodes │
└───────────────────┘       │  the raw workload desc │
                             └──────────┬───────────┘
                                        │
                   ┌────────────────────▼──────────────────────┐
                   │         Redis Cache Check                   │
                   │  (keyed by workload hash, TTL = 30 min)    │
                   └─────┬──────────────────────┬──────────────┘
                    HIT  │                       │  MISS
                         │              ┌────────▼──────────────┐
                         │              │ Cloud Pricing Fetcher  │
                         │              │ AWS / Azure / GCP APIs │
                         │              └────────┬──────────────┘
                         │                       │
                         │              ┌─────── ▼──────────────┐
                         │              │  GPT-4o Matching Engine│
                         │              │  System prompt +       │
                         │              │  pricing matrix +      │
                         │              │  workload profile      │
                         │              └────────┬──────────────┘
                         │                       │
                         │              ┌─────── ▼──────────────┐
                         │              │  Scoring & Ranking     │
                         │              │  Weighted multi-factor │
                         │              │  score per provider    │
                         │              └────────┬──────────────┘
                         │                       │
                         │              ┌─────── ▼──────────────┐
                         │              │  Cache Write           │
                         │              │  (Redis + PostgreSQL)  │
                         │              └────────┬──────────────┘
                         │                       │
                         └───────────────────────┘
                                        │
                             ┌──────────▼──────────┐
                             │  Ranked Response JSON│
                             │  + Explanations      │
                             │  + Cost Projections  │
                             └─────────────────────┘
```

---

### AI Matching Pipeline

```
 Workload Profile Input
        │
        ▼
┌───────────────────────────────────┐
│  Step 1: Feature Extraction        │
│  ─────────────────────────────── │
│  • Compute tier  (XS → 4XL)       │
│  • Storage type  (block/object/fs) │
│  • Network egress estimate         │
│  • Region requirements             │
│  • Compliance tags                 │
└────────────────┬──────────────────┘
                 │
                 ▼
┌───────────────────────────────────┐
│  Step 2: Capability Matrix Lookup  │
│  ─────────────────────────────── │
│  Provider capabilities indexed    │
│  by (service_type, region,        │
│  compliance_certifications)       │
└────────────────┬──────────────────┘
                 │
                 ▼
┌───────────────────────────────────┐
│  Step 3: LLM Reasoning (GPT-4o)   │
│  ─────────────────────────────── │
│  System prompt encodes:           │
│  • Scoring rubric & weights       │
│  • Provider strengths/weaknesses  │
│  • Cost normalisation rules       │
│  Returns structured JSON output   │
└────────────────┬──────────────────┘
                 │
                 ▼
┌───────────────────────────────────┐
│  Step 4: Weighted Scoring          │
│  ─────────────────────────────── │
│  score_i = Σ wⱼ · normalise(xᵢⱼ) │
│  Criteria: cost, perf, compliance,│
│  latency, ecosystem fit, support  │
└────────────────┬──────────────────┘
                 │
                 ▼
┌───────────────────────────────────┐
│  Step 5: Ranked Output             │
│  ─────────────────────────────── │
│  [ { provider, score, estimate,   │
│      rationale, trade_offs,       │
│      migration_effort } ]         │
└───────────────────────────────────┘
```

---

## ⚙️ How It Works

CloudMatchAI operates in five stages:

**1. Workload Profiling**
You describe your workload in structured JSON or natural language. The profiler normalises this into a canonical feature vector — compute tier, storage class, expected egress, compliance requirements, preferred regions, and SLA targets.

**2. Capability Matrix Matching**
A pre-indexed capability matrix maps each cloud provider's services to the feature vector dimensions. Compliance filters are applied first, immediately eliminating non-compliant providers from the candidate set.

**3. LLM Reasoning**
The workload feature vector and live pricing data are sent to GPT-4o with a structured system prompt that encodes scoring weights and provider knowledge. The model returns a structured JSON object with per-provider scores and natural-language rationale.

**4. Weighted Scoring & Ranking**
Scores are computed using a configurable weighted formula:

```
score = w₁·cost_score + w₂·performance_score + w₃·compliance_score + w₄·latency_score + w₅·ecosystem_score
```

Default weights are editable per-request or globally in `config.yaml`.

**5. Explainable Results**
Every recommendation includes:
- 💲 **Monthly cost estimate** (P50 / P90 ranges)
- 📋 **Rationale** — plain English explanation
- ⚖️ **Trade-offs** — what you gain and what you sacrifice
- 🚚 **Migration effort score** (Low / Medium / High)
- 🔗 **Direct links** to provider pricing calculators

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI 0.110 + Uvicorn |
| AI Engine | OpenAI GPT-4o (via `openai` SDK v1.x) |
| Validation | Pydantic v2 |
| Database | PostgreSQL 15 (SQLAlchemy + Alembic) |
| Cache | Redis 7 |
| Pricing Data | AWS Pricing API · Azure Retail Prices API · GCP Cloud Billing API |
| Auth | JWT (PyJWT) |
| Containerisation | Docker + Docker Compose |
| Testing | pytest + httpx |
| CI/CD | GitHub Actions |
| Observability | OpenTelemetry + Prometheus + Grafana |

---

## 🚀 Getting Started

### Prerequisites

- Python **3.10+**
- Docker & Docker Compose (for containerised setup)
- OpenAI API key with GPT-4o access
- PostgreSQL 15 instance (or use the provided Docker Compose stack)
- Redis 7 instance (or use the provided Docker Compose stack)

---

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/cloudmatchai.git
cd cloudmatchai

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

---

### Environment Variables

Copy the example env file and populate your secrets:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | Your OpenAI API key |
| `DATABASE_URL` | ✅ | PostgreSQL connection string |
| `REDIS_URL` | ✅ | Redis connection string |
| `AWS_ACCESS_KEY_ID` | Optional | For live AWS pricing lookups |
| `AWS_SECRET_ACCESS_KEY` | Optional | For live AWS pricing lookups |
| `AZURE_SUBSCRIPTION_ID` | Optional | For live Azure pricing lookups |
| `GCP_PROJECT_ID` | Optional | For live GCP pricing lookups |
| `JWT_SECRET_KEY` | ✅ | Secret for JWT token signing |
| `LOG_LEVEL` | Optional | `DEBUG`, `INFO` (default), `WARNING` |
| `CACHE_TTL_SECONDS` | Optional | Pricing cache TTL (default: `1800`) |

---

### Running Locally

```bash
# Apply database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

---

### Running with Docker

```bash
# Build and start all services (API + PostgreSQL + Redis)
docker compose up --build

# Run in detached mode
docker compose up -d --build

# View logs
docker compose logs -f api
```

---

## 📡 API Reference

### `POST /api/v1/match`

Submit a workload profile and receive ranked cloud provider recommendations.

**Request Body**

```json
{
  "workload": {
    "name": "ML Training Cluster",
    "description": "Weekly batch ML training job, GPU-accelerated, ~40 TB dataset",
    "compute": {
      "type": "gpu",
      "vcpu": 64,
      "memory_gb": 256,
      "gpu_count": 8
    },
    "storage": {
      "type": "object",
      "size_tb": 40,
      "iops_required": 5000
    },
    "network": {
      "egress_gb_monthly": 500,
      "regions_preferred": ["us-east-1", "eu-west-1"]
    },
    "compliance": ["SOC2", "GDPR"],
    "budget_monthly_usd": 15000
  },
  "weights": {
    "cost": 0.4,
    "performance": 0.3,
    "compliance": 0.2,
    "latency": 0.1
  },
  "filters": {
    "exclude_providers": [],
    "require_regions": ["us-east-1"]
  }
}
```

**Response**

```json
{
  "request_id": "cmatch_01J3XYZ789",
  "generated_at": "2026-06-21T21:37:00Z",
  "recommendations": [
    {
      "rank": 1,
      "provider": "AWS",
      "score": 0.87,
      "monthly_cost_estimate": {
        "p50_usd": 12340,
        "p90_usd": 14100
      },
      "rationale": "AWS offers the broadest GPU instance selection (p4d, p3dn) in both requested regions with native S3 integration for 40 TB object storage, minimising egress costs within-region. Both SOC 2 and GDPR controls are fully met.",
      "trade_offs": {
        "pros": ["Widest GPU availability", "Native S3 integration", "Mature MLOps tooling (SageMaker)"],
        "cons": ["Higher baseline compute cost vs GCP", "Egress costs add up at scale"]
      },
      "migration_effort": "Low",
      "compliance_status": {
        "SOC2": true,
        "GDPR": true
      },
      "pricing_links": {
        "compute": "https://aws.amazon.com/ec2/pricing/",
        "storage": "https://aws.amazon.com/s3/pricing/"
      }
    },
    {
      "rank": 2,
      "provider": "GCP",
      "score": 0.82,
      "monthly_cost_estimate": {
        "p50_usd": 11200,
        "p90_usd": 13500
      },
      "rationale": "GCP's A100-based A2 instances offer strong price-performance for ML training with Vertex AI integration. Lower compute unit cost than AWS, though slightly less egress-friendly at 500 GB/month.",
      "trade_offs": {
        "pros": ["Lower compute cost", "Vertex AI ecosystem", "Sustained use discounts automatic"],
        "cons": ["Fewer GPU availability zones in eu-west", "Support tier required for GDPR DPA"]
      },
      "migration_effort": "Medium",
      "compliance_status": {
        "SOC2": true,
        "GDPR": true
      },
      "pricing_links": {
        "compute": "https://cloud.google.com/compute/all-pricing",
        "storage": "https://cloud.google.com/storage/pricing"
      }
    }
  ],
  "cached": false
}
```

---

### Other Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Health check |
| `GET` | `/api/v1/providers` | List supported cloud providers |
| `GET` | `/api/v1/providers/{id}/capabilities` | Get capability matrix for a provider |
| `GET` | `/api/v1/match/{request_id}` | Retrieve a previous match result |
| `POST` | `/api/v1/webhooks` | Register a webhook endpoint |
| `DELETE` | `/api/v1/webhooks/{id}` | Remove a webhook |
| `GET` | `/api/v1/metrics` | Prometheus metrics endpoint |

Full OpenAPI spec available at `/docs` (Swagger UI) or `/redoc`.

---

## 🔧 Configuration

Scoring weights and provider lists are managed in `config.yaml`:

```yaml
# config.yaml

matching:
  default_weights:
    cost: 0.35
    performance: 0.30
    compliance: 0.20
    latency: 0.10
    ecosystem: 0.05
  cache_ttl_seconds: 1800
  max_recommendations: 5

providers:
  enabled:
    - aws
    - azure
    - gcp
    - oci
    - digitalocean

llm:
  model: gpt-4o
  temperature: 0.1
  max_tokens: 2048

webhooks:
  retry_attempts: 3
  retry_backoff_seconds: 5
```

---

## 🧪 Testing

```bash
# Run the full test suite
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run only integration tests (requires running DB + Redis)
pytest tests/integration/
```

---

## 🗺️ Roadmap

- [ ] **v1.1** — Terraform provider plugin for CloudMatchAI recommendations
- [ ] **v1.2** — Multi-cloud arbitrage mode (split workloads across providers)
- [ ] **v1.3** — Carbon footprint scoring dimension
- [ ] **v1.4** — Spot / Preemptible instance optimisation mode
- [ ] **v2.0** — Fine-tuned matching model replacing GPT-4o prompting
- [ ] **v2.1** — Real-time cost anomaly alerts via connected cloud billing APIs

---

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a pull request.

```bash
# Fork the repo and create your branch
git checkout -b feature/my-new-feature

# Make your changes, then run tests
pytest

# Commit with a conventional commit message
git commit -m "feat: add carbon footprint scoring dimension"

# Push and open a PR
git push origin feature/my-new-feature
```

All PRs require:
- Passing CI (tests + linting)
- At least one approving review
- Test coverage for new code paths

---

## 📄 License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for full terms.

---

<div align="center">

Built with ☁️ and 🤖 by the CloudMatchAI team.<br/>
<a href="https://github.com/your-org/cloudmatchai/issues">Report a Bug</a> •
<a href="https://github.com/your-org/cloudmatchai/issues">Request a Feature</a>

</div>
