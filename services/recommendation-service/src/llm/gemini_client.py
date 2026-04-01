"""Gemini 2.0 Flash LLM client with abstract interface for easy provider swapping."""
from __future__ import annotations
import abc
import os
import google.generativeai as genai


class LLMClient(abc.ABC):
    @abc.abstractmethod
    async def generate(self, prompt: str) -> str:
        ...


class GeminiClient(LLMClient):
    def __init__(self):
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        self._model = genai.GenerativeModel("gemini-2.0-flash")

    async def generate(self, prompt: str) -> str:
        response = await self._model.generate_content_async(prompt)
        return response.text


def get_llm_client() -> LLMClient:
    return GeminiClient()
