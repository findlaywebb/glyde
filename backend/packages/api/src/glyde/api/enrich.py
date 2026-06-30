"""Enrichment provider seam — resolves the key-gated Anthropic enricher.

Key types:
- ``Enricher`` — the callable shape ``(raw_text) -> glyde_markdown`` an enrich
  pass implements.
- ``get_enricher`` — resolve an ``Enricher`` from settings when a key is present,
  or return ``None`` (the deterministic parse path).

When ``Settings.anthropic_api_key`` is set, returns a callable backed by the
Anthropic Haiku adapter (``glyde.adapters.enrich``). Without a key the function
returns ``None``, causing ``compose_digest`` to fall back to the deterministic
parser with no error.

What this module does NOT do:
- No model calls of its own — it delegates to the adapters layer.
- The Anthropic key is read from ``Settings`` here (api layer) and injected as
  an argument into the adapter; it is never read in ``core`` or ``adapters``
  themselves.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from glyde.adapters.enrich import enrich as _adapter_enrich

if TYPE_CHECKING:
    from collections.abc import Callable

    from glyde.api.settings import Settings

type Enricher = Callable[[str], str]


def get_enricher(settings: Settings) -> Enricher | None:
    """Return a key-gated enricher callable, or ``None`` when no key is configured.

    Args:
        settings: Runtime settings carrying the optional Anthropic API key.

    Returns:
        A callable ``(raw_text) -> glyde_markdown`` backed by the Haiku adapter
        when a key is present; ``None`` otherwise (deterministic parse path).
    """
    api_key = settings.anthropic_api_key
    if api_key is None:
        return None
    return lambda raw: _adapter_enrich(raw, api_key=api_key)
