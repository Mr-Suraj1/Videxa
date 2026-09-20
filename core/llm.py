"""Shared Mistral client configuration for Videxa chains."""

import os

from langchain_mistralai import ChatMistralAI


def get_llm(temperature: float = 0.3) -> ChatMistralAI:
    """Create the project's configured Mistral chat client."""
    return ChatMistralAI(
        model="mistral-small-latest",
        api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=temperature,
        timeout=60,
        max_retries=2,
        max_concurrent_requests=4,
    )
