"""LAN serve scaffold — the foundation ships localhost; the LAN unit fills the door.

``serve_lan`` is the delegate the ``serve --lan`` flag calls. The foundation stub
runs the FastAPI app under uvicorn on ``settings.host`` (localhost) — no node
spawn, no QR, no token. A later LAN unit replaces this body with the ``0.0.0.0``
adapter-node front door, the QR, and the token guard, without touching ``cli.py``
or any other foundation file (the ``--lan`` flag only delegates here).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import uvicorn

if TYPE_CHECKING:
    from glyde.api.settings import Settings


def serve_lan(settings: Settings) -> None:
    """Serve the app on localhost (the LAN unit fills the real LAN front door).

    Args:
        settings: Runtime settings carrying the bind host/port.
    """
    uvicorn.run("glyde.api.app:create_app", factory=True, host=settings.host, port=settings.port)
