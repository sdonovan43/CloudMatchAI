from __future__ import annotations
from typing import Any, Dict, List
import math
import openai


class Scorer:
    """
    CloudMatchAI v2.0 scoring engine.
    Combines deterministic weighted scoring + optional LLM scoring.
    Produces:
        - numeric score (0–100)
        - explanation
        - per-field breakdown
    """

    def __init__(self, weights: Dict[str, float], llm_enabled: bool = False):
        """
        weights example:
        {
            "compute": 0.25,
            "storage": 0.25,
            "egress": 0.20,
            "regions": 0.15,
            "compliance": 0.15
        }
        """
        self.weights = weights
        self.llm_enabled = llm_enabled

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------

    def score(self, item: Dict[str, Any], criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        Returns:
        {
            "score": float,
            "breakdown": { field: float },
            "explanation": str
        }
        """

        breakdown = {}
        total = 0.0
        weight_sum = sum(self.weights.values())

        for key, weight in self.weights.items():
            expected = criteria.get(key)
            actual = item.get(key)

            if expected is None:
                breakdown[key] = 0.0
                continue

            if isinstance(expected, str):
                s = self._score_category(expected, actual)

            elif isinstance(expected, (int, float)):
                s = self._score_numeric(expected, actual)

            elif isinstance(expected, list):
                s = self._score_list(expected, actual)

            else:
                s = 0.0

            breakdown[key] = round(s * 100, 2)
            total += s * weight

        final_score = round((total / weight_sum) * 100, 2)

        explanation = (
            self._llm_explanation(item, criteria, breakdown, final_score)
            if self.llm_enabled
            else self._deterministic_explanation(item, breakdown, final_score)
        )

        return {
            "score": final_score,
            "breakdown": breakdown,
            "explanation": explanation,
        }

    # ----------------------------------------------------------------------
    # Deterministic scoring helpers
    # ----------------------------------------------------------------------

    def _score_category(self, expected: str, actual: Any) -> float:
        """
        high / medium / low → 1.0 / 0.6 / 0.3
        """
        if not isinstance(actual, str):
            return 0.0

        scale = {"high": 1.0, "medium": 0.6, "low": 0.3}
        return scale.get(actual.lower(), 0.0)

    def _score_numeric(self, expected: float, actual: Any) -> float:
        """
        Numeric scoring: closer is better.
        Perfect match = 1.0
        """
        if not isinstance(actual, (int, float)):
            return 0.0

        if expected == 0:
            return 1.0 if actual == 0 else 0.0

        diff = abs(expected - actual)
        return max(0.0, 1.0 - (diff / expected))

    def _score_list(self, expected: List[Any], actual: Any) -> float:
        """
        List scoring: fraction of expected items present.
        """
        if not isinstance(actual, list):
            return 0.0

        if not expected:
            return 1.0

        matches = sum(1 for x in expected if x in actual)
        return matches / len(expected)

    # ----------------------------------------------------------------------
    # Explanation generation
    # ----------------------------------------------------------------------

    def _deterministic_explanation(
        self,
        item: Dict[str, Any],
        breakdown: Dict[str, float],
        final_score: float,
    ) -> str:
        """
        Human-readable explanation without LLM.
        """
        lines = [f"Final score: {final_score}"]

        for k, v in breakdown.items():
            lines.append(f"- {k}: {v}")

        return "\n".join(lines)

    def _llm_explanation(
        self,
        item: Dict[str, Any],
        criteria: Dict[str, Any],
        breakdown: Dict[str, float],
        final_score: float,
    ) -> str:
        """
        Optional LLM explanation.
        """
        prompt = f"""
You are CloudMatchAI. Explain the scoring of this item.

Item:
{item}

Criteria:
{criteria}

Breakdown:
{breakdown}

Final Score: {final_score}

Write a concise explanation.
"""

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
            )
            return response.choices[0].message["content"].strip()

        except Exception as e:
            return f"(LLM explanation unavailable: {e})"
