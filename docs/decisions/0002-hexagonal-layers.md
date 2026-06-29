# 0002 — Hexagonal layers, enforced by import-linter and AST tests

Status: accepted

## Context

Agentic development discovers code by reading it; a clean, machine-enforced dependency
direction keeps each layer's responsibility obvious and stops an agent from quietly wiring
a framework dependency into the domain.

## Decision

Three layers, dependencies pointing inward: `api → adapters → core`.

- `core` imports nothing outside itself — no framework, no IO library, no `os.environ`, no
  clock read, no id minting.
- `adapters` import `core` only, are synchronous, and every public class implements a `core`
  port.
- `api` is the one place the environment is read (pydantic-settings), the clock is read, and
  ids are minted.

This is enforced two ways: import-linter (`[tool.importlinter]` in `pyproject.toml`) for the
import graph, and AST fitness tests (`backend/tests/architecture/`) for the things
import-linter can't express (no `print`, no clock/uuid/random in pure layers, the file-size
budget, schema-field descriptions, the no-mock rule).

## Consequences

- Adding a new port is deliberate (rule of three: don't abstract before the third real
  implementation). A new cross-layer edge or port is itself an ADR.
- The architecture tests run before any package is importable (they parse source), so they
  fail fast and cheaply.
