# scorer.py
from __future__ import annotations
from typing import Any
from openai import OpenAI
from config import ProfileConfig

client = OpenAI()


def score_candidates(
    candidates: list[dict[str, Any]],
    profile: ProfileConfig,
) -> list[dict[str, Any]]:
    """Score each candidate using GPT-4o and return sorted results."""
    results = []
    for candidate in candidates:
        score, reasoning = _score_single(candidate, profile)
        results.append({**candidate, "score": score, "reasoning": reasoning})
    return sorted(results, key=lambda x: x["score"], reverse=True)


def _score_single(
    candidate: dict[str, Any],
    profile: ProfileConfig,
) -> tuple[float, str]:
    prompt = _build_prompt(candidate, profile)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": (
                "You are a cloud infrastructure analyst. "
                "Score the candidate 0.0–1.0 against the profile. "
                "Reply with exactly two lines:\n"
                "SCORE: <float>\nREASON: <one sentence>"
            )},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=80,
    )
    return _parse_response(response.choices[0].message.content or "")


def _build_prompt(candidate: dict[str, Any], profile: ProfileConfig) -> str:
    weights_str = ", ".join(f"{k}={v}" for k, v in profile.weights.items())
    return (
        f"Candidate: {candidate}\n"
        f"Workload: {profile.workload}\n"
        f"Budget: ${profile.budget_monthly_usd}/mo\n"
        f"Requirements: {profile.requirements}\n"
        f"Weights: {weights_str}"
    )


def _parse_response(text: str) -> tuple[float, str]:
    score, reasoning = 0.5, "No reasoning returned."
    for line in text.splitlines():
        if line.startswith("SCORE:"):
            try:
                score = float(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("REASON:"):
            reasoning = line.split(":", 1)[1].strip()
    return score, reasoning
