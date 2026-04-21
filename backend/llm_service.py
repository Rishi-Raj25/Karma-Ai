"""OpenRouter GPT-4o-mini LLM service for Karma AI."""

import os
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

_session = requests.Session()
_session.headers.update({
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://karma-ai.app",
    "X-Title": "Karma AI",
})


def chat_completion(messages: list[dict], temperature: float = 0.7) -> str:
    """Generate a chat response using OpenRouter GPT-4o.

    Args:
        messages: List of message dicts with 'role' and 'content'.
        temperature: Sampling temperature (0-2).

    Returns:
        Assistant's response text.
    """
    url = f"{OPENROUTER_BASE_URL}/chat/completions"

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 300,
    }

    resp = _session.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    result = resp.json()
    return result["choices"][0]["message"]["content"]
