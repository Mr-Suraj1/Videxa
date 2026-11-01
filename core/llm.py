"""Shared Mistral client configuration for Videxa chains."""

import os

from langchain_mistralai import ChatMistralAI
from langchain_core.runnables import RunnableLambda

from core.mistral_retry import invoke_with_mistral_retry


def get_llm(temperature: float = 0.3) -> RunnableLambda:
    """Create the project's configured Mistral chat client."""
    model = ChatMistralAI(
        model="mistral-small-latest",
        api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=temperature,
        timeout=60,
        # Keep retries in invoke_with_mistral_retry so Retry-After and quota
        # errors are handled explicitly rather than hidden in SDK retries.
        max_retries=0,
        max_concurrent_requests=4,
    )
    return RunnableLambda(lambda prompt: invoke_with_mistral_retry(model, prompt))
