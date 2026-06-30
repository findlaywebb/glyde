# Glyde v1 — Authoritative Build Plan

_Synthesised from `V1-ENGINEERING-CTO.md` (sequencing/risk) and `V1-ENGINEERING-STAFF.md`
(design/decomposition), reconciled against `SCOPING.md`, the five `perspective-*.md`,
`open-questions.md`, `specs/001-block-pause/`, the `prototype/` reader, and the real
backend + frontend source. This file is the single source of truth for the overnight build.
A fresh agent in an isolated git worktree executes one unit below with **no further
questions**: every decision is made here, every file is named, every verify command is exact._

> This is an **agent-facing execution doc**. Em-dashes, spec references, and density are fine
> here (do not run emdash-audit on it). It is the brief F0 and every fan-out unit code against.

---

## 0. How to use this document

1. Read §1 (locked scope) and §2 (the four binding decisions) — they are HARD constraints.
2. Read §3 (the CTO↔Staff reconciliation) so you know which plan won where, and why.
3. Read §4 (the Digest IR) — the one typed contract everything codes against.
4. Read §5 (cross-cutting rules) — the gates, the boundary, the handoff invariant.
5. Find your unit in §7 (FOUNDATION) or §8 (fan-out). Build ONLY your `owned_paths`.
6. Cross-check §9 (file-ownership map) — if a path is not yours, you must not edit it.
7. Run your unit's exact verify recipe. Done = your recipe is green AND §10 holds.

---

## 1. Locked scope (v1, overnight)

Glyde is the **digest layer for the agent-output firehose**, for the dyslexic engineer who
works with coding agents. An agent or the CLI hands off a wall of natural-language output and
gets back a **named, traceable, low-fatigue digest** with a speakable slug, kept in a personal
library. v1 is N=1 dogfood: success = the builder stops reading raw agent output in the terminal.

The novelty is **handoff → store → read**, end to end, on **one typed IR**. v1 ships:

- The **Digest IR** (the keystone), the **Glyde-Markdown → IR parser** (pure, in `core`), the
  **DigestStore + SQLite** adapter, the **memorable two-word slug**, the **typed HTTP API**
  (`POST/GET/list /digests`, `GET/PUT /preferences`) with the regenerated **typed seam**.
- The **CLI handoff** (`glyde add` text-arg / stdin / file, plus `glyde list`) — the headline.
- The **reader, ported to SvelteKit** (mobile-first, consuming the IR through the typed seam):
  **all three modes** (RSVP red-pivot, Guided sweep, Fading trail), **default Guided**, **last-
  used mode persisted and restored**, and **full spec-001 blocks** (cue, re-show, grid, image,
  math, code/table pause-and-show, highlighting).
- **Preferences** (server-backed + localStorage mirror), a **minimal library home**,
  **LAN-to-mobile** serve (QR + bearer token, phone read-only), and a **gated Haiku-enrich**
  ingestion path (STRETCH, isolated, key-gated, deterministic fallback, cut first).

Phase 2 (NOT in v1): MCP server, rich library (read-state/search/grouped feed), reading
history wiring, frequency lexicon, the agent skill + prompt library. Hosted/multi-user: Later.

---

## 2. The four binding decisions (HARD constraints)

1. **Reading modes — ship all three. Default = Guided sweep.** The reader MUST persist the
   user's last-used `mode` into `Preferences` and restore it on next open. RSVP and Fading are
   one switch away. (Overrides the panel's "evidence default"; this is the dyslexic primary
   user's lived-preference call, realised as: ship Guided as the first-run default, persist what
   they actually pick.)
2. **Blocks — implement `specs/001-block-pause` IN FULL.** Block-ahead cue, re-show-last,
   rendered table grid, image cards, math cards, code/table pause-and-show, highlighting. Not
   deferred. (Relief valve if the night slips: syntax-highlighting *quality* and ClearSpeak math
   *linearisation* are spec-001's own stated out-of-scope line — a static legible monospace code
   card and a `linear_form`-or-raw math card satisfy v1. Dropping a block *kind* does not.)
3. **The reader is PORTED to SvelteKit** (the typed seam, mobile-first), consuming the typed API
   / Digest IR. `prototype/reader.html` is **reference only**; the shipped reader is the
   SvelteKit app under `frontend/src/lib/domains/reader/` + `routes/d/[slug]/`.
4. **Handoff = CLI only** for v1 (`glyde add`: text arg | stdin pipe | file path). `POST /digests`
   is shaped so a Phase-2 MCP server is a thin wrapper. A **Haiku-enrich** path (raw text →
   Haiku → Glyde Markdown) ships as an **isolated, mockable, key-gated** unit with graceful
   fallback to deterministic parsing when no key is present; it is a **STRETCH** that may drop if
   it threatens the night. The Anthropic key is injected via an adapter/Settings, **never read in
   `core`**.

---

## 3. CTO ↔ Staff reconciliation (explicit rulings)

Both engineering docs agree on the spine: the Digest IR is the keystone and freezes first; the
typed seam (`openapi.json → schema.d.ts`) is the second chokepoint; fan-out happens in
file-disjoint worktrees against a frozen seam; F (shell) solely owns the shared frontend shell;
reader↔cards meet at a typed prop contract; Haiku is the isolated, cut-first stretch. Where they
diverge, this plan rules as follows.

