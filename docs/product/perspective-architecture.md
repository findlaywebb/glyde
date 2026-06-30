# Perspective — Systems architect (data contracts & storage)

_I own the data-first spine: one typed object the syntax parses into, storage persists, the API
serves, the reader renders. Get it right and every surface is a thin projection of it; get it
wrong and we pay in every consumer._

## The one move: there is exactly one Digest, and everyone speaks it

The product's trick — "hand off text, get a typed digest with provenance and a memorable
link" — only pays off if **the digest is a single typed object reused unchanged by the CLI,
API, MCP and reader**, not a CLI shape reshaped for the API reshaped for the UI. One Pydantic
model in `core`, persisted by `adapters`, projected once by `api`, flowed to the frontend
through the existing typed seam (`openapi.json` → `schema.d.ts`). The MCP tool returns the same
`Digest` the API does. That is the DRY north star and the whole reason to invest in the IR up
front.

The **syntax→IR parser is the only ingest path**, pure (`core`): text in, typed segments out,
deterministic. The prototype's `launch.py` segmentation is its embryo; when the reader joins the
app, it graduates into the core parser and *every* channel ingests through it.

## The Digest IR

A **Digest** = metadata + an ordered list of **segments**.

**Metadata (`DigestMeta`)** — `id` (opaque, api-minted, the relation-stable key), `slug` (the
memorable phrase, unique, the human/agent handle), `name` (agent-given title), `provenance`,
`created_at` (canonical UTC), `token_count`, `est_reading_time_s` (derived once at a baseline
wpm), `content_sha` (dedup + integrity), and `ir_version` (so the shape evolves without a
destructive migration).

**Provenance** is a first-class typed sub-object — `source_kind` (`handoff|file|cli|paste`),
`origin` (path, agent run id, URL), `producer` (the producing agent/model), `ingested_via`
(`cli|api|mcp`) — 1:1 with the digest and immutable, born with it.

**Segments** are a discriminated union:

- **ProseSegment** — `role` (`heading|body|list_item`) + `tokens: list[Token]`. The streamed
  body. Knowing where you are in the structure fights fatigue, so structure survives into the IR.
- **Block** — the pause-and-show family, `block_kind ∈ {code, table, diagram, quote, math,
  note, pause}`, with `content`, kind-specific fields (`lang` for code, rows for table, a
  ref+alt for diagram), and an optional `lead` (the prose runway sentence). A block is a single
  stop in the timeline. This is the block-pause spec's segment list, formalised and named.

**Token** = `{ text, kind: word|punct, emphasis: none|strong|em|code, hold?: float }`. The
streaming atom. **Emphasis is a token property, not a wrapping segment** — the reader can flash
an emphasised word harder or hold it longer. `hold` is an optional agent-authored dwell hint.

### What I am deliberately keeping OUT of the IR

- **ORP pivot index, pixel offsets, per-word flash duration** — functions of the user's wpm,
  font and mode, i.e. *render-time, per-user* concerns. Baking them in freezes them against
  settings changes and couples `core` to reading-science constants that belong in the reader.
  The IR is the *what* (a word, emphasised, stop here); the reader is the *how*.
- **Sentence-boundary micro-pauses** — reader-derived from punctuation, not stored per full stop.
- **"Reading settings used"** does not live on the digest. A digest is content; the wpm/mode is
  preference, and (later) one digest is read by many users at different settings. The settings
  *used for a given read* belong on the reading session (history) — a property of the event.

## Storage: one JSON blob per digest, four concepts

The reader always fetches a whole digest start-to-finish; nothing in v1 queries "all code blocks
across digests." So **segments are stored as the serialised IR (a JSON column on the digest
row)**, not normalised into segment rows — `model_dump_json` ↔ `model_validate_json`, one
round-trip site, no join-and-reassemble. SQLite JSON1 can index into it if a cross-digest query
ever appears (rule of three).

Four tables, on the existing forward-migration + `schema.sql`-anchor pattern:

- **digests** — `id` PK, `slug` UNIQUE, `name`, inline provenance columns (1:1, not its own
  table until lineage exists), `created_at`, `token_count`, `est_reading_time_s`, `content_sha`,
  `ir_version`, `owner_id`, and `segments` (the IR JSON).
- **preferences** — the reader config off localStorage into the typed surface so CLI/API/UI
  agree: wpm, mode, context, sizes, font, theme, ramp. Keyed by `owner_id`.
