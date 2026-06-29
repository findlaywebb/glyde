"""The ``glyde`` CLI surface: ``serve`` and ``export-openapi``.

Thin typer commands — they parse options, call into the api layer, and translate
domain errors into exit codes. Composition logic does not live here.

Key callables:
- ``app`` — the typer application wired as the ``glyde`` console script.
- ``serve`` — boot the FastAPI app under uvicorn on the configured host/port.
- ``export-openapi`` — write the app's OpenAPI schema to the committed artifact.

Invariants:
- Exit codes are pinned: ``0`` on success, ``2`` on bad input (a file/format
  error, printed as a plain message — never ``typer.BadParameter``/rich, whose
  terminal-width wrapping breaks substring assertions across local vs CI widths).
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
import uvicorn

from glyde.api.openapi_doc import canonical_openapi_json
from glyde.api.settings import get_settings

app = typer.Typer(
    name="glyde",
    help="Glyde — boot the API and manage the committed OpenAPI artifact.",
    add_completion=False,
)

_EXIT_BAD_INPUT = 2
_DEFAULT_OPENAPI_OUT = Path("docs/schemas/openapi.json")


@app.command()
def serve() -> None:
    """Boot the Glyde app under uvicorn on the configured host/port.

    Reads the bind host/port and db path from settings; the app's lifespan
    configures logging and runs pending migrations at startup.
    """
    settings = get_settings()
    uvicorn.run("glyde.api.app:create_app", factory=True, host=settings.host, port=settings.port)


@app.command(name="export-openapi")
def export_openapi(
    out: Annotated[
        Path,
        typer.Option("--out", help="Where to write the canonical OpenAPI JSON (repo-relative)."),
    ] = _DEFAULT_OPENAPI_OUT,
) -> None:
    """Write the app's OpenAPI schema to a committed JSON artifact (no server).

    Serialises ``create_app().openapi()`` deterministically (sorted keys, 2-space
    indent, trailing newline) so it backs the frontend type seam and the drift
    gate. Run from the repo root; the default lands at ``docs/schemas/openapi.json``.

    Args:
        out: Destination path; parent directories are created if absent.
    """
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(canonical_openapi_json(), encoding="utf-8")
    except OSError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=_EXIT_BAD_INPUT) from exc
    typer.echo(f"wrote {out}")


if __name__ == "__main__":
    app()
