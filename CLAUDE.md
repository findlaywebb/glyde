# Glyde

A Python (FastAPI, JSON-first) backend + SvelteKit frontend, built **agentically**: the
deterministic gate stack — not human approval gates — is the source of truth (see
`docs/decisions/0001-agentic-gates.md`). One typed API surface, used identically by the UI
and by agents.

## Where the thinking lives

`docs/` is the canonical design vault. Read before non-trivial work:

- `docs/README.md` — index and reading order
- `docs/architecture.md` — module layout, the API surface, the boundary
- `docs/glossary.md` — canonical domain terms; no synonyms
- `docs/decisions/` — ADRs; add one for any boundary / port / public-API change

## Toolchain

uv workspace (Python 3.13, members under `backend/packages/`) · **ty is the sole type
gate** (no pyright/mypy) · ruff · import-linter · prek hooks · vulture (warn-only sweeps,
not a commit gate).

```bash
uv sync                  # one venv for the whole workspace
uv run pytest            # all tests (backend/tests/)
uv run ruff check .      # lint        (ruff format . to format)
uv run ty check          # types
uv run lint-imports      # boundary contract
prek run --all-files     # everything the commit hook runs
```

The gates are wired into prek + CI. **A red gate is the architecture speaking — fix the
code, never loosen a contract or budget to get green.** Contract changes are ADRs.

## The boundary rule

Dependencies point inward: `api → adapters → core`, core imports nothing outside itself.
See `BOUNDARIES.md`; enforced by import-linter + `backend/tests/architecture/`.

## Conventions (the non-inferable ones)

- **No ABC/Protocol until the 3rd real implementation** (rule of three). Prefer
  duplication over the wrong abstraction. Applies to shared type aliases and helpers too.
- **Soft budget 400 lines/file** (enforced by test). Over budget → **split into multiple
  files** along responsibility lines, optimised for agentic discovery (one concept per
  file); never trim, squeeze, or thin docstrings to fit — that defeats the signal.
- **Module + public-API docstrings are the agent contract** — purpose, key types,
  what it does *not* do, invariants. Written by hand; keep them current when behaviour
  changes. State designed gaps as capability facts ('no consumer yet'), never spec/roadmap
  numbers (enforced by an architecture test).
- **No `os.environ` / `os.getenv` in `core/`** — config is injected (enforced by test).
- Logging only, never `print` (enforced). `raise ... from exc`. `pathlib` over `os.path`.
- One canonical name per concept — check `docs/glossary.md` before introducing a term.
- Names say what a thing is: `record_store.py`, not `store.py`. Shallow nesting (≤3–4).

## Workflow

One feature = one spec dir = one branch = one PR (`specs/README.md` has the convention).

1. Scope into `specs/NNN-name/spec.md` — what + acceptance criteria.
2. Plan into `plan.md` (files to touch *and* to leave alone) — a **plan-reviewer agent**
   (fresh context, sceptical staff engineer) reviews it and **blocks** until it passes; no
   human checkpoint.
3. Implement autonomously against the plan, test-first; tick off `tasks.md`.
4. Review the diff against the plan. **Done = green CI + matches spec.**

Commit working checkpoints before stopping. Out-of-scope discoveries go to the backlog or
`docs/issues/`, not into the current diff.

## Sub-directory guides

- `backend/CLAUDE.md` — FastAPI / Pydantic-v2 / SQLite specifics
- `frontend/CLAUDE.md` — SvelteKit / Svelte-5-runes / typed-seam specifics
