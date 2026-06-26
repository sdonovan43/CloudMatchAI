import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import httpx
import json

# Import the scorer module
import scorer

# ============================
#   Mock Configuration Object
# ============================
class MockConfig:
    """A minimal mock configuration object to satisfy scorer.py's requirements."""
    def __init__(self, provider_name="gemini"):
        self.llm = self.LLMConfig(provider_name)
        self.profile = self.ProfileConfig()

    class LLMConfig:
        def __init__(self, provider_name):
            self.provider = provider_name
            self.model = "mock-model"
            self.api_key = "mock-api-key"
            self.endpoint = "http://mock-endpoint.com"

    class ProfileConfig:
        def __init__(self):
            self.name = "Test Profile"
            self.description = "A description for testing."
            self.criteria = {
                "performance": 0.4,
                "cost": 0.3,
                "reliability": 0.3
            }

# ============================
#   Test Cases for scorer.py
# ============================

@pytest.mark.asyncio
async def test_score_entities_with_retry_success():
    """
    Tests that score_entities successfully retries on transient errors (503, 429)
    and eventually succeeds for one item, while another item fails after retries.
    """
    mock_cfg = MockConfig(provider_name="gemini")
    
    test_items = [
        {"id": "item1", "name": "CloudServiceA"}, # Will fail after 3 retries
        {"id": "item2", "name": "CloudServiceB"}, # Will succeed after 2 retries (3 calls)
    ]

    mock_llm_response_json = json.dumps({
        "score_breakdown": {
            "performance": {"score": 0.9, "reasoning": "High performance."},
            "cost": {"score": 0.7, "reasoning": "Moderate cost."},
            "reliability": {"score": 0.8, "reasoning": "Good reliability."}
        },
        "overall_score": 0.82
    })

    with patch('scorer.GeminiProvider.chat', new_callable=AsyncMock) as mock_chat:
        # Define the sequence of side effects for all calls across all items
        # Item1 (CloudServiceA): 3 failures -> consumes 3 from side_effect
        # Item2 (CloudServiceB): 2 failures, then 1 success -> consumes 3 from side_effect
        # Total calls to mock_chat will be 3 + 3 = 6
        mock_chat.side_effect = [
            # Calls for 'CloudServiceA' (item1) - all 503s leading to failure
            httpx.HTTPStatusError("Service Unavailable", request=httpx.Request("POST", "/"), response=httpx.Response(503)),
            httpx.HTTPStatusError("Service Unavailable", request=httpx.Request("POST", "/"), response=httpx.Response(503)),
            httpx.HTTPStatusError("Service Unavailable", request=httpx.Request("POST", "/"), response=httpx.Response(503)),
            
            # Calls for 'CloudServiceB' (item2) - two 503s then a success
            httpx.HTTPStatusError("Service Unavailable", request=httpx.Request("POST", "/"), response=httpx.Response(503)),
            httpx.HTTPStatusError("Service Unavailable", request=httpx.Request("POST", "/"), response=httpx.Response(503)),
            mock_llm_response_json, # Success for 'CloudServiceB' on its 3rd attempt
        ]

        scored_results = await scorer.score_entities(mock_cfg, test_items)

        # Assertions
        assert len(scored_results) == 2
        
        # Check the first item (CloudServiceA), which should have failed after 3 attempts
        assert scored_results[0]["id"] == "item1"
        assert "_match_analysis" in scored_results[0]
        assert "error" in scored_results[0]["_match_analysis"]
        assert scored_results[0]["_match_analysis"]["error"] == "Failed to generate scores after multiple backend attempts."
        
        # Check the second item (CloudServiceB), which should have succeeded after retries
        assert scored_results[1]["id"] == "item2"
        assert "_match_analysis" in scored_results[1]
        assert "error" not in scored_results[1]["_match_analysis"]
        assert scored_results[1]["_match_analysis"]["overall_score"] == 0.82
        
        assert mock_chat.call_count == 6 # Total calls (3 for item1 + 3 for item2)

