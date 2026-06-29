# Glyde backend

Python 3.13 · FastAPI · Pydantic v2 · SQLite (WAL). Layers live in
`packages/{core,adapters,api}` as uv workspace members — see root `BOUNDARIES.md`
before adding any import across them.

## Non-inferable specifics

- **Settings**: `pydantic-settings` `BaseSettings` lives in `glyde.api` (never `core`),
  injected via `Annotated[Settings, Depends(get_settings)]` with `@lru_cache`. Tests clear
  with `get_settings.cache_clear()`.
- **CLI is a thin surface**: `cli.py` parses options and maps errors to exit codes; the
  composition logic lives in the api layer. CLI errors a test asserts on are plain-echoed
  (`typer.echo(msg)` + `typer.Exit`), never `typer.BadParameter`/rich: rich wraps the
  message to terminal width, so a substring assertion passes on a wide local terminal and
  fails on CI's narrow one.
- **`root_path="/api"` + `servers=[{"url":"/api"}]`** on the `FastAPI(...)` constructor:
  routes stay declared bare (`/records`, `/healthz`); the SvelteKit `handle()` proxy strips
  `/api` before forwarding. The committed `docs/schemas/openapi.json` advertises the prefix
  via the explicit `servers=` arg (required — `root_path` alone doesn't populate `servers`
  in the in-process `create_app().openapi()` call). The app ships no CORS: every caller is
  same-origin (browser via `/api`, SSR `load` via `${url.origin}/api`, agents direct to the
  bare paths).
- **Routes**: every route declares `summary` and `description` — agents consume the
  OpenAPI schema; an undocumented route is invisible to them. A route that injects the
  store via `Depends` must import the port at **runtime** (`# noqa: TC001`), never under
  `TYPE_CHECKING` — FastAPI resolves `Depends` annotations via `get_type_hints` at runtime
  and a deferred import makes it mis-read the param as a query field.
- **API schemas vs domain models**: `glyde.api` request/response schemas are projections
  of `glyde.core` models, defined separately in the api package (`ApiModel` base:
  `frozen=True`, `extra="forbid"`, `from_attributes=True`). Never expose a core model
  directly as a response model.
- **Server stamps time**: timestamps are ISO-8601 UTC, set server-side via `clock.py`
  (`canonical_now`, the one clock read); `core`/`adapters` receive them as arguments.
- **Ids are minted at the api layer**: `core`/`adapters` never import `uuid` (enforced by
  the purity test); ids arrive as arguments.
- **SQLite**: WAL + `synchronous=NORMAL` + `foreign_keys=ON` + `busy_timeout` pragmas on
  every connect (one connect path in `db.py`). Forward-only migrations tracked by
  `PRAGMA user_version`; a `schema.sql` declarative anchor is kept equal by a test.
- **Tests**: `httpx.AsyncClient` + `ASGITransport` with `app.dependency_overrides`, not
  `TestClient`, not a live server. Tests live in `backend/tests/`, mirroring `src`.

## Testing discipline

- **Every test has a docstring stating what it proves** (ruff `D` enforces presence in
  tests deliberately). **Summary line only** — no Args/Returns/Raises in test docstrings.
- **No mocking.** Real objects + the in-memory store fake; the port contract suite
  (`tests/support/store_contract.py`) is what keeps the fake honest (verified-fake
  pattern). `unittest.mock` / `pytest-mock` are banned by an architecture test — a genuine
  third-party boundary earns an explicit allowlist entry there, nothing else does.
- **Fixtures**: function-scoped by default, no `autouse`, shallow; prefer factory builders
  (`tests/support/factories.py` — override only the field under test) over fixture chains.
  Group behaviour families in plain classes (no `unittest.TestCase`).
- **Warnings are errors** (`filterwarnings = ["error"]`), `xfail_strict`, and test order is
  randomised (`pytest-randomly`) — an order-dependent failure means coupled state: fix the
  coupling, never the order. Reproduce with the printed seed.
- **Golden values are pinned literals**, never recomputed by the code under test on both
  sides. Hypothesis properties cover algorithmic invariants vectors can't (idempotence,
  equivalence classes). `parametrize` carries `ids=`; error assertions pin the
  machine-readable `code`, not just the exception type.
- **Coverage**: `glyde.core` is pure logic — held at 100% branch. Don't extend that bar
  to adapters/api without a decision.
