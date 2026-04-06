"""LLM client abstraction — supports Groq (free), Gemini, OpenAI, and Anthropic Claude.

Select provider via LLM_PROVIDER env var: "groq" (default, free) | "gemini" | "openai" | "anthropic"
"""
from __future__ import annotations
import abc
import os
import re


class LLMClient(abc.ABC):
    @abc.abstractmethod
    async def generate(self, prompt: str) -> str: ...


# ── Groq (free tier) ─────────────────────────────────────────────────────────

class GroqClient(LLMClient):
    def __init__(self):
        from groq import AsyncGroq
        self._client = AsyncGroq(api_key=os.environ["GROQ_API_KEY"])

    async def generate(self, prompt: str) -> str:
        from fastapi import HTTPException
        try:
            response = await self._client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=8192,
            )
            return _strip_markdown(response.choices[0].message.content or "")
        except Exception as exc:
            if getattr(exc, "status_code", None) == 429:
                raise HTTPException(
                    status_code=503,
                    detail="Plan generation is temporarily unavailable — please try again shortly.",
                )
            raise


# ── Anthropic Claude ──────────────────────────────────────────────────────────

class AnthropicClient(LLMClient):
    def __init__(self):
        import anthropic
        self._client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    async def generate(self, prompt: str) -> str:
        from fastapi import HTTPException
        try:
            message = await self._client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            return _strip_markdown(message.content[0].text)
        except Exception as exc:
            _cls = type(exc).__name__
            # Anthropic rate-limit errors
            if "rate" in _cls.lower() or "overload" in _cls.lower() or getattr(exc, "status_code", None) in (429, 529):
                raise HTTPException(
                    status_code=503,
                    detail="Plan generation is temporarily unavailable — please try again shortly.",
                )
            raise


# ── OpenAI ────────────────────────────────────────────────────────────────────

class OpenAIClient(LLMClient):
    def __init__(self):
        from openai import AsyncOpenAI
        self._client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

    async def generate(self, prompt: str) -> str:
        from fastapi import HTTPException
        try:
            response = await self._client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096,
            )
            return _strip_markdown(response.choices[0].message.content or "")
        except Exception as exc:
            if getattr(exc, "status_code", None) == 429:
                raise HTTPException(
                    status_code=503,
                    detail="Plan generation is temporarily unavailable — please try again shortly.",
                )
            raise


# ── Gemini ────────────────────────────────────────────────────────────────────

class GeminiClient(LLMClient):
    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        self._model = genai.GenerativeModel("gemini-2.0-flash-lite")

    async def generate(self, prompt: str) -> str:
        from google.api_core.exceptions import ResourceExhausted
        from fastapi import HTTPException
        try:
            response = await self._model.generate_content_async(prompt)
        except ResourceExhausted:
            raise HTTPException(
                status_code=503,
                detail="Plan generation is temporarily unavailable — please try again shortly.",
            )
        return _strip_markdown(response.text)


# ── Shared helpers ────────────────────────────────────────────────────────────

def _strip_markdown(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` fences LLMs sometimes wrap responses in."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def get_llm_client() -> LLMClient:
    provider = os.environ.get("LLM_PROVIDER", "groq").lower()
    if provider == "anthropic":
        return AnthropicClient()
    if provider == "openai":
        return OpenAIClient()
    if provider == "gemini":
        return GeminiClient()
    return GroqClient()
