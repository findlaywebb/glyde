# Glossary

One canonical name per concept; no synonyms. Check here before introducing a term, and add
the term here when you coin one.

- **Record** — the example domain entity shipped with the template (id, name, created_at).
  Replace it with the real domain vocabulary.
- **Port** — an abstract interface in `glyde.core.ports` that adapters implement.
- **Adapter** — a concrete port implementation in `glyde.adapters` (e.g. the SQLite store).
- **Canonical timestamp** — an ISO-8601 UTC string with a `+00:00` offset; sorts
  lexicographically in chronological order. The api layer is the one place it is produced.
- **Typed seam** — the generated `openapi-fetch` client + `schema.d.ts`, derived from the
  committed `openapi.json`. The frontend cannot drift from the API without a type error.
