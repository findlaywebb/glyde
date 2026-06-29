# Architecture

Glyde is a Python (FastAPI, JSON-first) backend + SvelteKit frontend, one typed API
surface used identically by the UI and by agents.

## Backend — hexagonal, dependencies point inward

A uv workspace of three packages under `backend/packages/`:

- `glyde.core` — domain models, ports (`glyde.core.ports`), pure logic. Imports nothing
  outside itself; no framework/IO, no clock, no id minting, no `os.environ`.
- `glyde.adapters` — concrete port implementations (the SQLite/WAL store). Imports `core`
  only. Synchronous and deterministic by contract.
- `glyde.api` — the FastAPI app, routers, request/response schemas (projections of core
  models), settings, the CLI, and the one clock-read + id-mint sites. Imports `core` and
  `adapters`.

The boundary is enforced by import-linter (`[tool.importlinter]` in `pyproject.toml`) and
the AST fitness tests in `backend/tests/architecture/`. See `BOUNDARIES.md`.

## Frontend — SvelteKit, typed seam

The browser and SSR `load`s call a generated `openapi-fetch` client. The SvelteKit
`adapter-node` server is the single front door: `hooks.server.ts` reverse-proxies `/api/*`
to FastAPI (stripping `/api`) and serves everything else. The app is same-origin, so it
needs no CORS. The frontend's own element boundary (routes → domains → {ui, api} → utils)
mirrors the backend's, enforced by eslint-plugin-boundaries + dependency-cruiser.

## The typed seam

FastAPI's OpenAPI document is exported to the committed `docs/schemas/openapi.json`
(`glyde export-openapi`). `openapi-typescript` generates `frontend/src/lib/api/schema.d.ts`
from it. Two drift gates keep both halves honest: a backend pytest check (the committed
artifact equals the live app) and a frontend `openapi-typescript --check`.

## Ports & adapters

- FastAPI: `127.0.0.1:8000` (configurable via `GLYDE_HOST` / `GLYDE_PORT`).
- SvelteKit dev: `5173`, proxying `/api` to the FastAPI origin.
- The proxy target is the only backend-origin knob: `GLYDE_API_ORIGIN`.