| Topic | CTO position | Staff position | **Ruling (this plan)** |
|---|---|---|---|
| **Foundation scope** | Phase 0 = models + schema projection + **stub** routes + seam; parser (A) and store (B) fan out **after**, then a serial "wire real parser+store + re-run seam" pass | F0 = the **whole real backend vertical** (IR + parser + slug + store + compose + real routes + seam) lands once | **Staff.** F0 is the full real backend, serial, first. The frontend only consumes `schema.d.ts` + a running server, so a *real* seam in F0 lets the frontend start no later than a stubbed one would — and it removes the stub-then-rewire re-integration pass the CTO itself files as risk #3. The seam is frozen because it is *real*, not because it is stubbed. |
| **CLI placement** | Worktree C (with routes) | Unit B1 (separate) | **Fold `glyde add`/`list` into F0.** It shares `compose_digest` (F0's), is thin, closes the end-to-end loop (a self-verifying foundation), and avoids two units contending on `cli.py` — the single command-registration file. |
| **Reader decomposition** | 2 units: D (engine+3 modes) + E (blocks) | 5 units: R1–R5 | **Hybrid: 5 file-disjoint reader units with linear deps** (R-CORE engine+contract → R-MODES / R-BLOCKS / R-CHROME in parallel → R-STAGE integrates). The composing file lives in exactly one unit (R-STAGE), which `depends_on` the pieces it imports. Maximises parallelism on the longest pole without a shared composing file. |
| **Library** | Bundled into F (shell+library+LAN) | Unit L1 owns `routes/+page.*` | **Separate `LIB` unit owns the new root route.** F0 *deletes* the template's Record-coupled `routes/+page.{ts,svelte}`; `LIB` *creates* the digest home. Delete→create, not a shared edit (see §5.4). Minimal feed only; rich library is Phase 2. |
| **Block kinds** | code/table/image/note (+static math) must-land | `code/table/image/diagram/math/quote/note` | **`code, table, image, quote, math, note`** (the SCOPING/glossary set). `image` covers diagrams and figures (it is the `![alt](src)` card); drop a separate `diagram` kind. |
| **`est_reading` field** | (defers to IR) | `est_reading_ms` (compose computes `count/wpm*60000`) | **`est_reading_ms: int`** (overrides SCOPING's `est_reading_time_s`). The reader and dwell maths are millisecond-native; one ms field removes unit ambiguity. The library formats it ("~2m 14s"). |
| **`tags`** | — | `tags?` on the create request | **Keep `tags: list[str] = []` on `DigestMeta`** (stored as a JSON column), populated by the repeatable CLI `--tag`. Cheap, hosted-ready, honours the locked CLI flag; the rich library that *uses* tags is Phase 2. |
| **Pacing computation** | (reader-side dwell) | reader computes `dwell_ms` client-side from `Preferences`; IR carries only coarse signals | **Reader-side.** The IR carries the *what* (emphasis, `Pause.reason` + `duration_scale`, token `kind`, optional `hold`); the reader (R-CORE) computes pivot index + `dwell_ms` from `Preferences` + the science constants. This is the locked SCOPING line and ADR-0004. (The accessibility perspective's "compute server-side into the IR" is explicitly NOT taken.) |
| **`list` projection** | (counts on list) | `list_meta()` returns `list[DigestMeta]` | **`DigestStore.list_all() -> list[Digest]` newest-first**; the list route computes `counts{words, blocks_by_kind}` from each digest's segments. At N=1 loading full digests for the list is fine; a meta-only projection is a Phase-2 perf optimisation (no consumer-perf need yet). |

**Cut order (the relief valves, in order overboard):** (1) Haiku-enrich (`HAIKU`); (2) LAN
niceties (`LAN` degrades to localhost, no token guard); (3) block *polish* (highlighting quality,
math linearisation) — never a block *kind*. Protect the **IR + seam freeze (F0)** and the
**SvelteKit reader (R-*)** above all; those are what the night turns on.

**The headline's safety net (a real fallback tier BELOW the SvelteKit reader).** SCOPING's slip plan
was "serve injected prototype IR / flattened prose"; this plan keeps it as an executable tier, not a
deleted net. **F0 ships `glyde read <slug>`** — `store.get_by_slug` then flatten the stored IR to
terminal prose (prose runs joined; each `Pause` a line break, a paragraph a blank line; each `Block`
printed as `[<kind>] {lead}` then its `content` indented) — so even if **every** R-* unit slips or is
cut, `glyde add` → `glyde read` still demonstrates handoff → store → read end to end,
**command-verifiably with zero frontend**. The richer degraded option is to point the reference
`prototype/reader.html` at a stored digest's flattened prose via an injected IR JSON. Neither blocks
the SvelteKit reader; both exist so the headline is never zero. **If the reader itself slips** (not a
clean cut), shed in this order: Fading polish → the RSVP context window → fall to `glyde read` — and
never a block *kind* or the IR.

---

## 4. The Digest IR (the single typed contract)

Defined **once** as Pydantic v2 in `glyde.core.models` (one concept per file, `frozen=True,
extra="forbid"`), projected once by `glyde.api.schemas`, mirrored to the frontend by the typed
seam (`glyde export-openapi` → `openapi.json` → `npm run gen:api` → `schema.d.ts`). The reading
syntax parses **into** it, SQLite persists it, the API serves it, the SvelteKit reader renders it.

### 4.1 Core models (`core/models/`)

```python
# token.py — the streaming atom
class Token(BaseModel):                 # frozen, extra=forbid
    text: str
    kind: Literal["word", "punct"] = "word"
    emphasis: Literal["none", "strong", "em", "code"] = "none"
    hold: float | None = None           # optional coarse agent dwell hint — NOT milliseconds

# segment.py — the ordered reading timeline element (discriminated union on `type`)
class ProseSegment(BaseModel):
    type: Literal["prose"] = "prose"
    role: Literal["heading", "body", "list_item"] = "body"
    tokens: list[Token]

class Pause(BaseModel):
    type: Literal["pause"] = "pause"
    reason: Literal["clause", "sentence", "paragraph", "block_ahead"]
    duration_scale: float = 1.0         # coarse beat weight; the reader maps reason+scale → ms

class Block(BaseModel):
    type: Literal["block"] = "block"
    kind: Literal["code", "table", "image", "quote", "math", "note"]
    content: str                        # raw block content — NEVER streamed word-by-word
    lang: str | None = None             # code language
    lead: str | None = None             # the prose runway sentence it follows
    alt: str | None = None              # image alt (image covers diagrams/figures)
    linear_form: str | None = None      # spoken form for promoted math (None in v1 unless authored)

Segment = Annotated[ProseSegment | Pause | Block, Field(discriminator="type")]

# provenance.py — "what produced this, and how it got here" (1:1, immutable, single-hop)
class Provenance(BaseModel):
    source_kind: Literal["agent", "file", "cli", "paste", "pipe", "api"]
    origin: str | None = None           # path | url | repo@sha | run-id | session
    producer: str | None = None         # the producing agent/model label
    ingested_via: Literal["cli", "api", "mcp"] = "cli"
    enriched: bool = False

# digest.py
class ReadingHint(BaseModel):
    suggested_mode: Literal["rsvp", "guided", "fading"]

class DigestMeta(BaseModel):
    id: str                             # opaque, api-minted; the relation-stable key
    slug: str                           # memorable two-word link; UNIQUE; 1:1 with id
    name: str = Field(min_length=1)     # agent-given semantic title
    provenance: Provenance
    created_at: str                     # canonical ISO-8601 UTC, api-stamped
    token_count: int                    # derived once at ingest (count of word tokens)
    est_reading_ms: int                 # derived once at BASELINE_WPM (300)
    content_sha: str                    # dedup + integrity (sha256 of source)
    ir_version: int = 1
    owner_id: str = "local"
    tags: list[str] = Field(default_factory=list)
    reading_hint: ReadingHint | None = None

class Digest(BaseModel):
    meta: DigestMeta
    segments: list[Segment]

# preferences.py — per-user config, keyed by owner_id (NEVER on the digest)
class Preferences(BaseModel):
    owner_id: str = "local"
    mode: Literal["rsvp", "guided", "fading"] = "guided"   # DEFAULT guided; last-used persisted
    wpm: int = 300
    context: Literal["off", "ab", "line", "sentence"] = "ab"
    ctx_scale: float = 0.7
    chunk: int = 1
    size_px: int = 64
    letter_spacing_em: float = 0.04
    font: Literal["atkinson", "lexend", "opendyslexic", "system", "serif", "mono"] = "atkinson"
    theme: Literal["dark", "light", "sepia"] = "dark"
    ramp: bool = True
```

**Designed boundaries (capability facts, not roadmap):** pacing *render maths* (pivot index,
flash-ms, pixel offsets) are NOT in the IR — the reader computes them from `Preferences` + the
science constants. Reading settings are per-user `Preferences`, never digest content; a digest
carries at most the optional `reading_hint`. `token.kind` is `word|punct` only in v1 (no
`number`/`low_freq` class yet — no frequency lexicon). `linear_form` is carried but only an
authored value populates it (no auto-linearisation yet).

### 4.2 Pure derivation (`core/derive.py`)

`core` mints no id/clock/random, but pure derivation is fine (`hashlib` is stdlib, allowed):

- `count_tokens(segments) -> int` — number of `Token` with `kind == "word"` across all prose.
- `content_sha(source: str) -> str` — `sha256` hex of the canonical source text (utf-8). For
  pre-segmented input with no text, the caller passes the canonical segments JSON.
- `estimate_reading_ms(token_count, wpm) -> int` — `round(token_count / wpm * 60000)`.
- `BASELINE_WPM = 300` constant.

### 4.3 Persistence (`adapters/sqlite/`, migration `0002_digests.sql`)

Forward-only migration on the existing `PRAGMA user_version` runner. **0001 stays untouched**;
0002 creates the new tables and **`DROP TABLE records`** (greenfield, no data); `schema.sql` (the
declarative anchor) is rewritten to the final cumulative state (no `records`). The schema
convergence test then passes (both paths end identically).

```sql
CREATE TABLE digests (
  id TEXT PRIMARY KEY, slug TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
  prov_source_kind TEXT NOT NULL, prov_origin TEXT, prov_producer TEXT,
  prov_ingested_via TEXT NOT NULL, prov_enriched INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL, token_count INTEGER NOT NULL, est_reading_ms INTEGER NOT NULL,
  content_sha TEXT NOT NULL, ir_version INTEGER NOT NULL DEFAULT 1,
  owner_id TEXT NOT NULL DEFAULT 'local', tags TEXT NOT NULL DEFAULT '[]',
  reading_hint TEXT, segments TEXT NOT NULL);           -- segments = model_dump_json(segments)
CREATE INDEX digests_created_at ON digests(created_at);
CREATE TABLE preferences (owner_id TEXT PRIMARY KEY, prefs TEXT NOT NULL);   -- Preferences JSON
CREATE TABLE history (    -- scaffolded now, NO v1 code path (wired Phase 2: resume + settings-used)
  id TEXT PRIMARY KEY, digest_id TEXT NOT NULL REFERENCES digests(id),
  owner_id TEXT NOT NULL DEFAULT 'local', started_at TEXT NOT NULL,
  segment_index INTEGER NOT NULL DEFAULT 0, token_offset INTEGER NOT NULL DEFAULT 0,
  completed_at TEXT, settings_snapshot TEXT);
```

DB lives in the **OS app-data dir** (`platformdirs.user_data_dir("glyde")`), `GLYDE_DB_PATH`
overrides — not today's CWD `glyde.db`. The store serialises via `model_dump_json` /
`model_validate_json` (one round-trip; no segment-row joins).

### 4.4 The store port (`core/ports/digest_store.py`) + errors

`DigestStore(ABC)` (replaces `RecordStore` — the established store seam, consistent with the
template's existing ABC; not a speculative new abstraction):

- `add(digest: Digest) -> None` — raises `DuplicateSlugError` on a slug clash.
- `get_by_slug(slug: str) -> Digest` — raises `UnknownDigestError` if absent (never `None`).
- `list_all() -> list[Digest]` — newest-first (by `created_at` desc, then `id`).
- `get_preferences(owner_id: str) -> Preferences` — returns defaults if none stored.
- `put_preferences(prefs: Preferences) -> None` — upsert by `owner_id`.

Errors (`core/ports/errors.py`): `StoreError` base; `UnknownDigestError(code="unknown_digest")`,
`DuplicateSlugError(code="duplicate_slug")`. The api maps `unknown_digest → 404`,
`duplicate_slug → 409`.

### 4.5 The API surface (`api → adapters → core`, bare paths proxied under `/api`)

- `POST /digests` ← `CreateDigestRequest{ name, text: str | None, segments: list[Segment] | None,
  source_kind, origin?, producer?, ingested_via?, tags?, enrich: bool = False }` → **201**
  `DigestView` (full IR). Exactly one of `text` / `segments` is required.
- `GET /digests` → `list[DigestListItemView]` (`meta` + `counts{words, blocks_by_kind}`),
  newest-first.
- `GET /digests/{slug}` → `DigestView` | 404.
- `GET /preferences?owner_id=local` → `PreferencesView`; `PUT /preferences` ← `PreferencesView`
  → `PreferencesView`. **PUT is full-replace** (upsert by `owner_id`; the body becomes the stored
  row). `PreferencesView` carries a **default for every field** (mirroring `Preferences`, §4.1), so a
  partial body validates under `extra="forbid"` (forbid rejects *unknown* keys, never *missing* ones —
  missing fall to defaults) and returns the full object. Because it is full-replace, the **PREF client
  always sends the complete `Preferences` object** on every change (never a partial), so no field is
  silently reset and the last-used `mode` survives the round-trip.
- Every route declares `summary` + `description` (the OpenAPI schema is the agent contract).
  Errors flow through the one app-level `StoreError → {code, message}` handler.
- **Named wire schemas (seam clarity, so reader units get clean types).** The projections are named
  one-per-variant — `TokenView`, `ProseSegmentView`, `PauseView`, `BlockView`, `DigestView`,
  `DigestListItemView{ meta, counts }`, `PreferencesView` — so each becomes a named
  `components['schemas'][…]` member in `schema.d.ts`. The wire segment union is a **Pydantic v2
  discriminated union** — `SegmentView = Annotated[ProseSegmentView | PauseView | BlockView,
  Field(discriminator="type")]`, each variant carrying a `Literal[…]` `type` tag — so
  `DigestView.segments.items` renders in the OpenAPI document as **`oneOf` of named `$ref`s with a
  sibling `discriminator` (`propertyName: "type"`, non-empty `mapping`)**, never an anonymous inline
  object and never a bare `anyOf`. (PROBE-VERIFIED: a discriminated union serialises as `oneOf`; drop
  the discriminator and FastAPI emits `anyOf` with no discriminator — the exact regression the §7 seam
  test catches.) R-CORE aliases the three named members into its `SegmentView` union in `types.ts`
  (§5.7); the **`.d.ts` cannot prove this** — `openapi-typescript` collapses both `oneOf` and `anyOf`
  into the same TS `A | B | C` — so the discriminator assertion is made on the **exported
  `openapi.json`, not the `.d.ts`** (§7). No reader unit ever hand-aliases an anonymous union.

**`compose_digest` is the one composition function the CLI and the route share** (`api/compose.py`).
To respect `max-args = 6`, it takes two bundles:

```python
def compose_digest(req: ComposeRequest, deps: ComposeDeps) -> Digest: ...
# ComposeRequest: name, text, segments, source_kind, origin, producer, ingested_via, tags, enrich
# ComposeDeps:    store, now (str), new_id (Callable), new_slug (Callable), enricher (Enricher | None)
```

It: optionally `enrich(text)` only when `enrich AND deps.enricher AND text has no structure
markers` (wrapped `try/except → raw`); parse `text → segments` via `parse_glyde_markdown` (else use
`segments`); mint `id` (`new_id`), `slug` (`new_slug(is_taken=store-closure)`); stamp `created_at`
(`now`); derive `token_count`, `est_reading_ms`, `content_sha`; build `Digest`; `store.add`; return.
The MCP server (Phase 2) is a thin wrapper over this same call.

### 4.6 The slug (`api/slug.py`, beside `ids.new_id`)

`new_slug(is_taken: Callable[[str], bool], *, rng: random.Random | None = None, k: int = 8) -> str`.
Two curated public-domain word pools (~200×200 ≈ 40k pairs) shipped as a packaged asset
(`importlib.resources.files("glyde.api") / "wordbank" / {left,right}.txt`, like migrations). Picks
`f"{a}-{b}"`; on `is_taken` retries up to `k`, then appends `-N` (suffix-on-collision). Minted at
the **api layer** (the purity gate forbids module-level `random` inward; `random.Random` is
api-side). Slug is the secondary UNIQUE key, 1:1 with `id`; `/d/{slug}` resolves slug → digest.

---

## 5. Cross-cutting rules (every unit obeys)

### 5.1 The boundary (non-negotiable, gate-enforced)

`api → adapters → core`; `core` imports nothing outward (no framework/IO/clock/uuid/`os.environ`).
Enforced by import-linter + `backend/tests/architecture/`. The Anthropic key and the LAN token are
injected via `Settings` (api layer), never read in `core`/`adapters`. Frontend mirror:
`routes → {domains, ui, api}`, `domains → {ui, api, utils}`, `ui → {utils}`, no cycles
(eslint-plugin-boundaries + dependency-cruiser).

### 5.2 The gates (a red gate = fix the code, never loosen the contract)

**GATES-BE** (run from repo root):
```bash
uv sync \
 && uv run ruff format --check . \
 && uv run ruff check . \
 && uv run ty check \
 && uv run lint-imports \
 && uv run pytest          # add --cov for the core-100%-branch coverage gate
```
**GATES-FE** (run from `frontend/`):
```bash
npm install \
 && npm run check:api-drift \   # schema.d.ts == regen from committed openapi.json
 && npm run lint \              # prettier + eslint + boundaries
 && npm run boundaries \        # dependency-cruiser, no cycles
 && npm run check \             # svelte-check, zero a11y (CI-fatal)
 && npm run typecheck \         # tsc --noEmit
 && npm run test \              # vitest (passWithNoTests)
 && npm run build               # adapter-node
```
**E2E-SEAM** (F0): `uv run glyde export-openapi`, then start the server and `curl` (recipe in §7).
**E2E-READER** (frontend units): **export a per-worktree `GLYDE_DB_PATH` first**
(`export GLYDE_DB_PATH="$PWD/.glyde/glyde.db"`), then `uv run glyde serve` (FastAPI :8000) **and**
`cd frontend && npm run dev` (SvelteKit :5173, Vite proxies `/api` → :8000); open the URL and
verify via **§5.9 PATH A** (build + `svelte-check` + `tsc` + a jsdom DOM/route assertion — the binding
gate). Real headless screenshots are an **optional, non-gating** extra via §5.9 PATH B (X1's Playwright);
there is **no screenshot skill** (§5.9). A digest added by `glyde add` is visible because
`serve` and `add` **in this worktree share this worktree's DB**. The per-worktree path is
**mandatory under parallel fan-out**: the default app-data DB
(`platformdirs.user_data_dir("glyde")`, §4.3) is **machine-global**, so without an override two
worktrees seeding concurrently collide (duplicate-slug 409s, cross-unit bleed). The `serve`
process and the `glyde add` that seeds it MUST export the **same** `GLYDE_DB_PATH`. (Backend
`pytest` runs are unaffected — they use tmp DBs.)

### 5.3 Style/quality constraints baked into the gates

- **Backend:** Google docstrings; module + public-API docstrings are the agent contract (state
  designed gaps as **capability facts** — never "spec 001"/roadmap numbers; an architecture test
  fails on spec numbers in source docstrings). `ANN` everywhere; `max-args 6`, `max-branches 10`,
  `max-statements 40`, mccabe `10`; `≤400 lines/file` (split by responsibility, never thin a
  docstring to fit); `raise ... from exc`; `logging`, never `print`; `pathlib`, never `os.path`;
  no `os.environ`/`os.getenv`. **No mocking** in tests (real objects + the in-memory fake kept
  honest by the port contract suite); golden values are pinned literals; every test has a
  one-line docstring; `filterwarnings=error` (close connections with `closing`).
- **Frontend:** Svelte-5 **runes only** (`$state`/`$derived`/`$effect`; no `$:`, `export let`,
  `createEventDispatcher`, `on:`, `<slot>`, `writable`-for-shared-state). A pure function of state
  is a `$derived`, never an `$effect` (`$effect` is for DOM/measure/network only). Never
  destructure `$state`. Typed seam used **inside `load` with the per-request `fetch`**, branch
  `{ data, error }` (a 200 is not success). Semantic **tokens**, never raw palette. **Zero
  `a11y_*` warnings.** shadcn-svelte components are owned source; lucide icon library.
  **Test-file naming is load-bearing** (`frontend/vitest.config.ts`): a test that touches the DOM
  or mounts a component (`@testing-library/svelte`, `localStorage`, `window`) MUST be named
  `*.component.test.ts` — vitest routes those to the **jsdom** `component` project. Plain
  `*.test.ts` runs in the **node** `unit` project with **no DOM**; use it only for pure-logic and
  `load`-function tests. A DOM test misnamed `*.test.ts` fails with `document is not defined`
  (gate-recoverable, but a wasted cycle per unit).

### 5.4 The ownership invariant (how "no two units edit the same file" holds)

The rule that protects parallel worktrees from conflicting is: **no two FAN-OUT units (which run
in parallel) ever edit the same file.** §9 proves this pairwise. F0 is the **serial root** — it
lands first and alone, so it may *scaffold* a file that exactly one later unit owns. This is a
sequential ownership transfer, never concurrent editing. There are exactly three such handoffs,
each engineered so F0's version is the correct default if the owning unit is cut:

| File(s) | F0 leaves | Sole later owner | If owner cut |
|---|---|---|---|
| `FE/routes/+page.{ts,svelte}` | **deleted** (Record consumer removed) | `LIB` **creates** the digest home | root route 404s; build stays green |
| `API/enrich.py` | stub: `get_enricher(...) -> None` (no key → deterministic parse) | `HAIKU` upgrades to key-gated Anthropic | the stub *is* the graceful fallback |
| `API/lan.py`, `API/routes/lan.py` | stub: `serve_lan(settings)` = localhost uvicorn, inert token router (registered in `app.py`) | `LAN` fills the 0.0.0.0 front door / QR / token | degrades to localhost, no guard |

The `serve --lan` **flag** lives on `cli.py`'s `serve` (F0-owned — **not** a handoff) and only
*delegates* to `glyde.api.lan.serve_lan(settings)`; F0's stub makes that localhost, LAN fills the real
front door — so `cli.py` is never edited by LAN, and no fan-out unit adds the flag. Every other file
belongs to exactly one unit. `hooks.server.ts` (LAN), the reader subdirs (R-*),
`lib/domains/preferences/*` (PREF), `app.css`/`app.html`/`+layout.svelte` (X1) are each touched by F0
**not at all**.

**The frozen OpenAPI seam constrains the two backend handoffs (binding).** `docs/schemas/openapi.json`
is F0-owned and frozen (§9), and `TESTS/api/test_openapi.py::test_committed_openapi_matches_the_app`
(also F0-owned) asserts it equals live `create_app().openapi()` byte-for-byte — a fan-out unit can edit
**neither** the artifact nor that test to repair drift. Therefore **neither LAN nor HAIKU may add,
remove, or alter a FastAPI path operation.** `API/routes/lan.py` is a **route-less router** (an
`APIRouter` with **zero** path operations; F0 registers it empty in `app.py`, which is OpenAPI-neutral),
and the LAN token guard lives **entirely** in FE `hooks.server.ts` (the proxy layer), never as a server
route. `API/enrich.py` only swaps the enricher provider behind the **unchanged** `POST /digests`. Both
keep the live OpenAPI identical to F0's frozen artifact, so the seam gate stays green for them. A
LAN/HAIKU feature that genuinely needs a new server route is **out of scope** — that is an OpenAPI
change, i.e. an F0-scope re-freeze (a future ticket), not an inline fan-out edit.

### 5.5 Branch / integration model

- F0 builds on `feat/v1-foundation`, merges to `main` first. **Nothing forks until F0 is merged
  and the seam is frozen.**
- **Branch-base rule (one rule — supersedes any "branch from F0" reading):** each fan-out unit
  branches `feat/v1-<id>` from the **integration tip (`main`) only after EVERY unit in its
  `depends_on` has merged** — not from F0 blindly. The `depends_on` graph (§8), **not** the wave
  label, is authoritative. Concretely: a unit whose `depends_on` is `F0` only (X1, R-CORE, LAN,
  HAIKU, DOCS) branches from merged-F0; a unit that also depends on X1 and/or R-CORE (LIB, PREF,
  R-MODES, R-BLOCKS, R-CHROME) branches **after X1 and R-CORE have merged**, so
  `lib/components/ui/*` + the reading tokens (X1, §5.8) and `lib/domains/reader/types.ts` (R-CORE,
  §5.7) are present and its worktree **typechecks on the first `npm run check`**; R-STAGE branches
  only after **all six** of its `depends_on` (R-CORE, R-MODES, R-BLOCKS, R-CHROME, PREF, X1) have
  merged. One feature = one branch = one PR.
- **Wave gate (the orchestrator enforces the rule):** do not start a unit until `git branch
  --merged main` shows **every** id in its `depends_on`. §9 disjointness still guarantees the
  resulting PRs do not conflict on files; this rule additionally guarantees each worktree
  **compiles** against the contracts it imports (the old "branch from merged-F0" rule did not, and
  would have failed typecheck the moment a Wave-2 unit imported R-CORE's types or X1's primitives).
- This plan is the spec+plan for the build; record it as `specs/002-glyde-v1/` (units are the
  task list). Commit working checkpoints before stopping.

### 5.6 The reader pacing science (R-CORE owns these constants)

Ported from `prototype/reader.html` + `perspective-accessibility.md`. `dwell_ms = base ×
Π(multipliers)`, `base = 60000 / wpm` (default `wpm = 300` → `base ≈ 200 ms`). **The cadence math
(WPM→ms/word, the ORP/pivot bucket, the pause-at-punctuation weights below) lives in a PURE
`FE/lib/domains/reader/cadence.ts`** (R-CORE-owned, no DOM, node-testable) that `engine.svelte.ts`
imports — the assay pure-core / thin-rAF-shell split (build the RSVP clock yourself; assay has none):
keep cadence in `.ts`, only the `requestAnimationFrame` wiring in the `.svelte.ts` shell. See
docs/research/assay-adoption.md §1.

- **Per-token multipliers:** long word (`len > 8`): `1 + 0.03·(len−8)`, cap ≈ 1.4; agent
  `emphasis != none`: ×1.25; first token after a pause/block: ×1.15. (`number`/`low_freq` classes
  are deferred — no lexicon in v1.)
- **Pause-after weights** (the reader maps `Pause.reason` + `duration_scale` → ms): clause ×1.5,
  sentence ×2.2, paragraph ×2.8; `block_ahead` = full stop + the "block ahead" cue.
- **Pivot (ORP):** Spritz bucket `len≤1→0, ≤5→1, ≤9→2, ≤13→3, else 4`, then **measure-and-
  translate** so the pivot glyph sits on a fixed reticle (font-agnostic; ADR-0004).
- **Ramp:** ease from ~45% of target wpm to target over the first ~30 words (when `prefs.ramp`).
- Colour **only** the pivot red. Off-white on near-black, never pure #fff/#000. Flow modes never
  teleprompter-scroll — the highlight moves; the view jumps discretely when the word leaves a band.

### 5.7 The reader prop contract (R-CORE freezes `types.ts` + `engine.svelte.ts`; Wave-2/3 import, never amend)

The single cross-cutting decision the reader fan-out turns on. R-CORE (Wave 1) freezes both files;
R-MODES / R-BLOCKS / R-CHROME (Wave 2) and R-STAGE (Wave 3) import these types and call the engine,
and **may not edit either file**. **No presentational unit recomputes pivot index or `dwell_ms`** —
the engine is the sole owner (closes SCOPING risk #9, the IR/reader pacing fork). Every member below
is frozen here, so a Wave-2 unit never has to recompute pacing locally and R-STAGE never stalls on a
missing field. The factory is the assay `.svelte.ts` state-machine shape (docs/research/assay-adoption.md
§1): `$state` getters + imperative methods, an injected clock, and **ZERO `$effect` in the factory** —
so it is **headless-constructible** and steppable in a node test (defect-fix: the engine must construct
and step without DOM/rAF).

```typescript
// FE/lib/domains/reader/types.ts — R-CORE owns; every reader unit imports from here.
import type { components } from '$lib/api/schema';   // the typed seam (F0 emits NAMED members, §4.5)

export type TokenView        = components['schemas']['TokenView'];
export type ProseSegmentView = components['schemas']['ProseSegmentView'];
export type PauseView        = components['schemas']['PauseView'];
export type BlockView        = components['schemas']['BlockView'];
export type PreferencesView  = components['schemas']['PreferencesView'];
export type SegmentView      = ProseSegmentView | PauseView | BlockView;  // discriminated on `type`
export type Mode             = PreferencesView['mode'];                   // "rsvp" | "guided" | "fading"

// The engine's reactive snapshot. Every field is computed ONCE by the engine; no presentational
// unit recomputes pacing. Backed by $state/$derived inside engine.svelte.ts.
export interface ReaderState {
  token: TokenView | null;       // word on the reticle now; null before first play and while a block shows
  pivotIndex: number;            // ORP glyph index into token.text (Spritz bucket, §5.6); 0 when token is null
  dwellMs: number;               // engine-computed hold for `token` at current prefs; 0 when paused/null
  contextBefore: TokenView[];    // already-read words for RSVP context, oldest→newest, length ≤ prefs.ctx window
  contextAfter: TokenView[];     // upcoming words for RSVP context, nearest→furthest, length ≤ prefs.ctx window
  wordIndex: number;             // 0-based ordinal of `token` across all prose words; 0 at start
  wordCount: number;             // total prose word tokens in the digest (static)
  isPlaying: boolean;            // transport state
  activeBlock: BlockView | null; // non-null exactly while the stream is paused on a block card
  blockAhead: boolean;           // true during the block-ahead cue window (the lead words before a block)
  atEnd: boolean;                // stream exhausted (last word shown, no block pending)
  remainingMs: number;           // est. time-left at current pace (drives Progress "~2m 14s left")
  blockNotches: number[];        // wordIndex of each upcoming block (Progress notches)
}

// The engine: the sole owner of position + pivot + dwell + the block state machine, and
// **headless-constructible** — the factory holds **ZERO `$effect`** (assay's `createLabelLoop` shape;
// docs/research/assay-adoption.md §1). Pure pacing (pivot index, dwell, remaining) is `$derived`; the
// next-token cadence is driven **imperatively through the INJECTED clock** — started in `play()`,
// cancelled in `pause()`/`destroy()` — never a module-level `requestAnimationFrame` / `performance.now`
// and never a reactive `$effect`. The pivot glyph's DOM measure-and-translate onto the reticle (§5.6)
// is **NOT** the engine's job: it lives in R-MODES's `Rsvp.svelte` `$effect` at the DOM boundary,
// reading `engine.pivotIndex` + `engine.token`. The returned object exposes ReaderState via getters —
// read e.g. `engine.token`; NEVER destructure (Svelte-5 rule) — plus the command surface.
export interface ReaderEngine extends Readonly<ReaderState> {
  readonly words: TokenView[];        // the full ordered prose word stream (Flow renders this)
  readonly mode: Mode;                // current mode (drives R-STAGE's Rsvp-vs-Flow choice)
  play(): void;
  pause(): void;
  toggle(): void;                     // unified: if activeBlock → resume; else flip play/pause (Space / tap-stage)
  stepForward(): void;                // advance one word/segment (Transport step button)
  replayWord(): void;                 // step back one word (Transport replay button)
  reshowLastBlock(): void;            // re-display the most-recent block card (ArrowLeft); no-op if none
  scrubTo(wordIndex: number): void;   // Progress tap-to-scrub
  setMode(mode: Mode): void;          // switch mode (R-STAGE persists it via PREF)
  setPrefs(prefs: PreferencesView): void; // re-derive pacing when settings change
  destroy(): void;                    // clear timers (called from the owning $effect cleanup)
}

// The injected clock makes the engine DOM-free and steppable in a HEADLESS (node) test — R-CORE's
// `engine.test.ts` (§8) constructs the engine with a fake clock and advances it deterministically (no
// rAF, no `performance.now`, no jsdom). DI mirrors assay's transport/clock injection
// (docs/research/assay-adoption.md §1); cadence math lives in the pure `cadence.ts` (§5.6), this shell
// holds only the rAF wiring.
export interface ReaderClock {
  now(): number;                                     // ms timestamp; default () => performance.now()
  schedule(tick: (now: number) => void): () => void; // request next frame; returns its canceller.
                                                     // default: requestAnimationFrame / cancelAnimationFrame
}

export function createReaderEngine(args: {
  segments: SegmentView[];
  prefs: PreferencesView;
  clock?: ReaderClock;       // INJECTED time source + frame scheduler; defaults to the real rAF clock.
  reducedMotion?: boolean;   // read ONCE at construction (default matchMedia('(prefers-reduced-motion: reduce)'));
                             // gates the word-flash cadence — a flashing reader is a seizure concern (§5.6).
}): ReaderEngine;

// --- Presentational prop contracts (no pacing maths in any of these) ---

// Mode views (R-MODES: Rsvp.svelte, Flow.svelte). R-STAGE passes the engine as `state`.
export interface ModeProps {
  mode: Mode;                    // "rsvp" → Rsvp.svelte; "guided" | "fading" → Flow.svelte (variant by mode)
  state: ReaderState;            // reads token, pivotIndex, contextBefore/After, wordIndex
  words: TokenView[];            // full prose stream (Flow renders all words, highlighting state.wordIndex)
}

// Block cards (R-BLOCKS: one component per `block.kind`). R-STAGE mounts the right card.
export interface BlockCardProps {
  block: BlockView;              // kind discriminates code | table | image | math | quote | note
  reshown: boolean;              // true when surfaced by the ArrowLeft re-show (subtle "again" affordance)
}
export interface BlockAheadCueProps {   // the "code ahead" chip (R-BLOCKS)
  kind: BlockView['kind'];       // chip label ("code ahead", "table ahead", …)
  visible: boolean;              // = ReaderState.blockAhead
}

// Transport (R-CHROME: Transport.svelte). Stateless chrome; every action calls the engine.
export interface TransportProps {
  isPlaying: boolean;            // = ReaderState.isPlaying
  wpm: number;                   // current speed (from Preferences)
  onToggle: () => void;          // → engine.toggle()
  onReplayWord: () => void;      // → engine.replayWord()
  onStepForward: () => void;     // → engine.stepForward()
  onSpeed: (wpm: number) => void;// edge speed rail → PREF write-through
}

// Progress (R-CHROME: Progress.svelte).
export interface ProgressProps {
  wordIndex: number;             // = ReaderState.wordIndex
  wordCount: number;             // = ReaderState.wordCount
  remainingMs: number;           // = ReaderState.remainingMs (rendered "~2m 14s left", tabular-nums)
  blockNotches: number[];        // = ReaderState.blockNotches (upcoming-block ticks)
  onScrub: (wordIndex: number) => void;  // → engine.scrubTo()
}
```

**The global keyboard + tap listener is R-STAGE's alone** (exactly one owner — two worktrees binding
`window` would double-fire). `Reader.svelte` binds a single `window` `keydown` and a single stage
`pointerdown` in one `$effect`: `Space`/tap-stage → `engine.toggle()` (which itself resumes when
`activeBlock` is set, else flips play/pause), `ArrowLeft` → `engine.reshowLastBlock()`, `ArrowRight`
→ `engine.stepForward()`. **R-MODES, R-BLOCKS and R-CHROME register NO global listeners** — Transport's
on-screen buttons call the engine through `TransportProps` callbacks; block cards are pure
presentational. This single-sources Space-resume / Left-re-show / tap-play-pause.

**The tap-stage element must be a11y-correct or the zero-a11y gate (§5.3) is CI-fatal.** A
`pointerdown`/`click` on a static element (a bare `<div>`) raises svelte-check's
`a11y_no_static_element_interactions` (and `a11y_click_events_have_key_events`), failing
`npm run check`. R-STAGE therefore mounts the stage as an interactive element: `role="button"` (or
`role="application"` for the reading surface) **+** `tabindex="0"` **+** an `aria-label`
(e.g. "Reading stage — tap to play or pause") **+** the paired `keydown` handler it already binds
(the `Space` toggle satisfies the keyboard-handler requirement). No `<div onpointerdown>` without
that quartet. (Chrome buttons in R-CHROME are real `<button>`s and need none of this.)

### 5.8 The X1 shell contract (X1 freezes `ui/*` + the semantic tokens + the FE deps; Wave-2/3 import, never amend)

The frontend twin of §5.7. **X1 (Wave 1) freezes three things every later FE unit consumes: the
`lib/components/ui/*` primitives, the semantic Tailwind token vocabulary, and the FE npm dependency
surface.** LIB, PREF, R-MODES, R-BLOCKS, R-CHROME and R-STAGE import these and **may not edit
`app.css`, `app.html`, `+layout.svelte`, `lib/components/ui/*`, or `package.json`** (§9). This seam
needs freezing as hard as the reader prop contract: two agents would otherwise guess different
`Slider` props (R-STAGE/R-CHROME break at integration) or different token names — and **a wrong
Tailwind token name fails NO gate** (svelte-check and eslint do not flag unknown utility classes), so
`text-pivot` mistyped as `text-pivot-color` is **silent** visual breakage. Every name below is frozen
here; a unit that finds a primitive or token missing flags X1 (Wave 1), it never adds its own.

#### Owned `ui/*` primitives (import path · frozen props)

shadcn-svelte conventions (owned source, §5.3): runes, `type Props = HTMLxAttributes & {…}`, semantic
tokens only, `cn()` from `$lib/utils`, Snippet children via `{@render children()}`. Slider and Sheet
may be hand-rolled or built on a headless lib X1 bundles — **the props are frozen regardless of
internals.**

```typescript
import type { Snippet, Component } from 'svelte';
import type { HTMLButtonAttributes } from 'svelte/elements';

// $lib/components/ui/Button.svelte — already in the scaffold; X1 keeps/owns it.
interface ButtonProps extends HTMLButtonAttributes {
  variant?: 'primary' | 'secondary' | 'destructive' | 'ghost';   // default 'primary'
  children: Snippet;
}

// $lib/components/ui/Icon.svelte — lucide wrapper. Consumers import the glyph from '@lucide/svelte'
// (X1-owned dep, below) and pass it: <Icon icon={Play} aria-label="Play" />.
interface IconProps {
  icon: Component;           // a '@lucide/svelte' icon component (Play, Pause, RotateCcw, SkipForward, …)
  size?: number;             // px; default 20
  class?: string;            // colour via a text-* token, e.g. class="text-muted-foreground"
  'aria-label'?: string;     // set for a standalone/interactive icon; omit ⇒ decorative (aria-hidden)
}

// $lib/components/ui/Slider.svelte — single-thumb range (speed / size / spacing / ctx_scale).
interface SliderProps {
  value: number;             // $bindable — current value (bind:value from the parent)
  min: number;
  max: number;
  step?: number;             // default 1
  onValueChange?: (value: number) => void;  // fired on commit (R-CHROME speed rail; PREF controls)
  'aria-label': string;      // REQUIRED (zero-a11y gate)
  class?: string;
}

// $lib/components/ui/Sheet.svelte — mobile-first overlay (Settings quick-panel, mode switcher).
interface SheetProps {
  open: boolean;             // $bindable — parent owns visibility (bind:open)
  side?: 'bottom' | 'right'; // default 'bottom'
  title: string;             // accessible label (rendered + aria-label on the dialog)
  onClose?: () => void;      // backdrop / Escape dismiss
  children: Snippet;
}
```

#### Semantic token vocabulary (the ONLY colour/face utilities a unit may type)

Defined in all **three** theme scopes (`:root`/`.light`, `.dark`, `.sepia`) in `app.css` and exposed
to Tailwind via `@theme inline` as `--color-*` / `--font-*`. X1 ports the prototype palette into these
names and adds an explicit `.light` and `.sepia` scope **beside** the scaffold's existing `.dark`, so
any subtree (and the `/dev` harness) can scope a theme.

| Token (CSS var) | Tailwind utility | Meaning / who uses it |
|---|---|---|
| (inherited shadcn set) | `bg-background` `text-foreground` `bg-card` `text-card-foreground` `bg-popover` `text-muted-foreground` `bg-primary` `text-primary-foreground` `bg-secondary` `bg-accent` `text-accent-foreground` `bg-destructive` `border-border` `bg-input` `ring-ring` | general chrome — LIB, PREF, R-CHROME, block cards. All flip per theme. |
| `--color-pivot` | `text-pivot` `bg-pivot` | the coral ORP letter — **the one reserved reading colour** (R-MODES RSVP pivot; §5.6 "colour only the pivot red"). |
| `--color-reading` | `bg-reading` | the calm reading-stage surface, distinct from `card` — R-STAGE / R-MODES. |
| `--color-reading-foreground` | `text-reading-foreground` | off-white reading text, never pure `#fff` (§5.6) — R-MODES. |
| `--color-reading-dim` | `text-reading-dim` | dimmed RSVP context words + the Fading trail — R-MODES. |
| `--color-cue` | `text-cue` `bg-cue` | the "block ahead" accent chip — R-BLOCKS `BlockAheadCue`. |
| `--font-reading` | `font-reading` | Atkinson Hyperlegible — the streamed word (R-MODES, R-STAGE). |
| `--font-ui` | `font-ui` | Lexend — chrome/labels (R-CHROME, LIB, PREF). |
| `--font-mono` | `font-mono` | the memorable slug (LIB) + code cards (R-BLOCKS). |

Units use **only** these utilities for colour/face; a raw hex or palette class (`bg-[#11151c]`,
`bg-neutral-900`) is a §5.3 violation. New token needs (none foreseen for v1) go through X1 — it is the
sole owner of `app.css`.

#### FE dependency surface (X1 owns `package.json`)

Mirroring F0's backend dep ownership: **X1 owns `frontend/package.json` + `frontend/package-lock.json`**
and is the sole FE unit that adds npm deps. It adds **`@lucide/svelte`** (the Svelte-5 lucide package) in
Wave 1, before any Wave-2 unit branches, so no later unit edits `package.json`. F0 treats the FE deps as
**read-only** (it runs `npm install`/`build` but adds nothing). Consumers import icon glyphs directly
from `@lucide/svelte` and pass them to `<Icon>`; no other unit adds a runtime FE dep — the v1 code card
is static monospace and the math card is `linear_form`-or-raw, so no highlighter/KaTeX dep is needed
(§2 relief valve). X1 is the only unit with standing to add the **optional, non-gating** Playwright
capability (PATH B, §5.9), since it owns `package.json`. **By default PATH B stays on-demand
(uncommitted)** — an agent that wants a screenshot runs `npm --prefix frontend i -D @playwright/test`
ad hoc — so `@playwright/test` never enters the committed `package.json` and therefore never enters an
offline `npm install` / GATES-FE step. Committing it (dep + `frontend/playwright.config.ts` +
`frontend/e2e/*` + an `e2e` script, all X1-owned, all outside `src/` so vitest/depcruise ignore them) is
**optional** and only sensible if the overnight harness warms `@playwright/test` + the chromium binary
online first (§6). Either way `e2e` is not in GATES-FE, so it changes no gate.

### 5.9 Visual verification — no screenshot skill (PATH A binding · PATH B optional)

There is **no screenshot skill** in this environment (`screenshot_available = false`), and
`@playwright/test` is **not** installed (absent from `frontend/package.json` / `node_modules`; no
`playwright.config.*`; no `e2e` script). Literal headless screenshots are therefore **unavailable by
default**. Every FE unit's **binding** done-condition is **PATH A** (build + type/markup gate + a jsdom
DOM/route assertion — no pixels); real headless screenshots are an **optional, non-gating** extra via
**PATH B** (X1's Playwright, §8 X1). A unit must **never gate** on a literal screenshot.

**PATH A — available now (the binding gate): build + svelte-check + tsc + a jsdom DOM assertion.**
Preconditions already met: `node_modules` present; `frontend/src/lib/api/schema.d.ts` already exists
(6.6 KB) so check/build run without regenerating. (If it were ever absent: export the seam —
`uv run glyde export-openapi`, entrypoint `glyde.api.cli:app` → `openapi_doc.py`, writes
`docs/schemas/openapi.json` — then `npm --prefix frontend run gen:api`, before check/build.)
```bash
npm --prefix /Users/findlaywebb/glyde/frontend run check      # svelte-kit sync + svelte-check 4.6.0: markup/a11y/CSS (a11y CI-fatal)
npm --prefix /Users/findlaywebb/glyde/frontend run typecheck  # tsc --noEmit (svelte-check does NOT cover this)
npm --prefix /Users/findlaywebb/glyde/frontend run build      # vite build via adapter-node — proves the route SSR-compiles
# Closest thing to visual verification without pixels: a vitest "component" test
# (src/**/*.component.test.ts, jsdom env, @testing-library/svelte already installed) that mounts the
# page/component and asserts on rendered DOM (getByRole / getByText):
npm --prefix /Users/findlaywebb/glyde/frontend test           # NB: jsdom renders no pixels — asserts DOM/a11y, not appearance
```

**PATH B — optional, non-gating: install Playwright ON-DEMAND → real headless screenshots.** Installed
ad hoc (not a committed dep — see §5.8), so any X1-dependent visual unit (LIB, PREF, R-MODES, R-BLOCKS,
R-STAGE) *may* capture a screenshot for human eyeballing — **never as a gate**:
```bash
npm --prefix /Users/findlaywebb/glyde/frontend i -D @playwright/test
npx --prefix /Users/findlaywebb/glyde/frontend playwright install chromium   # downloads the browser (online; warm before going dark, §6)
```
`frontend/e2e/shot.spec.ts` (guaranteed-correct API):
```ts
import { test } from '@playwright/test';
test('shoot route', async ({ page }) => {
  await page.goto('/');                                    // any route
  await page.screenshot({ path: 'shot.png', fullPage: true });
});
```
Add an `"e2e": "playwright test"` script + a minimal `playwright.config.ts` whose `webServer` boots the
app, e.g. `webServer: { command: 'npm run build && node build/index.js', url: 'http://localhost:3000',
reuseExistingServer: true }` (adapter-node serves `:3000`; or `npm run preview` → `:4173`; or
`npm run dev` → `:5173`), with `baseURL` set to match. One-off CLI capture once installed (confirm the
subcommand exists first: `npx playwright screenshot --help`):
```bash
npm --prefix /Users/findlaywebb/glyde/frontend run dev &     # Vite dev → http://localhost:5173
npx --prefix /Users/findlaywebb/glyde/frontend playwright screenshot --viewport-size=1280,800 http://localhost:5173/ shot.png
```
**CAVEAT for data routes:** the app proxies `/api` → FastAPI (`GLYDE_API_ORIGIN`, default
`http://127.0.0.1:8000`) and `+page.ts` `load`s fetch through it, so bring the backend up
(`uvicorn` / `uv run glyde serve`) **before** screenshotting any route that reads via the typed seam; the
bare index route can be shot without the backend if it renders without remote data. `e2e` is **not** in
GATES-FE, so adding it changes no gate; the browser binary is an online step (pre-flight §6).

### 5.10 The PREF store contract (PREF freezes `prefs.svelte.ts`; R-STAGE + Settings import, never amend)

R-STAGE reads `Preferences` from PREF's store and persists the last-used `mode` through it, so the store
surface is a cross-cutting contract — pinned here like §5.7/§5.8. PREF owns it; R-STAGE and the Settings
page import it and **may not amend it**. It reproduces the assay typed-seam discipline (committed
`schema.d.ts`, reads in `load`, `{data,error}`; docs/research/assay-adoption.md §2).

**Row shape — exactly `PreferencesView`** (the §4.1 `Preferences` projection: a default for **every**
field, so a partial body validates under `extra="forbid"`, §4.5). The persisted localStorage value and
the `PUT /preferences` body are the **same full object**:
```ts
// FE/lib/domains/preferences/prefs.svelte.ts — PREF owns; R-STAGE + Settings import.
import type { components } from '$lib/api/schema';
export type PreferencesView = components['schemas']['PreferencesView'];
//  = { owner_id, mode, wpm, context, ctx_scale, chunk, size_px, letter_spacing_em, font, theme, ramp }
//    every field defaulted, mirroring core Preferences (§4.1); owner_id is "local" in v1.

export const PREFS_STORAGE_KEY = 'glyde:prefs';            // the localStorage mirror key (§8 PREF e2e)
export const DEFAULT_PREFERENCES: PreferencesView;         // === core Preferences() defaults (mode "guided")

export interface PrefsStore {
  readonly current: PreferencesView;          // reactive $state getter — read `store.current`; NEVER destructure
  set(patch: Partial<PreferencesView>): Promise<void>;  // merge patch → current; mirror the FULL object to
                                              // localStorage SYNCHRONOUSLY (instant), then PUT the FULL object
  reload(): Promise<void>;                     // GET /preferences, reconcile with the localStorage mirror → current
}

export function createPrefsStore(args: {
  fetch?: typeof fetch;            // INJECTED (defaults to platform fetch) so the persist round-trip is
                                   // unit-testable with no server (§8 PREF component test)
  initial?: PreferencesView;       // SSR/load-provided prefs; else the localStorage mirror; else DEFAULT_PREFERENCES
}): PrefsStore;
```

**GET/PUT semantics (server is source of truth; §4.5):**
- First paint reads the localStorage mirror synchronously (instant, offline-safe); `reload()` then
  `GET /preferences?owner_id=local`, reconciles, and updates `current`.
- `set(patch)` is **write-through**: merge `patch` into `current`, write the **complete** object to
  `localStorage[PREFS_STORAGE_KEY]` synchronously, then **`PUT /preferences` with the complete object**.
  `PUT` is **full-replace** (upsert by `owner_id`; missing fields fall to defaults), so the client always
  sends the whole `PreferencesView` — never a partial — and no field (the last-used `mode` included) is
  silently reset on the round-trip.
- Branch `{ data, error }` on every read/write (a 200 is not success); on a failed `PUT` keep the
  optimistic local value and surface the error (do not roll back the user's setting).

### 5.11 Mobile-LAN + PWA split (X1 shell hooks · LAN payload) — assay-adoption.md §3

The mobile-LAN / PWA learnings (docs/research/assay-adoption.md §3) split across two **file-disjoint**
owners; pinned here so the split stays clean and degrades safely.

- **X1 owns the shell hooks (always ship, cost nothing):** in `app.html` the viewport
  `interactive-widget=resizes-content` + dark-first no-flash `<html class="dark">` + `color-scheme`; in
  `+layout.svelte` the guarded SW registration (`browser && !dev && 'serviceWorker' in navigator`,
  `.catch()`), the `<link rel="manifest">` + `theme-color` + `apple-touch-icon`, and the mounted
  `lib/components/ui/InstallHint.svelte` (iOS "Add to Home Screen", dismissible, ≥44px close); in
  `app.css` `overscroll-behavior-y: contain`, `overflow-x-clip` on `<main>`, text inputs **≥16px** (stop
  iOS focus-zoom — central for a reading app), touch targets **≥44px** (`min-h-11 min-w-11`). These are
  pure HTML/CSS/registration and reference LAN's payload only by **runtime URL** (`/sw.js`,
  `/manifest.json`), never by import — so they ship and stay green even if LAN is cut.
- **LAN owns the installable/offline payload (cuttable):** `static/manifest.json` (standalone, portrait,
  dark `theme_color`, 192/512 + maskable icons), `static/icons/*`, and `static/sw.js` — a classic
  shell-cache worker whose **`/api/*` passthrough is the FIRST statement** (a cache miss must never shadow
  a live read/mutation), caching only `/_app/immutable/**`. **Glyde's deliberate extension:** a **narrow**
  read-through cache for `GET /api/digests/{slug}` (the Digest IR, versioned key, stale-while-revalidate)
  placed **before** the general `/api/*` passthrough — only that one read path is cached for offline
  reading; list / preferences / mutations stay passthrough. The node front door + CSRF + token + HTTPS
  live in LAN's `hooks.server.ts` / `lan.py` (§8 LAN).
- **Cross-reference, not a handoff:** if LAN is cut, X1's guarded registration `.catch()`es the missing
  `/sw.js` and the manifest link 404s harmlessly — mobile ergonomics (viewport, ≥16px, ≥44px, no-flash)
  still ship via X1; only the installable/offline layer is lost. The PWA needs a **secure context**
  (HTTPS-over-LAN, §8 LAN) — over plain-HTTP LAN the SW simply never registers, which is correct.

---

## 6. Build order (waves)

**Pre-flight (network required for F0; warm the cache before any isolated wave).** F0 adds
`platformdirs` + `segno` + `anthropic` and regenerates `uv.lock` (a cold dependency resolve needs the
package index), and the frontend needs `npm install`. **Do not start F0 in a network-isolated
sandbox** — it dies at its first `uv sync`/`npm install`. Once F0 has merged, the fan-out worktrees
can gate **offline** only if the `uv` and `npm` caches are warm; if the overnight box is isolated,
run `uv sync` (against F0's pyprojects, so the three new wheels + the regenerated lock are resolved)
and `cd frontend && npm install` **once with network before going dark**, so every subsequent gate
(`uv sync`, `npm install`, `npm run build`) hits a warm cache. The build assumes this has happened.
**Two optional, non-gating online extras** (skip if isolated — no gate depends on either): if PATH B
screenshots (§5.9) are wanted, warm `@playwright/test` + `npx playwright install chromium` online; if
HTTPS-over-LAN (§8 LAN) is wanted, run `mkcert` for the LAN IP / `glyde.local` and trust its root CA on
the phone once. Neither is in GATES-FE, so an isolated box still gates green on PATH A + localhost serve.

**Per-worktree DB under parallel fan-out.** The overnight harness must export a distinct
`GLYDE_DB_PATH` per worktree (e.g. `$WORKTREE/.glyde/glyde.db`) for **every** `glyde add` / `serve` /
E2E-READER invocation in that worktree (§5.2): the default app-data DB is machine-global, so parallel
worktrees seeding the same SQLite file collide (duplicate-slug 409s, cross-unit bleed). The seed `add`
and the `serve` it feeds must share the **same** path; `pytest` runs use tmp DBs and are unaffected.

```
Wave 0 (serial):   F0  ────────────────────────────────────────────────┐  (merge, freeze seam)
                                                                        │
Wave 1 (parallel): X1   R-CORE   HAIKU*   LAN*   DOCS                    │  (depend on F0 only)
                                                                        │
Wave 2 (parallel): LIB   PREF   R-MODES   R-BLOCKS   R-CHROME            │  (depend on F0 + X1[/R-CORE])
                                                                        │
Wave 3 (serial-ish): R-STAGE  ─ integrates R-CORE+R-MODES+R-BLOCKS+R-CHROME+PREF+X1
```
`*` = relief valve (cut HAIKU first, then LAN). R-STAGE is the only integrator and lands last.

---

## 7. The FOUNDATION unit

Path-root legend: `CORE = backend/packages/core/src/glyde/core`,
`ADAPT = backend/packages/adapters/src/glyde/adapters`,
`API = backend/packages/api/src/glyde/api`, `TESTS = backend/tests`, `FE = frontend/src`.

### F0 — Digest IR + parser + store + slug + API + typed seam + CLI loop

- **summary:** The keystone. Replace the template `Record` with the Digest IR; ship the pure
  Glyde-Markdown parser (the test-first centrepiece), the slug generator, the `DigestStore` port +
  SQLite adapter (migration 0002 dropping `records`), the api schema projections, `compose_digest`,
  the real routes (`POST/GET/list /digests`, `GET/PUT /preferences`), the `serve`/`add`/`list`/`read`/
  `export-openapi` CLI (`serve` gains the delegating `--lan` flag; `read` is the §3 fallback reader),
  and the regenerated typed seam. Scaffold the three handoff points (§5.4).
  Close the loop end to end: `glyde add` → store → `GET /digests/{slug}` returns the parsed IR.
  Leave **every gate green** (backend + frontend + seam).
- **depends_on:** — (serial, first).
- **owned_paths:**
  - Core: `CORE/models/{__init__,token,segment,provenance,digest,preferences}.py`,
    `CORE/derive.py`, `CORE/parsing/{__init__,blocks,prose}.py`,
    `CORE/ports/{__init__,errors,digest_store}.py`, `CORE/__init__.py`.
    **Delete:** `CORE/models.py`, `CORE/ports/record_store.py`.
  - Adapters: `ADAPT/sqlite/{digest_store.py,schema.sql,__init__.py}`,
    `ADAPT/sqlite/migrations/0002_digests.sql`. (Leave `0001_init.sql` untouched.)
    **Delete:** `ADAPT/sqlite/store.py`.
  - Api: `API/{compose.py,slug.py,settings.py,deps.py,app.py,cli.py}`, `API/wordbank/{left,right}.txt`,
    `API/schemas/{__init__,segments,digests,preferences,results}.py`,
    `API/routes/{__init__,digests,preferences,meta}.py`,
    **scaffold-only:** `API/enrich.py`, `API/routes/lan.py`, `API/lan.py`.
    **Delete:** `API/schemas/records.py`, `API/routes/records.py`.
  - Deps/lock (F0 owns the **entire** v1 dependency surface so no fan-out unit touches a pyproject
    or `uv.lock`): add `platformdirs` + `segno` (LAN QR) to `backend/packages/api/pyproject.toml`,
    add `anthropic` to `backend/packages/adapters/pyproject.toml`; regenerate `uv.lock` once. (If
    LAN/HAIKU are cut, the unused dep is a harmless heavier install — the price of zero lock
    contention.)
  - Seam: `docs/schemas/openapi.json` (re-export), `FE/lib/api/schema.d.ts` (regenerate + commit).
    **Delete:** `FE/routes/+page.ts`, `FE/routes/+page.svelte` (Record consumer; `LIB` recreates).
  - Tests (replace Record suites with Digest suites): `TESTS/support/{factories,memory_store,store_contract}.py`,
    `TESTS/core/test_models.py` → `TESTS/core/{test_models,test_derive}.py`,
    `TESTS/core/parsing/{__init__,test_parser_golden,test_parser_props}.py`,
    `TESTS/core/ports/{__init__,test_inmemory_store}.py`,
    `TESTS/adapters/sqlite/{test_store,test_schema_convergence}.py`,
    `TESTS/api/{conftest,test_digests_flow,test_preferences_flow,test_slug,test_compose,test_openapi}.py`.
    **Delete:** `TESTS/api/test_records_flow.py`.
- **key construction notes (so a fresh agent needs no further questions):**
  - **Internal checkpoint order (F0 is one atomic merge, but build + commit it in this order so a
    fresh context resumes by reading the last commit, never by re-deriving state):**
    1. **Models + NAMED api-schema projections + the typed-seam export.** Land `core/models/*`, the
       `API/schemas/*` named wire views, `export-openapi`, and the regenerated **committed** `schema.d.ts`
       (the assay typed seam, docs/research/assay-adoption.md §2: `openapi-typescript 7.13.0` →
       committed `schema.d.ts`, the **dual drift gates** — `check:api-drift` AND
       `test_committed_openapi_matches_the_app`, neither alone proving freshness — and the
       `openapi-fetch 0.17.0` module client at `/api`); assert the seven named members exist
       (`test_named_seam_members_present`) and the discriminated-union marker
       (`test_segment_union_is_discriminated_oneof`), both below. Commit.
    2. **Store port + errors + SQLite adapter** (migration 0002 dropping `records`) **+ the port
       contract suite** (the in-memory fake and the SQLite store both pass `store_contract`). Commit.
    3. **Pure parser to 100% core branch** — loop parser ↔ golden vectors ↔ `--cov` (the blessed
       iterate-to-green grind, below). Commit.
    4. **`compose_digest` + routes** (`POST/GET/list /digests`, `GET/PUT /preferences`, `meta`) **+
       the `StoreError` handler + `app.py` wiring** incl. the route-less `lan` router. Commit.
    5. **CLI** (`add`/`list`/`read`/`serve`/`export-openapi`) **+ the three §5.4 scaffolds**
       (`enrich.py`, `lan.py`, `routes/lan.py`) **+ delete the Record files.** Re-export the seam.
       Commit. Then run the full §7 verify recipe and merge.
    Each checkpoint is independently green-able; a resuming agent runs `git log --oneline` to see the
    last completed step and continues.
  - The segment union is a Pydantic v2 **discriminated union on `type`** in **both** the core models
    (§4.1) and the api projections. Core models document via class docstrings (no field descriptions
    needed); the **api schema projections** (`API/schemas/segments.py`, `digests.py`, `preferences.py`)
    re-declare the wire shapes as `ApiModel` (`frozen`, `extra="forbid"`, `from_attributes=True`) with a
    **non-empty `description` on every field except the `type` discriminator** (the schema-descriptions
    gate). `API/schemas/segments.py` declares `SegmentView = Annotated[ProseSegmentView | PauseView |
    BlockView, Field(discriminator="type")]` (each variant a `Literal["prose"|"pause"|"block"]` `type`
    tag), and `DigestView.segments: list[SegmentView]`. `DigestView`/`PreferencesView` project via
    `model_validate(domain_model)`. **Name every wire variant** — `TokenView`, `ProseSegmentView`,
    `PauseView`, `BlockView` (and `DigestView`, `DigestListItemView`, `PreferencesView`) — never an
    inline union model, so the seam emits each as a named `components['schemas'][…]` member and
    `DigestView.segments.items` is a **`oneOf` of named `$ref`s with a sibling `discriminator`**
    (§4.5, §5.7). R-CORE's `types.ts` aliases these directly off `schema.d.ts`. **F0 proves the named
    members AND the discriminated-union marker before fan-out** (a reader unit cannot repair this seam —
    it is F0-owned). In `TESTS/api/test_openapi.py`:
    - `test_named_seam_members_present` asserts `create_app().openapi()["components"]["schemas"]`
      contains **`TokenView`, `ProseSegmentView`, `PauseView`, `BlockView`, `DigestView`,
      `DigestListItemView`, `PreferencesView`**.
    - `test_segment_union_is_discriminated_oneof` asserts on the **exported OpenAPI JSON**
      (`docs/schemas/openapi.json` — which `test_committed_openapi_matches_the_app` pins byte-equal to
      the live app; **NOT** the generated `.d.ts`, which cannot distinguish `oneOf` from `anyOf`) that
      the discriminated-union list field's array-item schema uses `oneOf` + `discriminator`, not `anyOf`.
      For model `M = DigestView`, field `f = segments`, at JSON path
      `openapi["components"]["schemas"]["DigestView"]["properties"]["segments"]["items"]`:
      - has key `"oneOf"` == True
      - has key `"anyOf"` == False
      - `["discriminator"]["propertyName"]` == `"type"`
      - `["discriminator"]["mapping"]` is a non-empty object

      The single canonical assertion: the discriminated-union item schema's union key MUST equal
      `"oneOf"` (with a sibling `"discriminator"`). If the discriminator is ever dropped, FastAPI emits
      `"anyOf"` and no discriminator — exactly the regression this test catches. (When a union is a
      top-level response/body rather than nested in a list, the same `oneOf`+`discriminator` lands
      directly under that schema / response-content schema instead of under `.items`; the marker is
      invariant — union key == `"oneOf"` AND a `"discriminator"` sibling present.)

    If F0 emits any variant anonymously, or the union as `anyOf`, the relevant test is red in F0, where
    it can still be fixed — before any reader unit imports the (missing) key or the wrong union shape.
  - Parser rules (`CORE/parsing/`, pure, deterministic — purity gate clean): `#…` →
    `ProseSegment(role=heading)`; blank line → `Pause(paragraph)`; `-/*/+`/`N.` item →
    `role=list_item`; fenced ` ```lang ` → `Block(code, lang)`; pipe table → `Block(table)`;
    `![alt](src)` → `Block(image, alt, content=src)`; `:::pause … :::` → `Block(note)`; `$$…$$` →
    `Block(math)`; `> …` → `Block(quote)`. Emit a `Pause(block_ahead)` **before every block** and
    set the block's `lead` to the preceding prose sentence. Prose tokenises to `Token`s; trailing
    `,;:` → following `Pause(clause)`, `.!?…` → `Pause(sentence)`; `==x==` → `emphasis="strong"`,
    inline `` `code` `` → `emphasis="code"`, `*em*`/`_em_` → `emphasis="em"`.
  - **Segmentation model (so the golden vectors are self-consistent):** prose splits into **runs** at
    clause/sentence punctuation — each run is one `ProseSegment`; a `Pause` between runs takes its
    `reason` from the punctuation that closed the preceding run (`,;:`→clause, `.!?…`→sentence). A
    blank line emits `Pause(paragraph)`; a trailing sentence-pause immediately before it is
    **upgraded** to the paragraph pause (no stacked pause). Headings and list items are their own
    `ProseSegment`; consecutive list items are separated by `Pause(clause)`. `Pause(block_ahead)`
    precedes every block and **supersedes** an immediately-preceding paragraph/sentence pause;
    `block.lead` = the nearest preceding prose run's text, else `None`. **No trailing `Pause` at
    EOF.** Emphasis does **not** nest in v1 — multiple spans per run are fine; an unmatched/inner
    delimiter is literal text.
  - **Golden vectors (pinned literals; `·` separates timeline segments). These are the parse
    contract — add more the moment `--cov` shows an uncovered branch:**
    1. `## Ship it\nWe ==shipped== it.` → `Prose(heading,[Ship,it]) · Prose(body,[We, shipped:strong, it])` (heading branch, strong, EOF→no pause).
    2. `Yes, it works. New idea.\n\nNext.` → `Prose(body,[Yes]) · Pause(clause) · Prose(body,[it,works]) · Pause(sentence) · Prose(body,[New,idea]) · Pause(paragraph) · Prose(body,[Next])` (clause/sentence/paragraph + the sentence→paragraph upgrade + EOF).
    3. `- one\n- two\n- three` → `Prose(list_item,[one]) · Pause(clause) · Prose(list_item,[two]) · Pause(clause) · Prose(list_item,[three])` (unordered marker + inter-item clause).
    4. ``1. run *fast* now\n2. use `grep` `` → `Prose(list_item,[run, fast:em, now]) · Pause(clause) · Prose(list_item,[use, grep:code])` (ordered marker, em + inline-code spans, no nesting).
    5. ```` Run this.\n\n```py\nx = 1\n``` ```` → `Prose(body,[Run,this]) · Pause(block_ahead) · Block(code, lang="py", content="x = 1", lead="Run this")` (fence + lang + lead + block_ahead-supersedes-paragraph).
    6. `| a | b |\n| --- | --- |\n| 1 | 2 |` → `Pause(block_ahead) · Block(table, content="<the 3 raw lines>", lead=None)` (pipe table, lead=None, block_ahead at start).
    7. `See below.\n\n![a cat](cat.png)` → `Prose(body,[See,below]) · Pause(block_ahead) · Block(image, alt="a cat", content="cat.png", lead="See below")`.
    8. `$$E=mc^2$$` → `Pause(block_ahead) · Block(math, content="E=mc^2")`; `> wisdom here` → `Pause(block_ahead) · Block(quote, content="wisdom here")`; `:::pause\nbreathe\n:::` → `Pause(block_ahead) · Block(note, content="breathe")` (the remaining three block kinds).
  - **Iterate to green, do not one-shot.** The pure parser must hit **100% core branch coverage**;
    reach it by adding vectors that exercise each remaining branch, not by perfecting one example.
    F0 is explicitly blessed to loop parser ↔ vectors ↔ `--cov` until green. **Golden-vector tests
    pin the parse** (a wrong parser poisons every surface) + Hypothesis properties (round-trip /
    idempotence).
  - `Settings` (full surface declared now so no unit re-edits it): `data_dir`
    (`platformdirs.user_data_dir("glyde")`), `db_path` (`data_dir/"glyde.db"`, `GLYDE_DB_PATH`
    overrides), `host`, `port`, `lan_host`, `lan_port` (the adapter-node LAN front door, default 3000),
    `lan_token: str | None`, `lan_https: bool = False`, `lan_cert_path: Path | None`,
    `lan_key_path: Path | None` (the mkcert HTTPS-over-LAN path LAN fills, §8 LAN / §5.11),
    `anthropic_api_key: str | None`. (LAN/HAIKU read these; F0 declares the full surface — the LAN HTTPS
    fields included — so neither re-edits `settings.py`.)
  - `app.py`: register `digests`, `preferences`, `meta`, and the **scaffold** `lan` router;
    map `_STATUS_BY_CODE = {"unknown_digest": 404, "duplicate_slug": 409}`.
  - `deps.py` (final, F0-owned): `get_digest_store` (connection-per-request), `get_now`,
    `bootstrap_migrations`. The **enricher provision lives in the handoff file `API/enrich.py`**,
    not here: F0 ships `API/enrich.py` with `Enricher` (a type alias) + `get_enricher(settings) ->
    Enricher | None` returning `None`. The digests route and `cli add` both do
    `from glyde.api.enrich import get_enricher` and pass `get_enricher(settings)` into `ComposeDeps`
    — so when HAIKU later upgrades `API/enrich.py` (key-gated, importing `ADAPT/enrich.py`), no
    F0-owned file changes. With F0's stub, `enrich: true` simply no-ops to the deterministic parse.
    `cli.py` `add` resolves source (existing path → file;
    stdin-not-a-tty → pipe; else literal → cli), calls `compose_digest` in-process via `open_store`,
    prints `name`, `slug`, and `http://{lan_host}:{port}/d/{slug}`; `list` prints the library;
    errors plain-echoed + `typer.Exit(2)` (never rich).
  - `serve` declares **`--lan: bool = False`**: false → `uvicorn` on `settings.host:{port}` (today's
    behaviour); true → delegate to `glyde.api.lan.serve_lan(settings)`. F0 ships `API/lan.py` with the
    **stub** `serve_lan(settings) -> None` = that same localhost uvicorn (no node spawn, no QR); LAN
    later fills the `0.0.0.0` adapter-node front door + QR + token. The `--lan` flag therefore lives on
    `cli.py` (F0-owned) but only *delegates*, so **no F0-owned file — `cli.py` included — changes when
    LAN lands** (LAN edits only `API/lan.py`/`API/routes/lan.py`). `API/routes/lan.py` is a **route-less**
    router — an `APIRouter` with **zero path operations** — that F0 registers in `app.py`. Registering an
    empty router is **OpenAPI-neutral**: the committed `docs/schemas/openapi.json` is unchanged, so
    `test_committed_openapi_matches_the_app` stays green now and after LAN fills the file (LAN adds **no**
    path operation; the token guard is the `hooks.server.ts` proxy, §5.4). F0 commits the seam **with**
    this empty router registered, so the frozen artifact already reflects it.
  - `read <slug>`: the **fallback-tier reader** (§3) — `store.get_by_slug(slug)` then flatten the IR
    to terminal prose (join each prose run's tokens; a `Pause` is a line break, a paragraph a blank
    line; a `Block` prints `[<kind>] {lead or ''}` then its `content` indented) and echo to stdout.
    Command-verifiable, zero frontend — the degraded headline if every R-* unit slips. Keep
    `export-openapi`.
- **verify recipe:**
  ```bash
  # backend + seam
  GATES-BE                                   # (the §5.2 chain, with --cov)
  uv run glyde export-openapi
  cd frontend && npm run check:api-drift && cd ..   # schema.d.ts regenerates clean
  # named-seam guard: every wire view the reader units import (§5.7) must be a NAMED schema member
  for V in TokenView ProseSegmentView PauseView BlockView DigestView DigestListItemView PreferencesView; do
    grep -q "$V:" frontend/src/lib/api/schema.d.ts || { echo "MISSING named schema member: $V"; exit 1; }
  done
  # discriminated-union seam marker — assert on the EXPORTED openapi.json, NOT schema.d.ts
  # (openapi-typescript collapses oneOf and anyOf into the same TS `A | B | C`, so the .d.ts can't prove it)
  jq -e '.components.schemas.DigestView.properties.segments.items | has("oneOf")'        docs/schemas/openapi.json  # true
  jq -e '.components.schemas.DigestView.properties.segments.items | (has("anyOf") | not)' docs/schemas/openapi.json  # anyOf absent
  jq -e '.components.schemas.DigestView.properties.segments.items.discriminator.propertyName == "type"' docs/schemas/openapi.json  # true
  jq -e '.components.schemas.DigestView.properties.segments.items.discriminator.mapping | length > 0'    docs/schemas/openapi.json  # non-empty mapping
  # E2E-SEAM (start the server in another shell: uv run glyde serve)
  curl -s -X POST localhost:8000/digests -H 'content-type: application/json' \
    -d '{"name":"t","text":"## H\n==big== news.\n\n```py\nx=1\n```","source_kind":"cli"}' | jq .meta.slug
  SLUG=$(…)          # capture it
  curl -s localhost:8000/digests/$SLUG | jq '.segments | map(.type)'   # prose,pause,block...
  curl -s localhost:8000/digests | jq '.[0].counts'                    # {words, blocks_by_kind}
  curl -s -X PUT localhost:8000/preferences -H 'content-type: application/json' \
    -d '{"owner_id":"local","mode":"rsvp"}' | jq .mode   # partial body OK (missing→default); PUT is full-replace (§4.5)
  # E2E loop (the headline) — printf, NOT echo: bash `echo` leaves literal \n, so the fence never parses
  printf '## R\ncode ahead:\n\n```py\nx=1\n```\n' | uv run glyde add --name PR   # prints slug + URL
  uv run glyde add ./README.md --name Readme
  uv run glyde list                                                    # lists both
  uv run glyde read "$SLUG"                                            # fallback reader: flattened prose + [block] (§3)
  # frontend stays green (root route deleted is fine)
  cd frontend && GATES-FE
  ```
- **done when:** GATES-BE, GATES-FE, and the seam drift gate are green; the curl loop returns a
  parsed IR with `block` segments; `glyde add`/`list` work in-process; `core` is 100% branch; the
  **seven named seam members are present** (`test_named_seam_members_present` green **and** the verify
  grep passes) and **`DigestView.segments.items` is a `oneOf` of named `$ref`s carrying a
  `discriminator` (`propertyName: "type"`, non-empty `mapping`) — asserted on the exported
  `docs/schemas/openapi.json`, not `anyOf` and not the `.d.ts`** (`test_segment_union_is_discriminated_oneof`
  green, jq checks pass); the registered `lan` router adds **zero** OpenAPI paths (committed
  `openapi.json` == live `create_app().openapi()`); the five internal checkpoints are each committed.

---

## 8. The fan-out units

Each is a fresh worktree off merged-F0. Build ONLY your `owned_paths`. Frontend units run GATES-FE;
backend units run GATES-BE; reader/library/settings units also run E2E-READER and the **§5.9 PATH A**
DOM/route assertions (real screenshots are optional/non-gating, §5.9 PATH B — there is no screenshot
skill). **Every FE-authoring unit** carries the verbatim Svelte-MCP directive in its instructions
(below) and follows docs/research/assay-adoption.md.

### X1 — App shell, theme tokens, fonts, base UI

- **summary:** The frontend visual foundation every other FE unit relies on, **frozen as the §5.8
  X1 contract** (primitives + token vocabulary + FE deps; Wave-2/3 import, never amend). Three themes
  (dark default / light / sepia) as `@theme inline` tokens carrying the prototype palette
  (dark `#11151c`/`#e6edf3`/coral `#ff5c5c`; sepia `#f4ecd8`/`#3a2f23`/`#b3402a`) — X1 adds an
  explicit `.light` and `.sepia` scope **beside** the scaffold's `.dark` so any subtree can scope a
  theme — the **coral pivot** + reading tokens (`pivot`, `reading`, `reading-foreground`,
  `reading-dim`, `cue`; §5.8), Atkinson Hyperlegible (`font-reading`) + Lexend (`font-ui`) faces,
  mobile-first base layout, and the `ui/` primitives (`Icon`/`Slider`/`Sheet` with the §5.8 props,
  plus the scaffold `Button`). Owns `frontend/package.json` + lockfile and adds **`@lucide/svelte`**
  (§5.8). Ships a committed **`/dev` harness route** (`routes/dev/+page.svelte`, X1-owned, unlinked)
  rendering a primitive + token gallery wrapped three times in `.dark`/`.light`/`.sepia` — **X1's only
  owned route**, so it can render and DOM/route-assert (PATH A; optional PATH B screenshot) in isolation
  without colliding with LIB's `/` (Wave 2) or R-STAGE's `/d/[slug]` (Wave 3). Dark-mode-first
  (`<html class="dark">` already set).
  - **Shell PWA + iOS ergonomics (the X1 half of the §5.11 split; docs/research/assay-adoption.md §3):**
    in `app.html` the viewport `interactive-widget=resizes-content` + the dark-first no-flash
    `color-scheme`; in `+layout.svelte` the guarded SW registration (`browser && !dev && 'serviceWorker'
    in navigator`, `.catch()`, runtime URL `/sw.js` — no import of LAN's payload), the `<link
    rel="manifest">` + `theme-color` + `apple-touch-icon`, and the mounted `lib/components/ui/InstallHint.svelte`
    (iOS Add-to-Home-Screen, dismissible, ≥44px close); in `app.css` `overscroll-behavior-y: contain`,
    `overflow-x-clip` on `<main>`, **text inputs ≥16px** (stop iOS focus-zoom — central for a reading
    app), **touch targets ≥44px** (`min-h-11 min-w-11`). These ship even if LAN is cut (LAN's `/sw.js` +
    manifest then 404 harmlessly). (Glyde mints ids server-side, so the `crypto.randomUUID`
    insecure-context fallback is only needed if a unit ever mints a client-side id over plain-HTTP LAN —
    assay-adoption.md §3; carry it then.)
  - **Svelte MCP + assay:** Use the Svelte MCP tools if available (ToolSearch 'svelte'); if absent from
    your context, use context7 for current Svelte 5 / SvelteKit / runes docs and run svelte-check as the
    runes-idiom gate; in all cases follow docs/research/assay-adoption.md.
- **owned_paths:** `FE/app.css`, `FE/app.html`, `FE/routes/+layout.svelte`, `FE/lib/components/ui/*`
  (incl. the new `InstallHint.svelte`), `FE/routes/dev/+page.svelte`, `FE/package.json`,
  `FE/package-lock.json`. (Optional, on-demand PATH B only: `frontend/playwright.config.ts` +
  `frontend/e2e/*` — uncommitted by default, §5.8/§5.9.)
- **depends_on:** F0.
- **e2e recipe:** GATES-FE; E2E-READER (§5.9 **PATH A**) — open the X1-owned **`/dev`** harness, run
  `npm run check`/`typecheck`/`build`, and assert via a jsdom component/route mount that the coral
  `text-pivot`, the Atkinson `font-reading` face, and each of `.dark`/`.light`/`.sepia` resolve (and
  **zero `a11y_*`** warnings). Optional PATH B: screenshot the three theme scopes. Depends on no other
  unit's route.

### LIB — Library home (the root route)

- **summary:** Create the digest library home (F0 deleted the template's records page). Newest-first
  feed: agent **name** as title, the memorable **slug** in a distinct mono treatment (tappable deep
  link to `/d/{slug}`), provenance (source/producer/when), and **shape badges** (word count, est
  read time, block mix "3 code · 1 table"). Loads `GET /digests` through the typed seam in `load`
  (the assay typed-seam discipline, docs/research/assay-adoption.md §2: `openapi-fetch` module client
  at `/api`, the **per-request `fetch`** + absolute `${url.origin}/api` base, branch `{data,error}` — a
  200 is not success — and `ui/` cards take **primitive props, never the wire/Digest type**). Minimal
  only — search/read-state/grouped feed are Phase 2.
  - **Svelte MCP + assay:** Use the Svelte MCP tools if available (ToolSearch 'svelte'); if absent from
    your context, use context7 for current Svelte 5 / SvelteKit / runes docs and run svelte-check as the
    runes-idiom gate; in all cases follow docs/research/assay-adoption.md.
- **owned_paths:** `FE/routes/+page.ts`, `FE/routes/+page.svelte`, `FE/lib/domains/library/*`.
- **depends_on:** F0, X1.
- **e2e recipe:** GATES-FE; E2E-READER (§5.9 PATH A) — assert via a route/jsdom mount that `/` lists
  seeded digests newest-first with name + mono slug + counts, and that a card links to `/d/{slug}`
  (optional PATH B screenshot).

### PREF — Preferences client + Settings page

- **summary:** The `Preferences` reactive store — **implement exactly the §5.10 PREF store contract**
  (`prefs.svelte.ts`: `PREFS_STORAGE_KEY`, `DEFAULT_PREFERENCES`, `PrefsStore{current,set,reload}`,
  `createPrefsStore({fetch?,initial?})`), so R-STAGE and Settings import it with zero guesswork. Server
  is source of truth (`GET/PUT /preferences`), mirrored to `localStorage['glyde:prefs']` for instant
  first paint + offline, reconciled on load, **write-through the full object on every change** (PUT is
  full-replace, §4.5) — so the **last-used mode is restored next open**. The factory's **injected
  `fetch`** makes the persist round-trip unit-testable with no server (assay typed-seam discipline,
  docs/research/assay-adoption.md §2; mutations through an injected gateway/`fetch`, never a module
  singleton). A Settings route with grouped controls (Reading: mode/speed/chunk/ramp; Comfort:
  font/size/spacing/theme; Context: treatment/size) and a live preview word.
  - **Svelte MCP + assay:** Use the Svelte MCP tools if available (ToolSearch 'svelte'); if absent from
    your context, use context7 for current Svelte 5 / SvelteKit / runes docs and run svelte-check as the
    runes-idiom gate; in all cases follow docs/research/assay-adoption.md.
- **owned_paths:** `FE/lib/domains/preferences/*`, `FE/routes/settings/+page.svelte`,
  `FE/routes/settings/+page.ts` (if a `load` is needed).
- **depends_on:** F0, X1.
- **e2e recipe:** GATES-FE; **component test** named
  `lib/domains/preferences/prefs.component.test.ts` (the **jsdom** `component` project — §5.3 suffix;
  jsdom is required for `localStorage`; `@testing-library/svelte`, run by `npm run test`): with an
  injected fake `fetch`, set `mode='rsvp'` on the store and assert (a)
  `localStorage['glyde:prefs']` parses to `mode === 'rsvp'` synchronously, and (b) the fake received a
  `PUT /preferences` carrying the **complete** `Preferences` object; build a second store from the same
  localStorage and assert it reads `mode === 'rsvp'` back (restore). E2E-READER — change mode in
  Settings → reload → restored; `curl -s localhost:8000/preferences` reflects the `PUT`.

### R-CORE — Reader pacing engine + reader prop contract

- **summary:** The shared reader spine the mode/block/chrome units import; **R-CORE freezes the full
  contract pinned in §5.7** (`types.ts` + `engine.svelte.ts`) — Wave-2/3 units import it and never amend
  either file. The **pacing engine** (`engine.svelte.ts`, the `createReaderEngine` factory of §5.7):
  consumes the IR `SegmentView` timeline (not a flat string), owns position + the **block state machine**
  (`activeBlock`/`blockAhead`/re-show) and computes pivot index + `dwell_ms` client-side from
  `Preferences` + the §5.6 constants. Built to the assay `.svelte.ts` state-machine shape
  (docs/research/assay-adoption.md §1): **`$state` getters + imperative methods, an INJECTED clock
  (defect-fix, §5.7) and ZERO `$effect` in the factory** — so it is headless-constructible and the
  next-token cadence runs imperatively through the clock (pure pacing is `$derived`); **no module-level
  rAF/`performance.now`**, and the DOM measure-and-translate is R-MODES's, not the engine's. The
  cadence math (WPM→ms, ORP bucket, pause-at-punctuation) lives in the **pure `cadence.ts`** (§5.6),
  node-testable; `reducedMotion` is read once at construction and gates the word-flash cadence. The
  **typed prop contract** (`types.ts`): `ReaderState`, `ReaderEngine`, `ModeProps`, `BlockCardProps`,
  `BlockAheadCueProps`, `TransportProps`, `ProgressProps` — every member fixed in §5.7, so no consuming
  unit recomputes pacing (SCOPING risk #9).
  - **Svelte MCP + assay:** Use the Svelte MCP tools if available (ToolSearch 'svelte'); if absent from
    your context, use context7 for current Svelte 5 / SvelteKit / runes docs and run svelte-check as the
    runes-idiom gate; in all cases follow docs/research/assay-adoption.md.
- **owned_paths:** `FE/lib/domains/reader/engine.svelte.ts`, `FE/lib/domains/reader/cadence.ts`
  (pure cadence math — §5.6), `FE/lib/domains/reader/types.ts`, `FE/lib/domains/reader/index.ts`,
  `FE/lib/domains/reader/engine.test.ts`.
- **depends_on:** F0. (Consumes the named `TokenView`/`SegmentView`/`PreferencesView` **types** from
  `schema.d.ts`, not PREF's store.)
- **e2e recipe:** GATES-FE; **vitest** unit tests on the engine (`engine.test.ts` — the **node**
  `unit` project, **no DOM** needed; §5.3 names it plain `*.test.ts`, **not** `*.component.test.ts`)
  constructing the engine with a **fake injected clock** (`createReaderEngine({…, clock})`) and
  advancing it deterministically (the headless-constructibility defect-fix; it also exercises the pure
  `cadence.ts` directly) — these run under `npm run test`, so a broken engine fails the gate. Pacing: at 300 wpm (`base = 200 ms`,
  low-freq multiplier deferred) a 12-letter word ending a sentence → `200 × (1 + 0.03·4) × 2.2 ≈ 493 ms`;
  a short mid-sentence word → ~200 ms; pivot bucket boundaries (`len` 1/5/9/13). **Block state machine**
  (command-verifiable, no DOM): drive the engine over a `[prose, Pause(block_ahead), Block(code), prose]`
  fixture and assert `blockAhead` flips true during the lead window, `activeBlock` becomes the code block
  when reached (the stream auto-pauses), `toggle()` clears `activeBlock` and advances, and
  `reshowLastBlock()` re-sets `activeBlock` to that block.

### R-MODES — The three reading modes

- **summary:** The presentational mode views taking engine state via `ModeProps`. **RSVP**
  (`Rsvp.svelte`): the **DOM measure-and-translate** of the pivot glyph (it lives here, in this unit's
  `$effect` at the DOM boundary — NOT the engine, §5.7), red pivot x-locked to the reticle, context
  above/below dimmed one word each side. **Flow** (`Flow.svelte`): Guided sweep + Fading trail
  (full text, left-aligned, discrete jump — never teleprompter-scroll). All three exist; default
  Guided is enforced by PREF/R-STAGE, not here.
  - **Assay motion discipline (docs/research/assay-adoption.md §1):** animate the moving marker / fade
    trail with **compositor-only `transform`/`opacity` + CSS transitions** (never `left`/`width`/`top`);
    **gate ALL motion on `prefers-reduced-motion`** (the engine's `reducedMotion`, read once at bind
    time) — a reduced-motion user gets the instant outcome, no travel/flash (non-negotiable for a
    flashing reader: accessibility + seizure concern). Use the `reading`/`reading-foreground`/
    `reading-dim`/`pivot` tokens (§5.8) only.
  - **Svelte MCP + assay:** Use the Svelte MCP tools if available (ToolSearch 'svelte'); if absent from
    your context, use context7 for current Svelte 5 / SvelteKit / runes docs and run svelte-check as the
    runes-idiom gate; in all cases follow docs/research/assay-adoption.md.
- **owned_paths:** `FE/lib/domains/reader/modes/*` (`Rsvp.svelte`, `Flow.svelte`, `index.ts`).
- **depends_on:** F0, R-CORE, X1.
- **e2e recipe:** GATES-FE; **component tests** named `modes/Rsvp.component.test.ts` +
  `modes/Flow.component.test.ts` (the **jsdom** `component` project — §5.3 suffix;
  `@testing-library/svelte`, run by `npm run test` — **the binding gate**, §5.9 PATH A, not screenshots):
  mount `Rsvp.svelte` with a `ModeProps` fixture and
  assert the pivot glyph is marked at `state.pivotIndex` and the context words render dimmed; mount
  `Flow.svelte` in `guided` and `fading` and assert the current word (`state.wordIndex`) carries the
  highlight class and the read words the faded class. Optional PATH B screenshot (each mode on top: RSVP
  pivot centred on the reticle, Guided current word highlighted, Fading read-words faded out).

### R-BLOCKS — Block cards (full spec-001)

- **summary:** The full pause-and-show family. On a `Pause(block_ahead)`, show the accent "code
  ahead" chip during the last prose words; on a `Block`, auto-pause the stream and render a static
  full-width card per kind: **code** (legible monospace, mobile horizontal-scroll + wrap toggle),
  **table** (rendered grid; wide → stacked `header: value`), **image** (`<img>` or alt fallback),
  **math** (`linear_form` aside or raw), **quote**, **note**. Space/tap resume and `Left` re-show are
  driven by the engine's `activeBlock` (R-STAGE owns the one global listener, §5.7) — **the cards bind
  no keys**, they are pure presentational over `BlockCardProps`. Block kind is labelled. (Docstrings
  state these as capabilities — no "spec 001" in source.)
  - **Svelte MCP + assay:** Use the Svelte MCP tools if available (ToolSearch 'svelte'); if absent from
    your context, use context7 for current Svelte 5 / SvelteKit / runes docs and run svelte-check as the
    runes-idiom gate; in all cases follow docs/research/assay-adoption.md.
- **owned_paths:** `FE/lib/domains/reader/blocks/*` (`CodeCard.svelte`, `TableCard.svelte`,
  `ImageCard.svelte`, `MathCard.svelte`, `QuoteCard.svelte`, `NoteCard.svelte`,
  `BlockAheadCue.svelte`, `index.ts`).
- **depends_on:** F0, R-CORE, X1.
- **e2e recipe:** GATES-FE; **component tests** named `blocks/*.component.test.ts` (one per card or a
  single `blocks/cards.component.test.ts`; the **jsdom** `component` project — §5.3 suffix;
  `@testing-library/svelte`, run by `npm run test`): mount each card with a `BlockCardProps` fixture
  and assert it renders its content —
  `CodeCard` shows the code text + lang label, `TableCard` renders an N-row grid and switches to
  stacked `header: value` under a narrow container (the existing table→stacked transform test),
  `ImageCard` falls back to `alt` when `src` fails, `MathCard` shows `linear_form` when present else
  the raw `content`, `QuoteCard`/`NoteCard` render their text; mount `BlockAheadCue` and assert it
  shows the `kind` label only when `visible` (the binding gate, §5.9 PATH A). Optional PATH B
  screenshot: a code + table pause with the block-ahead cue, then resume and `Left`-re-show the last card.

### R-CHROME — Transport + progress

- **summary:** Thumb-first chrome that auto-hides during playback. **Transport** (`Transport.svelte`):
  a slim bottom bar (replay-word / play-pause / step-forward) and an edge speed rail (drag up =
  faster), every control a `TransportProps` callback into the engine (**no global listener here** — the
  tap-stage gesture is R-STAGE's, §5.7). **Progress** (`Progress.svelte`): a hairline bar with
  **notches marking upcoming blocks** (`ProgressProps.blockNotches`), tap-to-scrub, and prominent
  **time-remaining** ("~2m 14s left", tabular-nums) with position secondary. Controls are real
  `<button>`s with **≥44px touch targets** (`min-h-11 min-w-11`) + `:focus-visible` rings
  (docs/research/assay-adoption.md §3).
  - **Svelte MCP + assay:** Use the Svelte MCP tools if available (ToolSearch 'svelte'); if absent from
    your context, use context7 for current Svelte 5 / SvelteKit / runes docs and run svelte-check as the
    runes-idiom gate; in all cases follow docs/research/assay-adoption.md.
- **owned_paths:** `FE/lib/domains/reader/Transport.svelte`, `FE/lib/domains/reader/Progress.svelte`,
  `FE/lib/domains/reader/Transport.component.test.ts`, `FE/lib/domains/reader/Progress.component.test.ts`.
- **depends_on:** F0, R-CORE, X1.
- **e2e recipe:** GATES-FE. **R-CHROME has no route of its own** (its host is R-STAGE's `/d/[slug]`),
  so its **binding gate is component tests** (`Transport.component.test.ts` + `Progress.component.test.ts`
  — the **jsdom** `component` project, run by `npm run test`; §5.3 suffix): mount `Transport.svelte`
  with a `TransportProps` fixture whose callbacks are **plain capture closures** (no mocking lib, §5.3),
  click replay / play-pause / step and the speed rail, and assert `onReplayWord` / `onToggle` /
  `onStepForward` / `onSpeed` each fired with the right argument; mount `Progress.svelte` with a
  `ProgressProps` fixture and assert it renders `wordIndex`/`wordCount`, the time-left string
  (`remainingMs` → "~2m 14s left", tabular-nums), one notch per `blockNotches` entry, and that a tap on
  the bar calls `onScrub` with a word index. **Any visual check is deferred to R-STAGE** (which mounts
  the chrome in the real reader and verifies auto-hide, notches, and time-left at a 390 px viewport via
  §5.9 PATH A, optionally PATH B) — R-CHROME has no route, so it **never gates on a screenshot**; its
  component tests are the gate.

### R-STAGE — Reader route + composing stage

- **summary:** The integrator and the longest pole's keystone. The reader route `load` fetches
  `GET /api/digests/{slug}` through the typed seam (the assay discipline, docs/research/assay-adoption.md
  §2: per-request `fetch`, absolute `${url.origin}/api` base, branch `{data,error}` — a 200 is not
  success, `error(502,…)` on failure); `Reader.svelte` wires the engine + the current mode (R-MODES) +
  block pause/cards (R-BLOCKS) + transport/progress (R-CHROME), reading `Preferences` from PREF's store
  (§5.10), mapping `block.kind` → the right card, and picking `mode` → Rsvp/Flow. **Owns the single
  global keyboard + tap/swipe listener** (§5.7): one `$effect` binds `window` `keydown` (→ the **pure
  `keyToIntent(key)` map** in `input.ts` → engine) + the stage gesture via **`bindSwipe`** (the assay
  Pointer-Events adapter in `input.ts`: axis-lock past 8px, ignore-zone on the reading body, feature-
  detected `setPointerCapture`, reduced-motion read once; docs/research/assay-adoption.md §1) — `Space`/
  tap → `engine.toggle()`, `ArrowLeft` → `engine.reshowLastBlock()`, `ArrowRight` → `engine.stepForward()`,
  **horizontal swipe → `engine.scrubTo`/`stepForward` (vertical yields to native scroll)** — so no other
  unit registers a global listener. The stage element carries the `role`+`tabindex`+`aria-label`+keyboard
  **quartet** (§5.7) so its gesture clears the CI-fatal `a11y_no_static_element_interactions` check.
  **The a11y spine (docs/research/assay-adoption.md §1):** a single `aria-live="polite"` `sr-only`
  announcer (play/pause, position, speed, block-shown), **roving focus** re-focusing the stable stage
  region on word/segment advance (no drop to `<body>`), and **focus-scoped keydispatch** —
  `preventDefault()` on every handled key, an `isEditable()` guard (never fire while typing), shortcuts
  only while the stage holds focus, and a visible control mirroring every gesture (WCAG 2.5.1). Enforces
  **default Guided** on first run and **persists the last-used `mode`** back to `Preferences` via PREF.
  The calm stage: the word is the screen; pauses are felt as a beat; blocks transform the stage into a
  static card. (If the night slips, gestures degrade to tap-only — the existing stage `pointerdown`; the
  pure `keyToIntent`/`classifySwipe` in `input.ts` stay node-testable regardless.)
  - **Svelte MCP + assay:** Use the Svelte MCP tools if available (ToolSearch 'svelte'); if absent from
    your context, use context7 for current Svelte 5 / SvelteKit / runes docs and run svelte-check as the
    runes-idiom gate; in all cases follow docs/research/assay-adoption.md.
- **owned_paths:** `FE/routes/d/[slug]/+page.ts`, `FE/routes/d/[slug]/+page.svelte`,
  `FE/lib/domains/reader/Reader.svelte`, `FE/lib/domains/reader/Reader.component.test.ts`,
  `FE/lib/domains/reader/input.ts` (pure `keyToIntent` + `classifySwipe` + the `bindSwipe` DOM adapter),
  `FE/lib/domains/reader/input.test.ts` (the **node** `unit` project — pure classifiers, no DOM).
- **depends_on:** F0, R-CORE, R-MODES, R-BLOCKS, R-CHROME, PREF, X1.
- **e2e recipe:** GATES-FE; **integration tests** in `lib/domains/reader/Reader.component.test.ts`
  (the **jsdom** `component` project — §5.3 suffix; `@testing-library/svelte`, run by `npm run test`)
  that gate the headline behaviours — these must pass as assertions, not only as screenshots:
  - **default Guided on first run:** render `Reader.svelte` with a fresh PREF store (no localStorage;
    injected `fetch` returns default prefs) and assert the Guided/Flow view mounts (not RSVP).
  - **last-used mode round-trip:** switch mode to `rsvp`; assert PREF wrote through (the fake `fetch`
    got `PUT /preferences` with `mode:"rsvp"` **and** `localStorage['glyde:prefs'].mode === 'rsvp'`);
    re-render `Reader.svelte` from that persisted prefs and assert **RSVP mounts**.
  - **block state machine through the stage:** feed a code-bearing digest, advance to the block, assert
    the `CodeCard` is in the DOM and the stream is paused; dispatch `Space` (a `window` keydown) and
    assert the card is gone and playback resumed; dispatch `ArrowLeft` and assert the card re-shows.
  Then E2E-READER (the full loop) — `glyde add` a code-bearing digest, open `/d/{slug}`: prose streams;
  all three modes switchable; **default Guided** on a fresh prefs store; switch to RSVP, reload →
  **RSVP restored**; the code block auto-pauses, the cue precedes it, Space resumes, `Left` re-shows.
  **This E2E is also where Transport/Progress get their visual check** (deferred from R-CHROME, which
  has no route): at a 390 px viewport assert (via the route/jsdom mount, §5.9 PATH A) chrome auto-hides
  during playback and Progress shows block notches + time-left; optional PATH B screenshot for a human
  eyeball.

### LAN — LAN serve + QR + bearer token (relief valve)

- **summary:** Fill F0's `serve_lan` stub so the **whole app** is served to a phone on the LAN,
  read-only. **The v1 front-door design (pinned here, since it is multi-process):** `serve_lan(settings)`
  runs the FastAPI app via `uvicorn` bound to **`127.0.0.1:{port}`** (local only) **and**
  `subprocess.Popen`-spawns the built SvelteKit **adapter-node** server (`node frontend/build/index.js`)
  bound to **`0.0.0.0:{lan_port}`** with env `HOST=0.0.0.0`, `PORT={lan_port}`,
  `ORIGIN=http://{lan_ip}:{lan_port}`, and `GLYDE_API_ORIGIN=http://127.0.0.1:{port}`. The node server is
  the single front door; `hooks.server.ts`'s `handle` returns **before `resolve()`** for `/api/*`, strips
  `/api`, **proxies → `GLYDE_API_ORIGIN`** (so the phone never talks to FastAPI directly), and
  `filterSerializedResponseHeaders` allows `content-type`+`content-length` (else hydrating typed-seam
  reads throw). At that door it runs **two complementary guards** (docs/research/assay-adoption.md §3):
  (1) the assay **CSRF origin assertion** — reject only a non-GET whose *present* `Origin` fails strict
  same-origin (an **absent** `Origin` is allowed: trusted SSR re-entry / local agent); and (2) **asserts
  the bearer token on `/api` mutations only** (reads stay open — phone is read-only). FastAPI uses
  `root_path="/api"` + explicit `servers=[{"url":"/api"}]`. `serve_lan` detects the LAN IP (the
  UDP-connect trick), **computes `ORIGIN` ONCE — the assay "triad": adapter-node `ORIGIN` env = QR
  payload = the CSRF compare value** (a mismatch 403s every mutation silently), reads/mints
  `settings.lan_token`, polls both servers to **liveness+readiness** before rendering the QR (`segno`)
  for `http://{lan_ip}:{lan_port}/?token=…` (`?token` → localStorage → `Authorization: Bearer` via
  `FE/lib/api/token.ts`), prints URL + QR + token, and tears both processes down on exit. The token is a
  guard, not authentication (and says so). **Reach the app via the printed LAN URL the QR encodes** —
  `localhost` against a LAN `ORIGIN` 403s on mutations.
  **LAN adds NO FastAPI path operation** (§5.4): `API/routes/lan.py` stays the **route-less** router
  F0 registered, and the guard lives only in `hooks.server.ts` (the proxy) — so the F0-frozen
  `docs/schemas/openapi.json` (§9) is untouched and `test_committed_openapi_matches_the_app` stays
  green. **Requires `frontend/build/` to exist** — `npm run build` (the GATES-FE build step) produces it.
  - **HTTPS-over-LAN now (the LAN half of the §5.11 split; docs/research/assay-adoption.md §3):** an
    installable/offline reader needs a **secure context** that a plain-HTTP LAN origin is not, so
    `serve_lan` optionally fronts adapter-node with a **`node:https`** wrapper (`frontend/serve-lan-https.mjs`)
    using an **mkcert** cert for the LAN IP / `glyde.local` (`settings.lan_https` + `lan_cert_path` +
    `lan_key_path`, declared in F0's Settings surface, §7) — trust the mkcert root CA on the phone once.
    HTTPS is the **first thing to degrade within LAN** (HTTPS → plain-HTTP LAN → localhost); over
    plain-HTTP LAN the SW simply never registers (correct), and keep the `crypto.randomUUID` →
    `getRandomValues` v4 fallback as free insurance for any future client-minted id (Glyde mints ids
    server-side today).
  - **PWA payload (LAN-owned static):** `manifest.json` (standalone, portrait, dark `theme_color`,
    192/512 + maskable icons), `static/icons/*`, and the classic shell-cache `sw.js` whose **`/api/*`
    passthrough is the FIRST statement** (a cache miss must never shadow a live read/mutation), caching
    only `/_app/immutable/**`, never HTML navigations. **Glyde's extension (docs/research/assay-adoption.md
    §3 divergence):** a **narrow** read-through cache for `GET /api/digests/{slug}` (the Digest IR,
    versioned key, stale-while-revalidate) placed **before** the general `/api/*` passthrough — only that
    one read path is cached for offline reading; list / preferences / mutations stay passthrough. (X1
    owns the shell hooks that reference these by runtime URL, §5.11.)
  - **Svelte MCP + assay:** Use the Svelte MCP tools if available (ToolSearch 'svelte'); if absent from
    your context, use context7 for current Svelte 5 / SvelteKit / runes docs and run svelte-check as the
    runes-idiom gate; in all cases follow docs/research/assay-adoption.md.
- **owned_paths:** `API/lan.py`, `API/routes/lan.py` (fill F0's scaffolds), `FE/hooks.server.ts`,
  `FE/lib/api/token.ts`, `FE/hooks.server.test.ts`, `frontend/static/manifest.json`,
  `frontend/static/sw.js`, `frontend/static/icons/*`, `frontend/serve-lan-https.mjs` (the `node:https`
  wrapper). (`InstallHint.svelte` + the SW registration / manifest `<link>` are **X1's** shell hooks,
  §5.11 — referenced by runtime URL, not imported, so cutting LAN keeps X1 green.)
- **depends_on:** F0 only. (Touches no shell/theme/`ui/` file and **imports** none, so it is
  **compile-independent of X1** — Wave 1. F0 already added `segno` and declared `settings.lan_host`/
  `lan_port`/`lan_token` **and the HTTPS fields `lan_https`/`lan_cert_path`/`lan_key_path`** (§7), so LAN
  edits no pyproject, `uv.lock`, or `cli.py`. The **PWA is runtime-complete only once X1 has also merged**
  — X1's `+layout.svelte` registers the `/sw.js` LAN serves — but each builds green alone, §5.11.)
- **e2e recipe:** GATES-BE + GATES-FE; `cd frontend && npm run build`, then `uv run glyde serve --lan`
  prints the QR + token + LAN URL. From another LAN host (or `curl --resolve`): a `/api` **mutation**
  with no token → **401**, with `Authorization: Bearer {token}` → **201**; a **read** (`GET /api/digests`)
  with no token still **200s**. Unit-test the `hooks.server.ts` guard in `src/hooks.server.test.ts`
  (the **node** `unit` project — no DOM; §5.3) with an injected fake event over the matrix (token
  present/absent × read/mutation) under `npm run test`.
- **cuttable:** yes (second overboard). If cut, F0's `serve_lan` stub ships — uvicorn on `settings.host`
  (localhost), no node spawn, no QR, no token guard — documented as the v1 reach. With no
  `hooks.server.ts` / `static/sw.js` / `manifest.json` (all LAN-owned, absent when LAN is cut), the
  frontend still builds green: X1's guarded SW registration `.catch()`es the missing `/sw.js` and the
  manifest `<link>` 404s harmlessly, so mobile ergonomics (viewport, ≥16px, ≥44px, no-flash) still ship
  via X1 — only the installable/offline/HTTPS layer is lost (§5.11).

### HAIKU — Haiku enrich (STRETCH)

- **summary:** The isolated raw-text → Glyde-Markdown structuring pass. `enrich(raw, *, api_key,
  client=None) -> str` (content **verbatim and in order**, low temperature, **Anthropic Messages
  API** `client.messages.create`, a Haiku-class model — verify the exact model id + params via the
  **`claude-api` skill** at implementation). Sync (adapters-async gate clean). Key injected via
  `Settings.anthropic_api_key`, passed as an argument — never read in `core`. Upgrades F0's
  `API/enrich.py` so `get_enricher(settings)` returns the callable only when a key is present, else
  `None`; `compose_digest` calls it only when `enrich AND key AND no structure detected`, wrapped
  `try/except → raw`. Tested via the injected `client` param with a **hand-written fake client**
  (a real object exposing `.messages.create`, returning a canned response) — the verified-fake
  pattern, so **no `unittest.mock` and no allowlist edit** (keeps `TESTS/architecture/` entirely
  F0's).
- **owned_paths:** `ADAPT/enrich.py` (new), `API/enrich.py` (upgrade F0's stub),
  `TESTS/adapters/test_enrich.py` (new file — F0 does not create it). (`anthropic` is already
  declared + locked by F0 — HAIKU touches no pyproject or `uv.lock`.)
- **depends_on:** F0.
- **e2e recipe:** GATES-BE (with a fake `client` — no network); then
  `printf 'a raw log line' | GLYDE_ANTHROPIC_API_KEY= uv run glyde add --enrich --name L` →
  passthrough digest (no key → deterministic parse, never an error).
- **cuttable:** yes (first overboard). If cut, F0's `get_enricher → None` stub ships (deterministic
  parse always); no gate references it.

### DOCS — Glossary + ADRs + authoring guide

- **summary:** Canonicalise the new vocabulary and record the load-bearing decisions. Add **Digest /
  Segment / Token / Provenance / slug** to the glossary (and retire the `Record` line); write the
  IR ADR and the LAN-token ADR; write the agent handoff-authoring guide (lead into a block with a
  prose sentence, summarise long code then show it, one idea per pause, `==highlight==` the
  decision).
- **owned_paths:** `docs/glossary.md`, `docs/decisions/0005-digest-ir.md`,
  `docs/decisions/0006-lan-token.md`, `docs/product/glyde-handoff-authoring.md`.
- **depends_on:** F0.
- **e2e recipe:** `prek run --all-files` passes; every code link resolves to a GitHub blob at a
  pinned SHA; the glossary defines every term F0 introduced.

---

## 9. File-ownership map (pairwise-disjoint proof)

Every fan-out unit's paths are disjoint from every other fan-out unit's. F0 hands off exactly the
three §5.4 files. `*` = directory the unit owns wholly.

| Unit | Backend paths | Frontend paths | Docs |
|---|---|---|---|
| **F0** | `CORE/models/*`, `CORE/derive.py`, `CORE/parsing/*`, `CORE/ports/*`, `CORE/__init__.py`, `ADAPT/sqlite/{digest_store,schema.sql,__init__}.py` + `migrations/0002_digests.sql`, `API/{compose,slug,settings,deps,app,cli}.py`, `API/wordbank/*`, `API/schemas/*`, `API/routes/{__init__,digests,preferences,meta}.py`, `TESTS/{support,core}/*` + `TESTS/adapters/sqlite/*` + `TESTS/api/*` (the digest suites in §7; the layout-agnostic `TESTS/architecture/*` stays untouched and passes as-is; `TESTS/adapters/test_enrich.py` is HAIKU's), all three `pyproject.toml`s, `uv.lock` | `schema.d.ts` (regen), **delete** `routes/+page.*` (FE `package.json`/lockfile are **X1's** — read-only to F0) | `docs/schemas/openapi.json` (committed **with** the empty `lan` router registered) |
| **X1** | — | `app.css`, `app.html`, `routes/+layout.svelte`, `lib/components/ui/*` (incl. `InstallHint.svelte`), `routes/dev/+page.svelte`, `package.json`, `package-lock.json`; *(optional/uncommitted, §5.8/§5.9: `frontend/playwright.config.ts`, `frontend/e2e/*`)* | — |
| **LIB** | — | `routes/+page.{ts,svelte}` (create), `lib/domains/library/*` | — |
| **PREF** | — | `lib/domains/preferences/*` (incl. `prefs.component.test.ts`), `routes/settings/*` | — |
| **R-CORE** | — | `lib/domains/reader/{engine.svelte.ts,cadence.ts,types.ts,index.ts,engine.test.ts}` | — |
| **R-MODES** | — | `lib/domains/reader/modes/*` (incl. `*.component.test.ts`) | — |
| **R-BLOCKS** | — | `lib/domains/reader/blocks/*` (incl. `*.component.test.ts`) | — |
| **R-CHROME** | — | `lib/domains/reader/{Transport,Progress}.svelte` + `{Transport,Progress}.component.test.ts` | — |
| **R-STAGE** | — | `routes/d/[slug]/*`, `lib/domains/reader/{Reader.svelte,Reader.component.test.ts,input.ts,input.test.ts}` | — |
| **LAN** | `API/lan.py`, `API/routes/lan.py` (fill F0 stubs; route-less) | `hooks.server.ts`, `lib/api/token.ts`, `hooks.server.test.ts`, `frontend/static/{manifest.json,sw.js,icons/*}`, `frontend/serve-lan-https.mjs` | — |
| **HAIKU** | `ADAPT/enrich.py`, `API/enrich.py` (fill F0 stub), `TESTS/adapters/test_enrich.py` | — | — |
| **DOCS** | — | — | `glossary.md`, `decisions/0005*`, `decisions/0006*`, `product/glyde-handoff-authoring.md` |

`lib/domains/reader/` is partitioned **by filename** (tests included):
`{engine.svelte.ts,cadence.ts,types.ts,index.ts,engine.test.ts}` (R-CORE) · `modes/*` (R-MODES) ·
`blocks/*` (R-BLOCKS) · `{Transport,Progress}.svelte` + `{Transport,Progress}.component.test.ts`
(R-CHROME) · `{Reader.svelte,Reader.component.test.ts,input.ts,input.test.ts}` (R-STAGE). Each subdir
exports via its own `index.ts`; consumers import from those, so `reader/index.ts` stays R-CORE's alone.
The new files stay disjoint: R-CORE's pure `cadence.ts` and R-STAGE's pure `input.ts`/`input.test.ts`
sit beside, not inside, any other unit's set; **LAN solely owns** the `frontend/static/*` PWA payload +
`frontend/serve-lan-https.mjs`, while **X1 solely owns** the shell hooks that reference them by runtime
URL (`/sw.js`, `/manifest.json`) — a runtime reference, never an import, so the two never edit a shared
file (§5.11). **No two fan-out units share any path.** F0 owns the **entire backend** dependency surface
(all three `pyproject.toml`s + `uv.lock`, declaring `platformdirs`/`segno`/`anthropic` up front), so
**no fan-out unit touches a pyproject or `uv.lock`** — LAN and HAIKU import already-locked deps. **X1
owns the entire FE dependency surface** (`frontend/package.json` + `package-lock.json`, declaring
`@lucide/svelte`, §5.8), so **no Wave-2/3 FE unit touches `package.json`** — F0 treats the FE deps as
read-only; the optional Playwright dep (PATH B) is installed on-demand, never committed by default
(§5.8/§5.9).

---

## 10. Definition of done (global)

The build is done when **every** item holds:

- **Backend green:** `uv run ruff format --check .` · `ruff check .` · `ty check` · `lint-imports` ·
  `pytest --cov` (architecture tests pass; `core` 100% branch) · `prek run --all-files`.
- **Frontend green:** `npm run lint` · `check` (svelte-check, zero a11y) · `typecheck` · `test` ·
  `boundaries` · `check:api-drift` · `build`.
- **Seam:** `docs/schemas/openapi.json` committed and equal to the live app; `schema.d.ts`
  regenerated; both drift gates green. The **named wire members** (`TokenView`, `ProseSegmentView`,
  `PauseView`, `BlockView`, `DigestView`, `DigestListItemView`, `PreferencesView`) are present and
  `DigestView.segments.items` is a **`oneOf` of named `$ref`s carrying a `discriminator`
  (`propertyName: "type"`) — asserted on the exported `openapi.json`, not `anyOf`, not the `.d.ts`**
  (§4.5, §7); LAN and HAIKU added **no** path operation, so the live OpenAPI still equals F0's frozen
  artifact.
- **End-to-end, per feature:**
  - `glyde add` (text arg / stdin pipe / file path) prints name + slug + URL; `glyde list` lists
    the library.
  - `/d/{slug}` renders the IR with **all three modes**, **default Guided** on first run, the
    **last-used mode restored** next open, and the **full block-card set** (cue, pause-and-show for
    code/table, grid, image, math, re-show on `Left`, Space-resume). These behaviours are **gated by
    vitest/@testing-library assertions under `npm run test`** (R-CORE block state machine; R-STAGE
    default-Guided + mode round-trip + block resume/re-show; PREF persist round-trip), not screenshots
    alone — a reader PR cannot land green with them broken. If the SvelteKit reader slips entirely,
    `glyde read <slug>` (flattened prose + `[block]` placeholders, §3) is the command-verifiable
    fallback floor.
  - `/` shows the minimal library (name · mono slug · provenance · shape counts → tap to read).
  - `GET/PUT /preferences` round-trips; the reader and Settings agree on `Preferences`.
  - `serve --lan` binds the front door with a QR + token-gated mutations (phone read-only) — or,
    if LAN was cut, localhost serving works and is documented as the v1 reach.
  - Haiku-enrich, if shipped, structures raw text behind `--enrich` + a key and falls back to
    deterministic parse without one — or, if cut, the deterministic path is the only path.
- **Matches spec:** the four binding decisions (§2) are satisfied; nothing in §1's Phase-2/Later
  list leaked into the diff; out-of-scope discoveries went to `docs/issues/` or the backlog.

**Done = green CI + matches spec.** A red gate is the architecture speaking: fix the code, never
loosen a contract or budget. Contract changes are ADRs.
