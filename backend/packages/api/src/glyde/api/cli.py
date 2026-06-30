"""The ``glyde`` CLI: the handoff loop plus serving and the OpenAPI export.

Thin typer commands — they parse options, call into the api layer, and translate
domain errors into exit codes. Composition logic lives in ``compose_digest``.

Key callables:
- ``app`` — the typer application wired as the ``glyde`` console script.
- ``add`` — ingest a digest from a text arg, a file path, or piped stdin.
- ``list`` / ``read`` — list the library; flatten a stored digest to terminal
  prose (the command-verifiable fallback reader, zero frontend).
- ``serve`` — boot the app under uvicorn; ``--lan`` delegates to ``serve_lan``.
- ``export-openapi`` — write the app's OpenAPI schema to the committed artifact.

Invariants:
- Exit codes are pinned: ``0`` on success, ``2`` on bad input — printed as a plain
  message (never ``typer.BadParameter``/rich, whose width-wrapping breaks substring
  assertions across local vs CI terminal widths).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Literal

import typer
import uvicorn

from glyde.api.compose import ComposeDeps, ComposeRequest, compose_digest
from glyde.api.deps import bootstrap_migrations, get_now, open_digest_store
from glyde.api.enrich import get_enricher
from glyde.api.ids import new_id
from glyde.api.lan import serve_lan
from glyde.api.openapi_doc import canonical_openapi_json
from glyde.api.settings import get_settings
from glyde.api.slug import new_slug
from glyde.core import Digest, Pause, ProseSegment, StoreError

app = typer.Typer(
    name="glyde",
    help="Glyde — hand off text to a typed digest, then serve or read it.",
    add_completion=False,
)

_EXIT_BAD_INPUT = 2
_DEFAULT_OPENAPI_OUT = Path("docs/schemas/openapi.json")

_SourceKind = Literal["agent", "file", "cli", "paste", "pipe", "api"]


def _resolve_source(text: str | None) -> tuple[str, _SourceKind, str | None]:
    """Resolve CLI input to ``(content, source_kind, origin)`` or exit on no input.

    An existing file path becomes a ``file`` source; any other text arg is a
    literal ``cli`` source; otherwise non-tty stdin is a ``pipe`` source.
    """
    if text is not None:
        path = Path(text)
        if path.is_file():
            return path.read_text(encoding="utf-8"), "file", text
        return text, "cli", None
    if not sys.stdin.isatty():
        return sys.stdin.read(), "pipe", None
    typer.echo("no input: pass text, an existing file path, or pipe stdin")
    raise typer.Exit(code=_EXIT_BAD_INPUT)


def _flatten(digest: Digest) -> str:
    """Flatten a digest's IR to terminal prose (the fallback reader)."""
    parts: list[str] = []
    previous_was_prose = False
    for segment in digest.segments:
        if isinstance(segment, ProseSegment):
            if previous_was_prose:  # adjacent runs with no pause (e.g. heading -> body)
                parts.append("\n")
            parts.append(" ".join(token.text for token in segment.tokens))
            previous_was_prose = True
            continue
        previous_was_prose = False
        if isinstance(segment, Pause):
            if segment.reason == "paragraph":
                parts.append("\n\n")
            elif segment.reason != "block_ahead":
                parts.append("\n")
        else:
            lead = f" {segment.lead}" if segment.lead else ""
            body = "\n".join(f"  {line}" for line in segment.content.splitlines())
            parts.append(f"\n[{segment.kind}]{lead}\n{body}\n")
    return "".join(parts).strip()


@app.command()
def add(
    text: Annotated[str | None, typer.Argument(help="Text, or an existing file path.")] = None,
    name: Annotated[str, typer.Option("--name", help="The digest's semantic title.")] = "",
    tag: Annotated[list[str] | None, typer.Option("--tag", help="Repeatable tag.")] = None,
    *,
    enrich: Annotated[bool, typer.Option("--enrich", help="Request an enrich pass.")] = False,
) -> None:
    """Ingest a digest from a text arg, a file path, or piped stdin; print slug + URL."""
    if not name:
        typer.echo("a non-blank --name is required")
        raise typer.Exit(code=_EXIT_BAD_INPUT)
    settings = get_settings()
    bootstrap_migrations(settings)
    content, source_kind, origin = _resolve_source(text)
    request = ComposeRequest(
        name=name,
        text=content,
        segments=None,
        source_kind=source_kind,
        origin=origin,
        ingested_via="cli",
        tags=list(tag) if tag else [],
        enrich=enrich,
    )
    with open_digest_store(settings.db_path) as store:
        deps = ComposeDeps(
            store=store,
            now=get_now(),
            new_id=new_id,
            new_slug=new_slug,
            enricher=get_enricher(settings),
        )
        try:
            digest = compose_digest(request, deps)
        except StoreError as exc:
            typer.echo(exc.code)
            raise typer.Exit(code=_EXIT_BAD_INPUT) from exc
    typer.echo(digest.meta.name)
    typer.echo(digest.meta.slug)
    typer.echo(f"http://{settings.lan_host}:{settings.lan_port}/d/{digest.meta.slug}")


@app.command(name="list")
def list_library() -> None:
    """List the digest library newest-first (slug, name, word count, source)."""
    settings = get_settings()
    bootstrap_migrations(settings)
    with open_digest_store(settings.db_path) as store:
        digests = store.list_all()
    if not digests:
        typer.echo("(no digests yet)")
        return
    for digest in digests:
        meta = digest.meta
        typer.echo(
            f"{meta.slug}  {meta.name}  [{meta.token_count} words, {meta.provenance.source_kind}]"
        )


@app.command(name="read")
def read_digest(
    slug: Annotated[str, typer.Argument(help="The slug to read.")],
) -> None:
    """Flatten a stored digest to terminal prose (the zero-frontend fallback reader)."""
    settings = get_settings()
    bootstrap_migrations(settings)
    with open_digest_store(settings.db_path) as store:
        try:
            digest = store.get_by_slug(slug)
        except StoreError as exc:
            typer.echo(exc.code)
            raise typer.Exit(code=_EXIT_BAD_INPUT) from exc
    typer.echo(_flatten(digest))


@app.command()
def serve(
    *,
    lan: Annotated[bool, typer.Option("--lan", help="Serve to the LAN (delegates).")] = False,
) -> None:
    """Boot the Glyde app under uvicorn; ``--lan`` delegates to the LAN front door."""
    settings = get_settings()
    if lan:
        serve_lan(settings)
        return
    uvicorn.run("glyde.api.app:create_app", factory=True, host=settings.host, port=settings.port)


@app.command(name="export-openapi")
def export_openapi(
    out: Annotated[
        Path,
        typer.Option("--out", help="Where to write the canonical OpenAPI JSON (repo-relative)."),
    ] = _DEFAULT_OPENAPI_OUT,
) -> None:
    """Write the app's OpenAPI schema to a committed JSON artifact (no server).

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
