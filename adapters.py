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
        url = self.cfg.source.url  # correct field
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
            normalized.append({
                "name": f"{title} — {company}",
                "title": title,
                "company": company,
                "location": location,
                "description": job.get("description", ""),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max"),
                "contract_type": job.get("contract_type"),
                "category": (job.get("category") or {}).get("label"),
                "url": job.get("redirect_url"),
            })
        return normalized


# ============================
#       ADAPTER REGISTRY
# ============================

ADAPTERS = {
    "rest_api": RestAPIAdapter,
    "static": StaticAdapter,
    "groq": GroqAdapter,
    "adzuna": AdzunaAdapter,
}


def get_adapter(cfg: RootConfig):
    cls = ADAPTERS.get(cfg.source.adapter)
    if not cls:
        raise ValueError(f"Unknown adapter: {cfg.source.adapter}")
    return cls(cfg)