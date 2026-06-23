CloudMatchAI
AI‑powered job intelligence system built on Microsoft Foundry (post‑upgrade architecture).

CloudMatchAI is an agentic system that retrieves, filters, scores, and ranks job opportunities using enterprise‑grade retrieval, tools, and identity governance. After upgrading to Microsoft Foundry, CloudMatchAI becomes a fully managed Foundry Agent with Foundry IQ, Fabric IQ, Work IQ, and agentic retrieval.

🚀 Features
Foundry‑native agent runtime

Multi‑source knowledge via Foundry IQ

Agentic retrieval with query decomposition + reranking

Tool‑based filtering, scoring, scraping, and notifications

Entra‑integrated identity and governance

Hybrid search (vector + keyword)

Grounded answers with citations

Enterprise‑safe permission enforcement

📐 Architecture Diagrams

                ┌──────────────────────────────┐
                │        Foundry Agent         │
                │      (CloudMatchAI Brain)    │
                └──────────────┬───────────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────────┐
        │                Agent Runtime                     │
        │  (Reasoning • Tool Orchestration • Identity)     │
        └──────────────┬───────────────────────────────────┘
                       │
     ┌─────────────────┼──────────────────┬──────────────────┐
     ▼                 ▼                  ▼
┌──────────┐     ┌───────────┐      ┌────────────┐
│ Tools     │     │ Knowledge │      │ Retrieval   │
│ (Filter)  │     │ (Foundry  │      │ (Agentic    │
│ (Score)   │     │  IQ)      │      │  Retrieval) │
│ (Scrape)  │     └───────────┘      └────────────┘
│ (Notify)  │
└──────────┘

                ┌──────────────────────────────┐
                │     Data Sources (Jobs)      │
                │  • Job Boards                │
                │  • Company Sites             │
                │  • Internal Docs             │
                └──────────────┬───────────────┘
                               ▼
                ┌──────────────────────────────┐
                │     Foundry IQ Ingestion     │
                │  • Chunking                  │
                │  • Embeddings                │
                │  • Indexing                  │
                │  • Sensitivity Labels        │
                └──────────────┬───────────────┘
                               ▼
                ┌──────────────────────────────┐
                │     Foundry IQ Index         │
                │  (Hybrid Search: Vector +    │
                │   Keyword + Reranking)       │
                └──────────────┬───────────────┘
                               ▼
                ┌──────────────────────────────┐
                │   Agentic Retrieval Layer    │
                │  • Query Decomposition       │
                │  • Parallel Subqueries       │
                │  • Reranking                 │
                │  • Citations                 │
                └──────────────────────────────┘

┌───────────────────────────────────────────────┐
│                CloudMatchAI Tools             │
├───────────────────────────────────────────────┤
│ FilterTool   → Filters jobs by criteria       │
│ ScoreTool    → Ranks jobs                     │
│ ScraperTool  → Pulls new postings             │
│ NotifyTool   → Sends alerts                   │
│ ProfileTool  → Analyzes resume                │
└───────────────────────────────────────────────┘

User Query
   │
   ▼
┌──────────────────────────────┐
│  Agent Decomposes Query      │
│  (LLM-driven planning)       │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  Subqueries Generated         │
│  (skills, location, salary)   │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  Parallel Retrieval           │
│  (Foundry IQ Hybrid Search)   │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│  Reranking + Citations        │
└──────────────┬───────────────┘
               │
               ▼
Final Answer (Grounded, Cited)

                ┌──────────────────────────────┐
                │        Entra Identity        │
                │  • User Identity             │
                │  • Managed Identity          │
                │  • RBAC / ACL                │
                └──────────────┬───────────────┘
                               ▼
                ┌──────────────────────────────┐
                │     Purview Governance       │
                │  • Sensitivity Labels        │
                │  • Data Classification       │
                │  • Access Policies           │
                └──────────────┬───────────────┘
                               ▼
                ┌──────────────────────────────┐
                │   Permission-Aware Retrieval │
                │  (Foundry IQ enforces ACLs)  │
                └──────────────────────────────┘

User → Foundry Agent (CloudMatchAI)
          │
          ▼
   Agent Runtime
          │
 ┌────────┼────────┬──────────┐
 ▼        ▼        ▼          ▼
Tools   Foundry   Agentic    Identity
        IQ        Retrieval  (Entra)
(Filter, (Jobs,   (Decomp,   (ACL,
Score,   Skills,   Hybrid,    Labels)
Scrape)  Resume)   Rerank)
          │
          ▼
   Final Answer
 (Ranked Jobs + Citations)