- **history** (reading sessions) — `digest_id` FK, `started_at`, `position` (segment index +
  token offset), `completed_at?`, `settings_snapshot`. Powers resume-on-phone, and is where
  "settings used" lives.
- Images/diagrams land as **content-addressed files in the data dir** (DB holds the hash/path),
  never BLOBs — keeps the DB small, lets the reader serve the file. Only when images arrive.

The IR taxonomy spans several files under `core/models/` (one concept per file — `digest.py`,
`segment.py`, `provenance.py`), never one giant `models.py`, per the 400-line budget.

## The memorable slug

Glyde's literary take on MLflow's adjective-animal: a **two-word `evocative-evocative` slug**
from a curated literary word-bank (`pale-fire`, `salt-marsh`, `hollow-lantern`). Two words, not
three — shorter is more memorable to say and type, the low-fatigue north star.

- **Corpus**: a curated word-bank drawn from public-domain novels (Gutenberg), shipped as a
  packaged offline asset (`importlib.resources`, like the migrations) — two pools of ~1k words →
  ~1M unique pairs before any suffix. Curated to dodge the classic unfortunate-pairing gotcha.
- **Minted at the api layer**, beside `ids.new_id` (the purity test forbids `random` inward):
  `new_slug(is_taken)` takes an injected collision-check, retries on the UNIQUE clash, and
  appends a short numeric suffix (`pale-fire-2`) only after K misses.
- **Mapping**: the slug is a stable *secondary* key, 1:1 with id. FKs point at `id`
  (relation-stable, opaque); the link `/d/pale-fire` resolves slug→digest. Regenerating a slug
  (import collision, profanity) leaves the id and every relation untouched.

## Local-first, and LAN to mobile

- **Storage location**: an OS app-data dir (`~/Library/Application Support/glyde/` on macOS,
  XDG on Linux), overridable via `GLYDE_DB_PATH` — not today's CWD `glyde.db`. Holds the DB,
  WAL/SHM, backups, and cached block images; the word-bank ships in the package.
- **LAN bind**: FastAPI stays on localhost behind the proxy, never exposed. `glyde serve --lan`
  binds the *SvelteKit front door* to `0.0.0.0` and prints the LAN URL **plus a QR code** (scan
  from the phone — low friction, on brand).
- **Auth**: a **single shared bearer token** minted on `--lan`, carried in the QR URL →
  localStorage → header; the `handle()` proxy asserts it on mutations (ADR-0003 flagged the CSRF
  gap). A guard, not authn — it stops the curious roommate, not an attacker on a hostile network,
  and we should say so. Mobile is mostly a *reader*, so the LAN mutating surface is small anyway.

## Design-for-now vs defer

**Now** (cheap to bake, expensive to retrofit): an `owner_id` column on every table defaulting
to a `"local"` sentinel — the local single-tenant DB becomes a degenerate case of the
multi-tenant one, and backfilling a tenant key across a JSON-blob store later is the migration
from hell. Plus `ir_version` + `content_sha`. The typed IR itself (one model, all channels) *is*
the hosted-ready move.

**Defer** (don't build; don't let it shape v1 beyond the owner key): real accounts / OAuth / API
keys (the local CLI and MCP run as the user; the shared-token LAN guard is the v1 ceiling),
cross-user sharing / ACLs / public hosted links, per-row encryption, and multi-device sync
(local→hosted is a CRDT-shaped problem — explicitly out of v1).

## Open questions for the human

- **Tokenise at ingest, or store raw prose and tokenise in the reader?** I chose ingest-time
  (CLI/API/MCP/UI can't disagree on word boundaries) at the cost of a fatter blob. The opposite
  keeps the IR text-light but ripples through every consumer — the one call that touches them all.
- **Can mobile (over LAN) *create* digests, or is it read-only?** Read-only shrinks the LAN
  attack surface to near nothing and matches the likely flow (laptop agents produce, phone
  consumes). "rsvp that" from the phone means the shared token must gate writes too.
- **Slug style: suffix-on-collision (`pale-fire`) or always-suffixed (`pale-fire-417`) like
  MLflow?** Always-suffixed never collides and drops the retry logic but reads less like a phrase.
  I picked the former — confirm the aesthetic.
- **Does provenance need multi-hop lineage in v1** (digest from digest from file), or is
  single-hop "where did this come from" enough? Single-hop is inline columns; lineage promotes
  provenance to its own table with a parent link.
- **Is "Digest" the right canonical noun** for the handed-off unit? It propagates into the
  glossary, the URL (`/d/{slug}`), the API path and the MCP tool names — worth fixing before the
  contract sets.
