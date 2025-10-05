from __future__ import annotations

"""OpenAI chat streaming helpers.

This module provides small helpers used by the Streamlit UI to stream
assistant outputs. It supports both the new `openai>=1.0` client-style API
and older `openai` SDKs so the app can run in different environments.

Main symbols:
- get_system_prompt() -> str
- stream_completion(prompt: str) -> Iterator[str]  # backwards compatible
- stream_messages(messages: list[dict]) -> Iterator[str]  # preferred for ongoing dialog

Messages are lists of dicts: {"role": "system"|"user"|"assistant", "content": str}
"""

import os
from typing import Iterator

try:
    # New SDK exposes OpenAI client class
    from openai import OpenAI as OpenAIClient
except Exception:  # pragma: no cover - openai optional until used
    OpenAIClient = None

try:
    # Older SDK exposes top-level openai module with ChatCompletion
    import openai as openai_legacy
except Exception:  # pragma: no cover
    openai_legacy = None


def get_system_prompt() -> str:
    return (
        "You are ArtRogue, an art museum chatbot inspired by Waldemar Januszczak. "
        "You respond to questions about artworks, artists, and museum collections with historical insight and cultural comparisons. "
        "Avoid a dry academic tone - be bold and conversational. If possible, include an unexpected detail or interpretation."
    )


def stream_completion(prompt: str) -> Iterator[str]:
    """Stream completion tokens from OpenAI (if available).

    Yields text chunks; if OpenAI isn't available or API key missing, yields a short fallback message.
    """
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
    if not api_key:
        yield "(No OpenAI API key set in OPENAI_API_KEY environment variable)"
        return

    # Prefer the new OpenAI client if available
    if OpenAIClient is not None:
        # New SDK: client reads key from env or accepts it in constructor
        os.environ.setdefault("OPENAI_API_KEY", api_key)
        try:
            client = OpenAIClient()
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": get_system_prompt()}, {
                    "role": "user", "content": prompt}],
                stream=True,
            )

            for event in stream:
                # event may be a dict-like or object; try a few ways to extract incremental text
                choices = None
                try:
                    choices = event.get("choices")
                except Exception:
                    choices = getattr(event, "choices", None)

                if not choices:
                    continue

                first = choices[0]
                delta = None
                if isinstance(first, dict):
                    delta = first.get("delta") or first.get("message") or first
                else:
                    delta = getattr(first, "delta", None) or getattr(
                        first, "message", None) or first

                text = None
                if isinstance(delta, dict):
                    text = delta.get("content") or delta.get("text")
                else:
                    text = getattr(delta, "content", None) or getattr(
                        delta, "text", None)

                if text:
                    yield text

        except Exception as e:
            yield f"(Error streaming from OpenAI (new client): {e})"
        return

    # Fallback: older openai module with ChatCompletion
    if openai_legacy is not None:
        try:
            openai_legacy.api_key = api_key
            resp = openai_legacy.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": get_system_prompt()}, {
                    "role": "user", "content": prompt}],
                stream=True,
            )

            for chunk in resp:
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                text = delta.get("content") or choices[0].get("text")
                if text:
                    yield text
        except Exception as e:
            yield f"(Error streaming from OpenAI (legacy): {e})"
        return

    # No OpenAI SDK installed
    yield "(OpenAI SDK not installed)"


def stream_messages(messages: list[dict]) -> Iterator[str]:
    """Stream a completion given a messages list (system/user/assistant)."""
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
    if not api_key:
        yield "(No OpenAI API key set in OPENAI_API_KEY environment variable)"
        return

    # Prefer new client
    if OpenAIClient is not None:
        os.environ.setdefault("OPENAI_API_KEY", api_key)
        try:
            client = OpenAIClient()
            stream = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                stream=True,
            )
            for event in stream:
                choices = None
                try:
                    choices = event.get("choices")
                except Exception:
                    choices = getattr(event, "choices", None)
                if not choices:
                    continue
                first = choices[0]
                delta = None
                if isinstance(first, dict):
                    delta = first.get("delta") or first.get("message") or first
                else:
                    delta = getattr(first, "delta", None) or getattr(
                        first, "message", None) or first
                text = None
                if isinstance(delta, dict):
                    text = delta.get("content") or delta.get("text")
                else:
                    text = getattr(delta, "content", None) or getattr(
                        delta, "text", None)
                if text:
                    yield text
        except Exception as e:
            yield f"(Error streaming from OpenAI (new client): {e})"
        return

    # Fallback legacy
    if openai_legacy is not None:
        try:
            openai_legacy.api_key = api_key
            resp = openai_legacy.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=messages,
                stream=True,
            )
            for chunk in resp:
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                text = delta.get("content") or choices[0].get("text")
                if text:
                    yield text
        except Exception as e:
            yield f"(Error streaming from OpenAI (legacy): {e})"
        return

    yield "(OpenAI SDK not installed)"
