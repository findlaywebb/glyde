"""LAN serve — the ``0.0.0.0`` adapter-node front door, QR, and bearer-token guard.

``serve_lan`` is the delegate the ``serve --lan`` flag calls. It runs the FastAPI
app under uvicorn bound to loopback (the node proxy is its only client) and spawns
the built SvelteKit adapter-node server bound to ``0.0.0.0`` as the single
LAN-facing door. The node door reverse-proxies ``/api`` to loopback FastAPI (so
CORS is structurally absent) and enforces the CSRF-origin + bearer-token guard in
``hooks.server.ts``. Once both servers answer a readiness probe it renders a QR of
the LAN URL (carrying the token) for a phone to scan, then blocks until interrupted.

Key callables:
- ``serve_lan`` — orchestrate the two processes, print URL + QR + token, tear down.

What this module does NOT do:
- It adds NO FastAPI path operation and does NO token *validation* — the guard lives
  in the node proxy (``hooks.server.ts``); this module only mints the token and
  hands it to the node process through its environment.
- No business logic — it is a launcher.

Invariants:
- FastAPI binds loopback only; only the node door binds ``0.0.0.0``.
- The LAN origin is computed ONCE (the assay "triad"): the adapter-node ``ORIGIN``
  env, the QR payload, and the node door's CSRF compare value are the same string;
  a mismatch silently 403s every mutation.
- HTTPS-over-LAN degrades first (HTTPS via ``node:https`` + mkcert → plain-HTTP LAN
  → localhost). The token is a guard, not authentication.
"""

from __future__ import annotations

import logging
import os
import secrets
import shutil
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING

import segno
import typer

if TYPE_CHECKING:
    from glyde.api.settings import Settings

logger = logging.getLogger(__name__)

_LOOPBACK = "127.0.0.1"
_NODE_BIND = "0.0.0.0"  # the load-bearing LAN bind for the node front door
_PROBE_ATTEMPTS = 40
_PROBE_DELAY = 0.5
_PROBE_TIMEOUT = 1.0
_TERMINATE_GRACE = 5.0


def _detect_lan_ip() -> str:
    """Return this host's LAN IP via the UDP-connect trick (no packet is sent).

    Connecting a datagram socket to a public address makes the kernel pick the
    source IP it would route through, without emitting traffic. Degrades to
    loopback when there is no LAN (offline).
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return _LOOPBACK
    finally:
        sock.close()


def _frontend_dir() -> Path:
    """Return the frontend directory holding the built adapter-node server.

    Searches the working directory first (the documented "run from the repo root"
    path), then walks up from this module (the editable-install layout).

    Raises:
        RuntimeError: When no ``frontend/build/index.js`` is found — the build
            step (``npm run build``) has not run.
    """
    for base in (Path.cwd(), *Path(__file__).resolve().parents):
        candidate = base / "frontend"
        if (candidate / "build" / "index.js").is_file():
            return candidate
    raise RuntimeError(
        "frontend build not found — run `npm run build` in frontend/ before `serve --lan`"
    )


def _https_enabled(settings: Settings) -> bool:
    """Return True when HTTPS-over-LAN is configured with a cert and key."""
    return bool(settings.lan_https and settings.lan_cert_path and settings.lan_key_path)


def _child_env(overrides: dict[str, str]) -> dict[str, str]:
    """Return a copy of the parent environment with ``overrides`` applied.

    Args:
        overrides: Variables to set on top of the inherited environment.
    """
    env = dict(os.environ)  # noqa: TID251 - a launcher propagates the parent env to its child
    env.update(overrides)
    return env


def _node_command(frontend: Path, settings: Settings) -> list[str]:
    """Return the node argv for the front door (the HTTPS wrapper when enabled).

    Raises:
        RuntimeError: When the ``node`` binary cannot be located on the PATH.
    """
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("`node` not found on PATH — install Node >=22.19 to serve the LAN door")
    entry = "serve-lan-https.mjs" if _https_enabled(settings) else "build/index.js"
    return [node, str(frontend / entry)]


def _spawn_fastapi(settings: Settings) -> subprocess.Popen[bytes]:
    """Spawn loopback FastAPI under uvicorn (the node proxy is its only client)."""
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "glyde.api.app:create_app",
            "--factory",
            "--host",
            _LOOPBACK,
            "--port",
            str(settings.port),
        ]
    )


def _spawn_node(
    frontend: Path, settings: Settings, origin: str, token: str
) -> subprocess.Popen[bytes]:
    """Spawn the adapter-node front door bound ``0.0.0.0`` with the origin-triad env.

    Args:
        frontend: The frontend directory (the subprocess working directory).
        settings: Runtime settings (ports + optional HTTPS cert/key paths).
        origin: The single LAN origin string (adapter ``ORIGIN`` = QR = CSRF compare).
        token: The bearer token the node door asserts on ``/api`` mutations.
    """
    env = {
        "HOST": _NODE_BIND,
        "PORT": str(settings.lan_port),
        "ORIGIN": origin,
        "GLYDE_API_ORIGIN": f"http://{_LOOPBACK}:{settings.port}",
        "GLYDE_LAN_TOKEN": token,
    }
    if _https_enabled(settings):
        env["GLYDE_LAN_CERT_PATH"] = str(settings.lan_cert_path)
        env["GLYDE_LAN_KEY_PATH"] = str(settings.lan_key_path)
    return subprocess.Popen(_node_command(frontend, settings), cwd=frontend, env=_child_env(env))


def _unverified_context() -> ssl.SSLContext:
    """Return an SSL context that skips verification (local HTTPS readiness probe)."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def _probe_once(url: str, *, insecure: bool) -> bool:
    """Return True if the URL answers (any HTTP status), False if unreachable."""
    context = _unverified_context() if insecure else None
    try:
        with urllib.request.urlopen(url, timeout=_PROBE_TIMEOUT, context=context):
            return True
    except urllib.error.HTTPError:
        return True  # the server answered (e.g. a 404 root) — it is up
    except (urllib.error.URLError, OSError):
        return False


