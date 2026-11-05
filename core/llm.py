"""Shared Gemini client configuration for Videxa chains."""

import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableLambda

from core.gemini_retry import invoke_with_gemini_retry

_DEFAULT_MODEL = "gemini-3.7-flash"


def get_llm(temperature: float = 0.3) -> RunnableLambda:
    """Create the project's configured Gemini chat client."""
    model_name = os.getenv("GEMINI_MODEL", _DEFAULT_MODEL)
    model = ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=temperature,
        timeout=60,
        max_retries=0,
    )
    return RunnableLambda(lambda prompt: invoke_with_gemini_retry(model, prompt))
