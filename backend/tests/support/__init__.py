"""Shared test support: factory builders, pinned golden constants, and repo paths."""

from pathlib import Path

# The one canonical repo-root anchor for repo-relative test paths (e.g. the committed
# docs/schemas/openapi.json the OpenAPI drift test reads). Test modules import this rather
# than recomputing Path(__file__).parents[N], which is fragile to file moves and obscure.
# Kept dependency-free (no glyde imports) so the AST architecture checks can use it too.
REPO_ROOT = Path(__file__).resolve().parents[3]
