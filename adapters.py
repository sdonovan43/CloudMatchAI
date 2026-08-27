from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
import asyncio
import httpx
from config import RootConfig


class BaseAdapter(ABC):
    def __init__(self, cfg: RootConfig):
        self.cfg = cfg

    @abstractmethod
    async def fetch(self) -> list[dict[str, Any]]:
        ...


# ============================
#       GROQ ADAPTER
# ============================

class GroqAdapter(BaseAdapter):
    """
    Adapter for Groq's OpenAI-compatible API.
    This adapter is for fetching ENTITIES, not scoring.
    """

    async def fetch(self) -> list[dict[str, Any]]:
        url = self.cfg.source.url  # correct fieldare you still thinking?
        method = self.cfg.source.method.upper()
        headers = self.cfg.source.headers or {}
        params = self.cfg.source.params or {}

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if method == "GET":
                    resp = await client.get(url, headers=headers, params=params)
                else:
                    resp = await client.post(url, headers=headers, json=params)

                resp.raise_for_status()
                data = resp.json()

                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    for v in data.values():
                        if isinstance(v, list):
                            return v

                return []

            except Exception as e:
                print("GROQ ADAPTER ERROR:", e)
                return []


# ============================
#       REST API ADAPTER
# ============================

class RestAPIAdapter(BaseAdapter):
    async def fetch(self) -> list[dict[str, Any]]:
        url = self.cfg.source.url
        method = self.cfg.source.method.upper()
        headers = self.cfg.source.headers or {}
        params = self.cfg.source.params or {}

        async with httpx.AsyncClient(timeout=10) as client:
            try:
                if method == "GET":
                    resp = await client.get(url, headers=headers, params=params)
                else:
                    resp = await client.post(url, headers=headers, json=params)

                resp.raise_for_status()
                data = resp.json()

                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    for v in data.values():
                        if isinstance(v, list):
                            return v

                return []

            except Exception as e:
                print("REST API ERROR:", e)
                return []


# ============================
#       STATIC ADAPTER
# ============================

class StaticAdapter(BaseAdapter):
    async def fetch(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "AWS",
                "compute": "high",
                "storage": "high",
                "egress": "high",
                "regions": 30,
                "compliance": ["SOC2", "GDPR"]
            },
            {
                "name": "Azure",
                "compute": "high",
                "storage": "medium",
                "egress": "medium",
                "regions": 28,
                "compliance": ["SOC2", "GDPR"]
            },
            {
                "name": "GCP",
                "compute": "medium",
                "storage": "medium",
                "egress": "low",
                "regions": 25,
                "compliance": ["SOC2"]
            },
        ]


# ============================
#       ADZUNA ADAPTER
# ============================

class AdzunaAdapter(BaseAdapter):
    """
    Fetches job listings via the Adzuna API (https://developer.adzuna.com/).
    Adzuna aggregates listings from Indeed and many other boards under one
    legitimate, ToS-compliant API — this avoids scraping LinkedIn/Indeed
    directly, which their own Terms of Service prohibit.

    Retries on transient errors (503, 429, timeouts) with backoff, since
    external job-board APIs occasionally have brief outages/blips.

    Expected source config:
        source:
          adapter: "adzuna"
          url: "https://api.adzuna.com/v1/api/jobs"   # base endpoint, no trailing slash
          method: "GET"
          params:
            country: "us"              # adzuna country code, e.g. us, gb, au
            what: "cyber security engineer"
            where: "Athens GA"
            results_per_page: 20
            app_id: "${ADZUNA_APP_ID}"
            app_key: "${ADZUNA_APP_KEY}"
    """

    async def fetch(self) -> list[dict[str, Any]]:
        base_url = self.cfg.source.url.rstrip("/")
        params = dict(self.cfg.source.params or {})

        country = params.pop("country", "us")
        page = params.pop("page", 1)
        url = f"{base_url}/{country}/search/{page}"

        # `what` can be a single string (one search) or a list of strings
        # (one search per title, results merged). Running separate searches
        # per title is more reliable than trying to cram multiple job titles
        # into Adzuna's single `what` field, which does an AND-style match
        # rather than "any of these titles."
        what_value = params.pop("what", None)
        what_list = what_value if isinstance(what_value, list) else [what_value]

        all_results: list[dict[str, Any]] = []
        async with httpx.AsyncClient(timeout=20) as client:
            for title in what_list:
                query_params = dict(params)
                if title is not None:
                    query_params["what"] = title
                page_results = await self._fetch_one(client, url, query_params, title)
                all_results.extend(page_results)

        return all_results

    async def _fetch_one(self, client: httpx.AsyncClient, url: str,
                          query_params: dict, title_label: Any) -> list[dict[str, Any]]:
        max_retries = 3
        attempt = 0

        while attempt < max_retries:
            try:
                resp = await client.get(url, params=query_params)
                resp.raise_for_status()
                data = resp.json()
                return self._normalize(data)

            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                if status in (429, 503):
                    attempt += 1
                    backoff_time = 10.0 * attempt
                    print(f"ADZUNA RETRY ('{title_label}'): Got status {status}. "
                          f"Backing off for {backoff_time}s... (Attempt {attempt}/{max_retries})")
                    await asyncio.sleep(backoff_time)
                else:
                    print(f"ADZUNA ADAPTER ERROR ('{title_label}'): Unrecoverable status {status}: {e}")
                    return []

            except httpx.TimeoutException as e:
                attempt += 1
                backoff_time = 10.0 * attempt
                print(f"ADZUNA TIMEOUT ('{title_label}'): {type(e).__name__}. "
                      f"Backing off for {backoff_time}s... (Attempt {attempt}/{max_retries})")
                await asyncio.sleep(backoff_time)

            except Exception as e:
                print(f"ADZUNA ADAPTER ERROR ('{title_label}'):", e)
                return []

        print(f"ADZUNA FATAL ('{title_label}'): Giving up after {max_retries} attempts.")
        return []

    @staticmethod
    def _normalize(data: dict) -> list[dict[str, Any]]:
        results = data.get("results", [])
        normalized = []
        for job in results:
            title = job.get("title", "").strip()
            company = (job.get("company") or {}).get("display_name", "Unknown")
            location = (job.get("location") or {}).get("display_name", "")
            category_val = job.get("category")
            category = category_val.get("label") if isinstance(category_val, dict) else category_val

            normalized.append({
                "name": f"{title} — {company}",
                "title": title,
                "company": company,
                "location": location,
                "description": job.get("description", ""),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max"),
                "contract_type": job.get("contract_type"),
                "category": category,
                "url": job.get("redirect_url"),
            })
        return normalized


