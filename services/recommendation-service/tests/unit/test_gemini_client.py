"""Unit tests for GeminiClient error handling — Gemini 429 / ResourceExhausted."""
from __future__ import annotations
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_generate_raises_503_on_resource_exhausted():
    """GeminiClient.generate() must raise HTTPException(503) when Gemini returns 429."""
    from google.api_core.exceptions import ResourceExhausted
    from src.llm.gemini_client import GeminiClient

    client = GeminiClient.__new__(GeminiClient)
    mock_model = MagicMock()
    mock_model.generate_content_async = AsyncMock(
        side_effect=ResourceExhausted("Quota exceeded")
    )
    client._model = mock_model

    with pytest.raises(HTTPException) as exc_info:
        await client.generate("test prompt")

    assert exc_info.value.status_code == 503
    assert "temporarily unavailable" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_generate_returns_stripped_text_on_success():
    """GeminiClient.generate() returns cleaned response text on success."""
    from src.llm.gemini_client import GeminiClient

    client = GeminiClient.__new__(GeminiClient)
    mock_response = MagicMock()
    mock_response.text = "```json\n{\"key\": \"value\"}\n```"
    mock_model = MagicMock()
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)
    client._model = mock_model

    result = await client.generate("test prompt")
    assert result == '{"key": "value"}'


@pytest.mark.asyncio
async def test_generate_reraises_other_exceptions():
    """GeminiClient.generate() must NOT swallow non-quota exceptions."""
    from src.llm.gemini_client import GeminiClient

    client = GeminiClient.__new__(GeminiClient)
    mock_model = MagicMock()
    mock_model.generate_content_async = AsyncMock(side_effect=ValueError("unexpected"))
    client._model = mock_model

    with pytest.raises(ValueError):
        await client.generate("test prompt")
