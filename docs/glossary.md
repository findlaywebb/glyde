# Glossary

One canonical name per concept; no synonyms. Check here before introducing a term, and add
the term here when you coin one. Every IR term below names a Pydantic model (or field) in
`glyde.core.models`; keep this page equal to those symbols.

## The Digest IR

The one typed contract, defined in `glyde.core.models` and projected to the wire by
`glyde.api.schemas` (see ADR `decisions/0005-digest-ir.md`).

- **Digest** — the aggregate and Glyde's core artifact: a `meta` (`DigestMeta`) plus an
  ordered `segments` list (the reading timeline). Produced at handoff, persisted, and read.
- **DigestMeta** — a digest's relation-stable header: the api-minted opaque `id` (the stable
  key), the `slug`, the agent-given `name`, its `provenance`, the server-stamped `created_at`,
  and the values derived once at ingest — `token_count`, `est_reading_ms`, `content_sha` —
  plus `ir_version`, `owner_id`, `tags`, and an optional `reading_hint`.
- **Segment** — the ordered reading-timeline element: a discriminated union on `type` of
  `ProseSegment | Pause | Block` (`Annotated[..., Field(discriminator="type")]`). The reader
  streams the list in order.
- **ProseSegment** — a `Segment` variant (`type="prose"`): a run of `Token`s with a structural
  `role` (`heading` | `body` | `list_item`). The reader streams it word by word.
- **Pause** — a `Segment` variant (`type="pause"`): a felt beat between runs, carrying a
  `reason` (`clause` | `sentence` | `paragraph` | `block_ahead`) and a coarse `duration_scale`.
  It holds no milliseconds — the reader maps `reason` + `duration_scale` to a dwell.
- **Block** — a `Segment` variant (`type="block"`): non-streamed content shown as a static
  card, discriminated by `kind` (`code` | `table` | `image` | `quote` | `math` | `note`). Its
  raw `content` is shown verbatim, never flashed word by word; optional `lang` (code language),
  `lead` (the prose runway it follows), `alt` (image alt text), and `linear_form` (a spoken form
  for promoted math, authored-only in v1).
- **Token** — the streaming atom: a single `text` with a `kind` (`word` | `punct`), an
  agent-given `emphasis` (`none` | `strong` | `em` | `code`), and an optional coarse `hold` dwell
  hint (never milliseconds). v1 emits only `word` tokens — there is no frequency lexicon yet.
- **Provenance** — a single-hop record of where a digest came from and how it arrived:
  `source_kind` (`agent` | `file` | `cli` | `paste` | `pipe` | `api`), an optional `origin`
  locator (path, url, repo@sha, run-id), an optional `producer` (the agent/model label),
  `ingested_via` (`cli` | `api` | `mcp`), and an `enriched` flag. Not a multi-hop lineage or an
  audit log.
- **ReadingHint** — an optional per-digest suggestion of a reading mode (`suggested_mode`). A
  hint carried on the digest, distinct from the user's `Preferences`.
- **Preferences** — per-user reading settings keyed by `owner_id`, never stored on a digest:
  `mode` (default `guided`), `wpm`, `context`, sizes, `font`, `theme`, `ramp`. The reader's
  last-used `mode` persists here.

## Identity

- **id** — a digest's opaque, api-minted key; the relation-stable identifier. Internal; the
  shareable handle is the `slug`.
- **slug** — the memorable two-word link, `"{left}-{right}"`, drawn from two packaged word pools
  and minted at the api layer. The secondary UNIQUE key, 1:1 with `id`; `/d/{slug}` resolves a
  digest. On collision the minter retries fresh pairs, then appends an incrementing `-N` suffix.
- **name** — a digest's agent-given semantic title (non-blank), shown in the library. Distinct
  from the `slug` (the link) and the `id` (the opaque key).
- **Canonical timestamp** — an ISO-8601 UTC string with a `+00:00` offset; sorts
  lexicographically in chronological order. Stamped on `created_at`. The api layer is the one
  place it is produced.

## Glyde-Markdown

The reading syntax an agent writes; `parse_glyde_markdown` (`glyde.core.parsing`) parses it into
the Digest IR. A pure, deterministic text-to-segments transform. The authoring guide is
`product/glyde-handoff-authoring.md`.

- **Glyde-Markdown** — the markup that parses into segments. The markers below are its full v1
  surface; anything else is plain prose.
- **`#` heading** — a `ProseSegment` with `role="heading"`.
- **list item** — a line led by `-`, `*`, `+`, or `N.` becomes a `ProseSegment` with
  `role="list_item"`; consecutive items are separated by a `clause` pause.
- **paragraph break** — a blank line, parsed as a `Pause(reason="paragraph")`.
- **clause terminator** — `,` `;` or `:` (followed by whitespace or line end) ends a prose run
  and sets the following pause's `reason` to `clause`.
- **sentence terminator** — `.` `!` `?` or `…` (followed by whitespace or line end) ends a prose
  run and sets the following pause's `reason` to `sentence`. A terminator mid-token (e.g. the dot
  in `3.14`) is ordinary text.
- **fenced code** — ```` ``` ````-delimited lines become a `code` block, with the fence's tag as
  `lang`.
- **pipe table** — a run of consecutive `|`-led lines becomes one `table` block.
- **image** — a whole-line `![alt](src)` becomes an `image` block (`content` is the src, `alt` the
  alt text); covers diagrams and figures.
- **math** — a single-line `$$…$$` becomes a `math` block.
- **note** — `:::` … `:::`-fenced lines become a `note` block.
- **quote** — a run of consecutive `>` lines becomes one `quote` block.
- **inline emphasis** — `==strong==`, `` `code` ``, and `*em*` / `_em_` mark a `Token`'s
  `emphasis`. Spans do not nest; an unmatched delimiter is literal text.
- **lead** — the prose runway a `Block` follows: the nearest preceding prose run's text, set by
  the parser onto `Block.lead` (or null when no prose precedes the block). Every block is preceded
  by a `Pause(reason="block_ahead")`.

## Architecture

- **Port** — an abstract interface in `glyde.core.ports` that adapters implement.
- **DigestStore** — the persistence port (`glyde.core.ports`): `add`, `get_by_slug`, `list_all`,
  `get_preferences`, `put_preferences`. The SQLite adapter implements it; an in-memory fake (kept
  honest by the port contract suite) backs the tests.
- **Adapter** — a concrete port implementation in `glyde.adapters` (e.g. the SQLite
  `DigestStore`).
- **Typed seam** — the generated `openapi-fetch` client + `schema.d.ts`, derived from the
  committed `openapi.json`. The frontend cannot drift from the API without a type error.