# ============================
#       AWS ADAPTER
# ============================

class AWSAdapter(BaseAdapter):
    """
    Adapter for fetching AWS job listings from public sources.
    Returns sample data formatted to match existing CloudMatchAI job structure.
    """
    
    async def fetch(self) -> list[dict[str, Any]]:
        # This would use AWS job APIs with specific search parameters
        # Sample data in the same format as used by AdzunaAdapter in jobs.match.yaml
        return [
            {
                "name": "AWS Cloud Solutions Architect - Senior",
                "title": "Senior Cloud Solutions Architect",
                "company": "Amazon Web Services",
                "location": "Remote",
                "description": "Design and implement scalable cloud solutions on AWS. Experience required with EC2, S3, Lambda, RDS, and IAM.",
                "salary_min": 140000,
                "salary_max": 180000,
                "contract_type": "Full-time",
                "category": "Cloud Architecture",
                "url": "https://aws.amazon.com/jobs/senior-architect"
            }
        ]


# ============================
#       GCP ADAPTER
# ============================

class GCPAdapter(BaseAdapter):
    """
    Adapter for fetching GCP job listings from public sources.
    Returns sample data formatted to match existing CloudMatchAI job structure.
    """
    
    async def fetch(self) -> list[dict[str, Any]]:
        # This would use GCP job APIs with specific search parameters
        # Sample data in the same format as used by AdzunaAdapter in jobs.match.yaml
        return [
            {
                "name": "GCP Data Engineer - Principal",
                "title": "Principal Data Engineer",
                "company": "Google Cloud Platform",
                "location": "Remote",
                "description": "Design and implement data pipelines using GCP services. Experience with Dataproc, BigQuery, Dataflow, and Cloud Storage required.",
                "salary_min": 130000,
                "salary_max": 170000,
                "contract_type": "Full-time",
                "category": "Data Engineering",
                "url": "https://cloud.google.com/jobs/principal-data-engineer"
            }
        ]


# ============================
#       AZURE ADAPTER
# ============================

class AzureAdapter(BaseAdapter):
    """
    Adapter for fetching Azure job listings from public sources.
    Returns sample data formatted to match existing CloudMatchAI job structure.
    """
    
    async def fetch(self) -> list[dict[str, Any]]:
        # This would use Azure job APIs with specific search parameters
        # Sample data in the same format as used by AdzunaAdapter in jobs.match.yaml
        return [
            {
                "name": "Azure Cloud Architect - Lead",
                "title": "Lead Cloud Architect",
                "company": "Microsoft Azure",
                "location": "Remote",
                "description": "Design enterprise cloud solutions on Azure. Experience required with VMs, Storage, AD, and Azure networking services.",
                "salary_min": 135000,
                "salary_max": 175000,
                "contract_type": "Full-time",
                "category": "Cloud Architecture",
                "url": "https://azure.microsoft.com/jobs/lead-architect"
            }
        ]


# ============================
#       ADAPTER REGISTRY
# ============================

ADAPTERS = {
    "rest_api": RestAPIAdapter,
    "static": StaticAdapter,
    "groq": GroqAdapter,
    "adzuna": AdzunaAdapter,
    "aws": AWSAdapter,
    "gcp": GCPAdapter,
    "azure": AzureAdapter,
}


def get_adapter(cfg: RootConfig) -> BaseAdapter:
    """Factory function to create an adapter instance based on configuration."""
    adapter_type = cfg.source.adapter
    adapter_class = ADAPTERS.get(adapter_type)
    
    if not adapter_class:
        raise ValueError(f"Unsupported adapter type: {adapter_type}")
    
    return adapter_class(cfg)