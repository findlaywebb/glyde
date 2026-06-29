# Glyde

A Python (FastAPI) backend + SvelteKit frontend, built agentically. Scaffolded from the
`agentic-py-svelte` template.

## Setup

```bash
uv sync                          # one venv for the whole backend workspace
uv run glyde export-openapi      # generate docs/schemas/openapi.json (the typed-seam source)
cd frontend && npm install && npm run gen:api   # generate src/lib/api/schema.d.ts, then commit it
```

## Develop

```bash
uv run glyde serve               # FastAPI on 127.0.0.1:8000
cd frontend && npm run dev        # SvelteKit on :5173, proxying /api -> FastAPI
```

## Gates

```bash
uv run pytest                    # tests
uv run ruff check . && uv run ty check && uv run lint-imports
prek install && prek run --all-files
```

See `CLAUDE.md`, `BOUNDARIES.md`, and `docs/` for conventions and architecture.
