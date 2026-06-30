"""Enrichment provider seam — the handoff point the enrich path owns later.

Key types:
- ``Enricher`` — the callable shape ``(raw_text) -> glyde_markdown`` an enrich
  pass implements.
- ``get_enricher`` — resolve an ``Enricher`` from settings, or ``None``.

The foundation ships the stub: ``get_enricher`` returns ``None`` (no key, no
provider), so ``compose_digest`` falls back to the deterministic parse and
``enrich: true`` simply no-ops. A later key-gated provider replaces this file's
body without touching any other foundation file.

What this module does NOT do:
- No model calls of its own; it only resolves the provider. The Anthropic key is
  injected via ``Settings`` (api layer), never read in ``core``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from glyde.api.settings import Settings

type Enricher = Callable[[str], str]


def get_enricher(settings: Settings) -> Enricher | None:
    """Return an enricher for ``settings``, or ``None`` (the deterministic path).

    Args:
        settings: Runtime settings carrying any provider key.

    Returns:
        ``None`` — the foundation ships no enricher, so ingestion always uses the
        deterministic parser. A later provider returns a callable when keyed.
    """
    return None
