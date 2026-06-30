# 0005 — The Digest IR: one discriminated-union contract across CLI, API, MCP, and UI

Status: accepted

The IR lives in `glyde.core.models` (one concept per file) and is projected to the wire by
`glyde.api.schemas`. Terms are canonicalised in `../glossary.md`.

## Context

Glyde's novelty is **handoff → store → read**, end to end: an agent (or the CLI) hands off a
wall of natural-language output and Glyde returns a named, traceable, low-fatigue digest. Four
surfaces touch that artifact — the CLI handoff, the typed HTTP API, a Phase-2 MCP server, and
the SvelteKit reader — and they must agree on its shape exactly, because the reader's pacing is
*derived from structure*: where to pause, what is a block (never streamed word by word), what an
agent emphasised. Carry only flat text and each surface re-invents that structure, the reader's
intent forks from the parser's, and the frontend has nothing typed to render.

The reading science (ADR-0004) draws a hard line the data model must respect: pixel-level pacing
maths (the pivot index, flash-ms, ramp) belong to the reader and the user's `Preferences`, not to
the content. So the contract has to be rich enough to drive a reader yet free of render maths, and
it has to be the *same* object for every surface — not parallel DTOs that drift.

## Decision

**One typed intermediate representation, defined once and shared by every surface.**

- **Defined once in `glyde.core` as Pydantic v2**, `frozen=True, extra="forbid"`, one concept per
  file (`token.py`, `segment.py`, `provenance.py`, `digest.py`, `preferences.py`). The parser
  parses *into* it, SQLite persists it (a single `model_dump_json` / `model_validate_json`
  round-trip, no segment-row joins), the API serves it, and the reader renders it.
- **`Segment` is a discriminated union on `type`**:
  `Annotated[ProseSegment | Pause | Block, Field(discriminator="type")]`. A reading timeline is an
  ordered `list[Segment]`. The three variants carry exactly what a reader needs and nothing it must
  recompute: `ProseSegment` a run of `Token`s with a structural `role`; `Pause` a `reason` plus a
  coarse `duration_scale`; `Block` a `kind` and raw `content` shown as a static card.
- **The IR carries the *what*, never the *how-long*.** A `Token` has `emphasis` and an optional
  coarse `hold` hint; a `Pause` has `reason` + `duration_scale`. None of these is milliseconds —
  the reader maps them to a dwell from `Preferences` and the cadence constants. This closes the
  IR/reader pacing fork by construction.
- **Reading settings are per-user `Preferences`, never digest content.** A digest carries at most
  an optional `reading_hint`. The same digest reads differently for different users and the same
  user's preferences apply to every digest.
- **Projected once to the wire by `glyde.api.schemas`** as named, one-per-variant views
  (`TokenView`, `ProseSegmentView`, `PauseView`, `BlockView`, `DigestView`, …). The wire segment
  union is itself a Pydantic discriminated union, so the OpenAPI document emits **`oneOf` of named
  `$ref`s with a sibling `discriminator`**, never an anonymous `anyOf`. That is what lets the typed
  seam (`schema.d.ts`) hand the frontend a clean `A | B | C` it can narrow on `type`.
- **Identity is minted at the api layer**, never in `core`: the opaque `id`, the memorable two-word
  `slug` (1:1 with `id`), and the canonical `created_at` timestamp. `core` stays pure — the derived
  counts (`token_count`, `est_reading_ms`, `content_sha`) are pure functions in `glyde.core.derive`,
  computed once at ingest and stamped onto `DigestMeta`.

## Consequences

- **The seam freezes because it is *real*, not stubbed.** Every surface codes against one Pydantic
  definition and one generated `schema.d.ts`; the two drift gates (the committed `openapi.json` vs
  the live app, and `openapi-typescript --check`) keep both halves honest. A Phase-2 MCP ingest path
  is a thin wrapper over the same `compose_digest`.
- **Adding a block `kind`, a token class, or a pause `reason` is an IR change** — it ripples through
  the parser, the projection, the seam, and the reader, and is an ADR-adjacent decision, not a local
  edit. That cost is the point: it keeps the surfaces in lockstep.
- **Designed gaps (capability facts, not roadmap):** `token.kind` is `word | punct` only — no
  frequency class yet, because there is no lexicon; the parser emits only `word` tokens.
  `linear_form` is carried but populated only when authored (no auto-linearisation). Pacing render
  maths are deliberately absent from the IR.
- A pre-segmented producer can `POST` `segments` directly instead of `text`; the contract is the
  same union either way, so an upstream that already has structure need not round-trip through
  Glyde-Markdown.

Supersedes nothing; it fills in the domain the template's placeholder `Record` entity stood in for
(now removed). The reader-side pacing split it depends on is ADR-0004; the same-origin serving it
ships over is ADR-0003.
