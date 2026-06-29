# docs/

The canonical design vault (an Obsidian vault). Read before non-trivial work.

Reading order:

1. `architecture.md` — module layout, the boundary, the API surface, the typed seam.
2. `glossary.md` — canonical domain terms; one name per concept, no synonyms.
3. `decisions/` — ADRs. Add one for any boundary / port / public-API change.

New design knowledge goes here (or an ADR), not into a personal vault. Schedules and
roadmap live in `specs/`, never in source docstrings (an architecture test enforces that).

Subfolders:

- `decisions/` — Architecture Decision Records (`NNNN-title.md`).
- `runbooks/` — operational playbooks (dependency updates, releases).
- `schemas/` — the committed `openapi.json` (generated; the frontend type seam's source).
- `issues/` — one markdown file per out-of-scope issue found while doing something else.
