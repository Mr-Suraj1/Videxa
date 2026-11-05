"""
Minimal live smoke test for the Gemini connection.

Run from the project root:
    .venv\\Scripts\\python.exe tests\\smoke_gemini.py

Requires GOOGLE_API_KEY in .env or the shell environment.
Makes exactly one real API call (step 4). All other checks are offline.
"""
import sys
from pathlib import Path

# Make project root importable when the script is run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import os
from dotenv import load_dotenv

load_dotenv()


def _ok(msg: str) -> None:
    print(f"OK   {msg}")


def _fail(msg: str) -> None:
    print(f"FAIL {msg}")
    sys.exit(1)


# ── 1. Key presence ───────────────────────────────────────────────────────────
key = os.getenv("GOOGLE_API_KEY")
if not key:
    _fail("GOOGLE_API_KEY is not set — add it to .env or the shell environment.")
_ok(f"GOOGLE_API_KEY present ({len(key)} chars)")

# ── 2. Model configuration ────────────────────────────────────────────────────
model_name = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")
_ok(f"GEMINI_MODEL = {model_name!r}")

# ── 3. Client construction (offline) ─────────────────────────────────────────
from core.llm import get_llm  # noqa: E402

llm = get_llm(temperature=0.0)
_ok("LLM client built")

# ── 4. Live text generation — exactly one API call ───────────────────────────
# Pass a plain string: BaseChatModel accepts str, list[BaseMessage], or PromptValue.
# Production chains always wrap get_llm() in a prompt template, so the LLM receives
# a ChatPromptValue. The smoke test calls llm.invoke() directly, so a plain string
# is the correct minimal input here — a bare HumanMessage is not a valid input type.
prompt = "Reply with the single word: hello"
print(f"     Calling {model_name}...")
response = llm.invoke(prompt)
text = response.content if hasattr(response, "content") else str(response)
# Newer Gemini Flash models return content as a list of blocks (text + thinking).
# Production chains use StrOutputParser() which handles this; the smoke test does not.
if isinstance(text, list):
    text = " ".join(
        block.get("text", "") if isinstance(block, dict) else str(block)
        for block in text
    ).strip()
if not text.strip():
    _fail("Response is empty.")
_ok(f"Response received ({len(text)} chars): {text!r}")

# ── 5. Auth error path — no API call ─────────────────────────────────────────
# Detection path in gemini_retry.py:
#   _http_status():      class name "Unauthenticated" → 401  (line 35)
#   _is_auth_failure():  status 401 ∈ {401, 403}  → True    (line 51)
#   invoke_with_gemini_retry: auth check runs BEFORE the 429/503 gate
#   → raises GeminiProviderError(category="auth", status_code=401)
#
# The class must be named exactly "Unauthenticated" to hit the class-name
# branch of _http_status. No extra attributes are needed.

from core.gemini_retry import GeminiProviderError, invoke_with_gemini_retry  # noqa: E402


class Unauthenticated(Exception):
    """Mirrors google.api_core.exceptions.Unauthenticated by class name only."""


class _BadKeyModel:
    def invoke(self, _prompt: object) -> None:
        raise Unauthenticated("Invalid API key.")


try:
    invoke_with_gemini_retry(_BadKeyModel(), "x")
    _fail("Expected GeminiProviderError for auth failure — none raised.")
except GeminiProviderError as exc:
    if exc.category != "auth":
        _fail(f"Wrong category {exc.category!r}, expected 'auth'.")
    if exc.status_code not in {401, 403}:
        _fail(f"Unexpected status_code {exc.status_code!r}, expected 401 or 403.")
    _ok(
        f"Auth failure → GeminiProviderError("
        f"category={exc.category!r}, status_code={exc.status_code})"
    )

print("\nSmoke test passed.")