def _wait_until_ready(
    url: str, proc: subprocess.Popen[bytes], label: str, *, insecure: bool = False
) -> None:
    """Poll ``url`` until it answers, failing fast if ``proc`` dies first.

    Args:
        url: The readiness endpoint to poll.
        proc: The process expected to be serving it (checked for early exit).
        label: A human label for the process, used in error messages.
        insecure: Skip TLS verification (a self-signed mkcert HTTPS door).

    Raises:
        RuntimeError: When the process exits during startup or never answers.
    """
    for _ in range(_PROBE_ATTEMPTS):
        if proc.poll() is not None:
            raise RuntimeError(f"{label} exited during startup (code {proc.returncode})")
        if _probe_once(url, insecure=insecure):
            return
        time.sleep(_PROBE_DELAY)
    raise RuntimeError(f"{label} did not become ready at {url}")


def _announce(origin: str, token: str) -> None:
    """Print the LAN URL, a scannable QR, and the token (the QR encodes the token)."""
    url = f"{origin}/?token={token}"
    typer.echo("")
    typer.echo(f"Glyde is live on your LAN:  {origin}")
    typer.echo("Scan to open on your phone (the token is a guard, not a login):")
    typer.echo("")
    segno.make(url, error="m").terminal(out=sys.stdout, compact=True)
    typer.echo("")
    typer.echo(f"URL:    {url}")
    typer.echo(f"Token:  {token}")
    typer.echo("Reads are open; a mutation needs this token and the LAN origin.")
    typer.echo("Press Ctrl-C to stop.")


def _terminate(proc: subprocess.Popen[bytes]) -> None:
    """Terminate a child process, escalating to kill if it ignores SIGTERM."""
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=_TERMINATE_GRACE)
    except subprocess.TimeoutExpired:
        proc.kill()


def serve_lan(settings: Settings) -> None:
    """Serve the whole app to the LAN: loopback FastAPI behind a ``0.0.0.0`` node door.

    Spawns loopback FastAPI and the built adapter-node front door, waits for both to
    answer, renders the QR of the token-bearing LAN URL, and blocks until interrupted,
    tearing both processes down on exit.

    Args:
        settings: Runtime settings carrying the ports, token, and HTTPS knobs.
    """
    try:
        frontend = _frontend_dir()
    except RuntimeError as exc:
        typer.echo(str(exc))
        raise typer.Exit(code=1) from exc

    lan_ip = _detect_lan_ip()
    scheme = "https" if _https_enabled(settings) else "http"
    origin = f"{scheme}://{lan_ip}:{settings.lan_port}"
    token = settings.lan_token or secrets.token_urlsafe(32)

    logger.info("starting LAN serve: FastAPI loopback :%d, node door %s", settings.port, origin)
    api_proc = _spawn_fastapi(settings)
    node_proc = _spawn_node(frontend, settings, origin, token)
    try:
        _wait_until_ready(f"http://{_LOOPBACK}:{settings.port}/healthz", api_proc, "FastAPI")
        node_probe = f"{scheme}://{_LOOPBACK}:{settings.lan_port}/api/healthz"
        _wait_until_ready(node_probe, node_proc, "LAN front door", insecure=(scheme == "https"))
        _announce(origin, token)
        node_proc.wait()
    except KeyboardInterrupt:
        logger.info("shutting down the LAN servers")
    finally:
        _terminate(node_proc)
        _terminate(api_proc)
