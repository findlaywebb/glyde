"""LAN router scaffold — a route-less ``APIRouter`` the LAN unit fills later.

``lan_router`` carries ZERO path operations. Registering an empty router in the
app is OpenAPI-neutral: the committed ``docs/schemas/openapi.json`` is unchanged
now and stays unchanged when the LAN unit fills this file (it adds no path
operation either — the LAN token guard lives in the frontend proxy, not a server
route). Keeping the registration here means the frozen seam already reflects it.
"""

from __future__ import annotations

from fastapi import APIRouter

lan_router = APIRouter(tags=["lan"])
