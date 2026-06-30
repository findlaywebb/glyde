"""Anthropic enricher adapter — raw text to Glyde Markdown via the Haiku model.

Key types:
- ``enrich`` — convert raw text to Glyde Markdown using the Anthropic Messages API.

The caller injects the API key; this adapter never reads the environment.
The optional ``client`` parameter allows injection of a hand-written fake during
unit tests so the adapter is exercised without a real API call.

What this module does NOT do:
- No key resolution — the caller provides ``api_key`` (injected from Settings via
  the api layer).
- No fallback — the caller wraps this call in a try/except and falls back to the
  deterministic parser on any failure.
- No async — the adapters layer is synchronous by design.
- No token or session management — every call is stateless.
"""

from __future__ import annotations

import logging

import anthropic
from anthropic.types import TextBlock

logger = logging.getLogger(__name__)

_MODEL = "claude-haiku-4-5"
_MAX_TOKENS = 4096
_TEMPERATURE = 0.0

_SYSTEM_PROMPT = (
    "Convert the raw agent or CLI output below into Glyde Markdown for a"
    " dyslexia-friendly digest reader.\n\n"
    "Rules:\n"
    "- Preserve all content verbatim and in order — do not summarise, omit,"
    " or paraphrase.\n"
    "- Use headings (#) for distinct section titles and topic shifts.\n"
    "- Wrap code in triple-backtick fences with a language label"
    " (```py, ```bash, etc.).\n"
    "- Wrap tabular data as pipe tables (| col | col |).\n"
    "- Separate logically distinct ideas with a blank line.\n"
    "- Use ==highlights== only for genuinely critical terms.\n"
    "- Output only Glyde Markdown — no preamble, no commentary, no metadata."
)


def enrich(
    raw: str,
    *,
    api_key: str,
    client: anthropic.Anthropic | None = None,
) -> str:
    """Convert raw text to Glyde Markdown using the Anthropic Haiku model.

    Args:
        raw: The raw agent or CLI output to structure.
        api_key: The Anthropic API key (injected by the caller, never read here).
        client: Optional pre-built Anthropic client; constructed from ``api_key``
            when ``None`` (allows injection of a hand-written fake in tests).

    Returns:
        Glyde Markdown with headings, fenced blocks, and blank-line separators.

    Raises:
        anthropic.APIError: On network or API-layer failure (caller catches all).
        ValueError: When the response contains no text block.
    """
    _client = client if client is not None else anthropic.Anthropic(api_key=api_key)
    message = _client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": raw}],
        temperature=_TEMPERATURE,
    )
    if not message.content:
        raise ValueError("enricher response contained no content blocks")
    block = message.content[0]
    if not isinstance(block, TextBlock):
        raise TypeError("enricher response first block is not a text block")
    return block.text
