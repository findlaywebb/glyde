# Boundaries

One page: who owns what, who may import whom. The machine-readable version is
`[tool.importlinter]` in `pyproject.toml` + `backend/tests/architecture/` — **those checks
are the contract**; this page is the orientation read. Changing a boundary is an ADR
(`docs/decisions/`).

Hexagonal; **dependencies point inward**. The core knows nothing about where it runs.

| Layer | Workspace member | Owns | May import |
|---|---|---|---|
| `glyde.core` | `backend/packages/core` | Domain models, ports (`glyde.core.ports`), pure logic | nothing outside `core` |
| `glyde.adapters` | `backend/packages/adapters` | Concrete port impls: SQLite store, external clients | `core` only |
| `glyde.api` | `backend/packages/api` | FastAPI app, routers, request/response schemas, settings, CLI | `core`, `adapters` |
| `frontend/` | (SvelteKit) | UI | only the typed API surface (OpenAPI → `schema.d.ts`) |

Hard rules the checks enforce:

- `glyde.core` imports no framework or I/O lib (fastapi, uvicorn, sqlalchemy, aiosqlite,
  httpx) and never touches `os.environ` / `os.getenv` — config is injected.
- `glyde.core` and `glyde.adapters` are pure: no clock reads, no `uuid` minting, no
  module-level randomness; adapters are synchronous. Timestamps and ids arrive as
  arguments (the api layer is the one mint/clock site).
- No `print()` anywhere in `backend/packages/`; logging only.
- Soft file budget: 400 lines — a spike signals a god module; split it.
- Every public class in `glyde.adapters` implements a port from `glyde.core.ports`.

Public surface discipline: each layer's `__init__.py` exports only what is public and its
module docstring states purpose, non-goals, and invariants — keep both current; they are
the first thing an agent reads.