@pytest.mark.asyncio
async def test_single_entity_retry_success():
    """
    Tests that score_entities successfully retries a single entity on transient errors
    (503, 429) and eventually succeeds.
    """
    mock_cfg = MockConfig(provider_name="gemini")
    test_item = {"id": "single_item", "name": "ReliableCloudService"}

    mock_llm_response_json = json.dumps({
        "score_breakdown": {
            "performance": {"score": 0.9, "reasoning": "High performance."},
            "cost": {"score": 0.7, "reasoning": "Moderate cost."},
            "reliability": {"score": 0.8, "reasoning": "Good reliability."}
        },
        "overall_score": 0.82
    })

    with patch('scorer.GeminiProvider.chat', new_callable=AsyncMock) as mock_chat:
        mock_chat.side_effect = [
            httpx.HTTPStatusError("Rate Limit Exceeded", request=httpx.Request("POST", "/"), response=httpx.Response(429)),
            httpx.HTTPStatusError("Service Unavailable", request=httpx.Request("POST", "/"), response=httpx.Response(503)),
            mock_llm_response_json, # Success on the 3rd attempt
        ]

        scored_results = await scorer.score_entities(mock_cfg, [test_item])

        assert len(scored_results) == 1
        result = scored_results[0]
        
        assert result["id"] == "single_item"
        assert "_match_analysis" in result
        assert "error" not in result["_match_analysis"]
        assert result["_match_analysis"]["overall_score"] == 0.82
        
        # The retry loop means 1 initial call + 2 retries = 3 calls
        assert mock_chat.call_count == 3

@pytest.mark.asyncio
async def test_single_entity_retry_failure():
    """
    Tests that score_entities fails after exhausting all retries for a single entity.
    """
    mock_cfg = MockConfig(provider_name="gemini")
    test_item = {"id": "failing_item", "name": "UnreliableCloudService"}

    with patch('scorer.GeminiProvider.chat', new_callable=AsyncMock) as mock_chat:
        mock_chat.side_effect = [
            httpx.HTTPStatusError("Service Unavailable", request=httpx.Request("POST", "/"), response=httpx.Response(503)),
            httpx.HTTPStatusError("Service Unavailable", request=httpx.Request("POST", "/"), response=httpx.Response(503)),
            httpx.HTTPStatusError("Service Unavailable", request=httpx.Request("POST", "/"), response=httpx.Response(503)),
            # No successful response; it exhausts all 3 attempts (initial + 2 retries)
        ]

        scored_results = await scorer.score_entities(mock_cfg, [test_item])

        assert len(scored_results) == 1
        result = scored_results[0]
        
        assert result["id"] == "failing_item"
        assert "_match_analysis" in result
        assert "error" in result["_match_analysis"]
        assert result["_match_analysis"]["error"] == "Failed to generate scores after multiple backend attempts."
        
        # The retry loop means 1 initial call + 2 retries = 3 calls
        assert mock_chat.call_count == 3

@pytest.mark.asyncio
async def test_single_entity_unrecoverable_error():
    """
    Tests that score_entities handles an unrecoverable error (e.g., JSONDecodeError or other non-HTTPStatusError)
    and does not retry, marking the item as failed.
    """
    mock_cfg = MockConfig(provider_name="gemini")
    test_item = {"id": "bad_json_item", "name": "CorruptResponseService"}

    with patch('scorer.GeminiProvider.chat', new_callable=AsyncMock) as mock_chat:
        # Simulate an API response that is not valid JSON
        # This will cause a json.JSONDecodeError, which is caught by the generic `except Exception`
        # and should not retry.
        mock_chat.side_effect = ["this is not json response"] 

        scored_results = await scorer.score_entities(mock_cfg, [test_item])

        assert len(scored_results) == 1
        result = scored_results[0]
        
        assert result["id"] == "bad_json_item"
        assert "_match_analysis" in result
        assert "error" in result["_match_analysis"]
        # Corrected assertion: matches the actual error message stored in `_match_analysis`
        assert result["_match_analysis"]["error"] == "Failed to generate scores after multiple backend attempts."
        
        # It should only attempt once because other Exceptions are "unrecoverable"
        assert mock_chat.call_count == 1

@pytest.mark.asyncio
async def test_score_entities_empty_items():
    """
    Tests that score_entities returns an empty list if given an empty list of items.
    """
    mock_cfg = MockConfig(provider_name="gemini")
    
    with patch('scorer.GeminiProvider.chat', new_callable=AsyncMock) as mock_chat:
        scored_results = await scorer.score_entities(mock_cfg, [])
        assert scored_results == []
        assert mock_chat.call_count == 0 # No calls should be made if no items

