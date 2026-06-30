# Glyde v1 — Staff engineering design + work-unit decomposition

Concrete design for the locked scope. The **Digest IR is the keystone**: parsed into, persisted,
served, rendered — defined once in `core`, mirrored to the frontend via the existing typed seam.
Path roots (abbreviated below): `core = backend/packages/core/src/glyde/core`,
`adapters = .../adapters/src/glyde/adapters`, `api = .../api/src/glyde/api`, `fe = frontend/src`.

## (a) The Digest IR — Pydantic v2 in `core/models/` (one concept per file, ≤400 lines)

All models `frozen=True, extra="forbid"`. The segment union is a Pydantic **discriminated union on
`type`** — `word` is a `Token`, `emphasis{level}` is `Token.emphasis`, `pause{reason,…}` and
`block{kind,…}` are segments (the orchestrator's union, organised correctly per the panel's
"tokenise at ingest / emphasis is a token property" call).

```python
# token.py        — the streaming atom ("word")
class Token(BaseModel):           # frozen, extra=forbid
    text: str
    kind: Literal["word", "punct"] = "word"
    emphasis: Literal["none", "strong", "em", "code"] = "none"   # "emphasis{level}"
    hold: float | None = None     # coarse agent dwell hint — NOT milliseconds
# segment.py
class ProseSegment(BaseModel):    # the streamed body
    type: Literal["prose"] = "prose"
    role: Literal["heading", "body", "list_item"] = "body"
    tokens: list[Token]
class Pause(BaseModel):           # "pause{reason, duration}"
    type: Literal["pause"] = "pause"
    reason: Literal["clause", "sentence", "paragraph", "block_ahead"]
    duration_scale: float = 1.0   # coarse weight; reader maps reason+scale → ms
class Block(BaseModel):           # "block{kind, payload, ...}"
    type: Literal["block"] = "block"
    kind: Literal["code","table","image","diagram","math","quote","note"]
    content: str                  # raw — NEVER streamed word-by-word
    lang: str | None = None       # code
    lead: str | None = None       # the prose runway sentence it follows
    alt: str | None = None        # image/diagram alt
    linear_form: str | None = None  # spoken form for promoted math
type Segment = Annotated[ProseSegment | Pause | Block, Field(discriminator="type")]
# provenance.py
class Provenance(BaseModel):
    source_kind: Literal["agent","file","cli","paste","pipe","api"]
    origin: str | None = None      # path | url | repo@sha | run-id
    producer: str | None = None    # the producing agent/model ("agent")
    ingested_via: Literal["cli","api","mcp"] = "cli"
    enriched: bool = False
# digest.py
class ReadingHint(BaseModel):  suggested_mode: Literal["rsvp","guided","fading"]
class DigestMeta(BaseModel):
    id: str; slug: str; name: str; provenance: Provenance; created_at: str
    token_count: int; est_reading_ms: int; content_sha: str
    ir_version: int = 1; owner_id: str = "local"
    reading_hint: ReadingHint | None = None
class Digest(BaseModel):  meta: DigestMeta;  segments: list[Segment]
```

**Decisions (flagged):** (1) the orchestrator's `pause{duration_ms}` is stored as **coarse
`duration_scale`, not ms** — ms is a function of wpp/mode/font and freezes pacing against a settings
change (panel-decided: flash-ms lives in the reader). `est_reading_ms` on *meta* is a derived display
estimate, fine as a number. (2) The orchestrator's meta-`settings` is realised as the optional
**`reading_hint`**, not live settings — settings are per-user `Preferences`, never digest content.
**Typed-seam mirror:** the api wire-schemas (§e) project these models; `glyde export-openapi` →
`openapi.json` → `npm run gen:api` → `fe/lib/api/schema.d.ts`. The frontend imports `Segment`,
`Digest`, `Preferences` types straight off `schema.d.ts` — one definition, both halves.

```python
# preferences.py — per-user config, keyed by owner_id (NOT on the digest)
class Preferences(BaseModel):
    owner_id: str = "local"
    mode: Literal["rsvp","guided","fading"] = "guided"   # DEFAULT guided; last-used persisted
    wpm: int = 300; context: Literal["off","ab","line","sentence"] = "ab"; ctx_scale: float = 0.7
    chunk: int = 1; size_px: int = 64; letter_spacing_em: float = 0.04
    font: Literal["atkinson","lexend","opendyslexic","system","serif","mono"] = "atkinson"
    theme: Literal["dark","light","sepia"] = "dark"; ramp: bool = True
```

## (b) Glyde Markdown grammar + the pure parser (`core/parsing/`)

CommonMark subset + spec-001 block markers + one prose mark. Pure, deterministic, the **only** ingest
path (`parse_glyde_markdown(text: str) -> list[Segment]`); no clock/uuid/IO (purity-gate clean).

- Headings `#…` → `ProseSegment(role=heading)`; blank line → `Pause(paragraph)`; list item → `role=list_item`.
- Fenced ``` ```lang ``` → `Block(code, lang)`; pipe table → `Block(table)`; `![alt](src)` → `Block(image, alt, content=src)`; `:::pause … :::` → `Block(note)`; display `$$…$$` → `Block(math, linear_form?)`; `> …` → `Block(quote)`. A `Pause(block_ahead)` is **emitted before every block**.
- Prose tokenises into `Token`s; trailing `,;:` → following `Pause(clause)`, `.!?…` → `Pause(sentence)`; `==x==` → `Token(emphasis=strong)`. Inline `` `code` `` → `Token(emphasis=code)`.

**Before** `## Risk\nThe auth change ==widens== scope:\n\n```py\nreturn trust(c)\n```` → **after**
`[Prose(heading,[Risk]), Prose(body,[…,widens@strong,…,scope]), Pause(clause), Pause(block_ahead),
Block(code,py,lead="…scope:",content="return trust(c)")]`. Golden-vector tests pin the parse
(centrepiece — a wrong parser poisons every surface).

## (c) SQLite store — schema + adapter

Four concepts, **three tables** (provenance rides inline on `digests`, 1:1, immutable — its own table
waits for multi-hop lineage, rule of three; images-as-files wait until images arrive). Migration
`0002_digests.sql` on the existing forward-only/`user_version` runner; `schema.sql` anchor updated.

```sql
CREATE TABLE digests (
  id TEXT PRIMARY KEY, slug TEXT NOT NULL UNIQUE, name TEXT NOT NULL,
  prov_source_kind TEXT NOT NULL, prov_origin TEXT, prov_producer TEXT,
  prov_ingested_via TEXT NOT NULL, prov_enriched INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL, token_count INTEGER NOT NULL, est_reading_ms INTEGER NOT NULL,
  content_sha TEXT NOT NULL, ir_version INTEGER NOT NULL DEFAULT 1,
  owner_id TEXT NOT NULL DEFAULT 'local', reading_hint TEXT,
  segments TEXT NOT NULL);              -- IR JSON: model_dump_json(segments); one round-trip
CREATE INDEX digests_created_at ON digests(created_at);
CREATE TABLE preferences (owner_id TEXT PRIMARY KEY, prefs TEXT NOT NULL);   -- Preferences JSON
CREATE TABLE history (   -- scaffolded now, wired Phase 2 (resume + settings-used)
  id TEXT PRIMARY KEY, digest_id TEXT NOT NULL REFERENCES digests(id),
  owner_id TEXT NOT NULL DEFAULT 'local', started_at TEXT NOT NULL,
  segment_index INTEGER NOT NULL DEFAULT 0, token_offset INTEGER NOT NULL DEFAULT 0,
  completed_at TEXT, settings_snapshot TEXT);
```

`DigestStore(ABC)` port (`core/ports/digest_store.py`): `add(digest)` (→`DuplicateSlugError`),
`get_by_slug(slug)` (→`UnknownDigestError`), `list_meta()` (newest-first `DigestMeta`),
`get_preferences(owner_id)`, `put_preferences(prefs)`. `SqliteDigestStore` adapter serialises via
`model_dump_json`/`model_validate_json`. DB lives in the **OS app-data dir** (`Settings.data_dir`,
`GLYDE_DB_PATH` override). Verified-fake `InMemoryDigestStore` + shared `digest_store_contract.py`.

## (d) Memorable two-word slug (`api/slug.py`, beside `ids.new_id`)

`new_slug(is_taken: Callable[[str], bool], *, rng: random.Random | None = None, k: int = 8) -> str`.
Two curated public-domain word pools (~200×200 ≈ 40k pairs) shipped as a packaged asset
(`importlib.resources.files("glyde.api")/"wordbank"/{left,right}.txt`, like migrations). Picks
`f"{a}-{b}"`; on `is_taken` retries up to `k`, then appends `-N` (suffix-on-collision). Minted at the
**api layer** (purity gate forbids `random`/`uuid` inward; `random.Random` is api-side). Slug is the
**secondary UNIQUE key, 1:1 with `id`**; FKs point at `id`; `/d/{slug}` resolves slug→digest, so a
regenerated slug never touches relations.

## (e) API surface — `api → adapters → core`, bare paths (proxied under `/api`)

`POST /digests` ← `CreateDigestRequest{ name, text: str | None, segments: list[Segment] | None,
source_kind, origin?, producer?, tags?, enrich: bool=False }` → **201** `DigestView` (full IR).
`GET /digests` → `list[DigestListItemView]` (meta + `counts{words, blocks_by_kind}`, newest-first).
`GET /digests/{slug}` → `DigestView` | 404. `GET /preferences?owner_id=local` & `PUT /preferences`
→ `PreferencesView`. Every route carries `summary`/`description` (agents read the schema). Errors map
via the one app-level `StoreError`→`{code,message}` handler (`unknown_digest`→404, `duplicate_slug`→409).

`compose_digest(...)` (`api/compose.py`) is the **one composition function CLI and route share**:
parse `text`→segments (else use `segments`); mint `id` (`new_id`), `slug` (`new_slug(is_taken=store
closure)`), stamp `created_at` (`canonical_now`); derive `token_count`, `est_reading_ms`
(`token_count/wpm*60000`), `content_sha` (sha256 of canonical source); `store.add`. The enrich hook is
an **injected callable defaulting to `None`** (§i). MCP (Phase 2) is a thin wrapper over this same call.

## (f) CLI handoff (`api/cli.py`, thin — composition stays in the api layer)

`glyde add [TEXT]`: resolves source — existing path → file (`source_kind=file`); else stdin not a tty →
pipe (`source_kind=pipe`); else literal arg → cli. Flags `--name --tag --source-kind --enrich
--open/--no-open`. Calls `compose_digest` **in-process** via `open_store` (no running server needed),
prints `name`, `slug`, and the LAN reader URL `http://{lan_host}:{port}/d/{slug}`. `glyde list` prints
the library. Errors plain-echoed + `typer.Exit(2)` (never rich — CI-width-safe). `serve`/`export-openapi` kept.

## (g) SvelteKit reader — full port (mobile-first, typed seam)

Routes `fe/routes/+page.svelte` (library), `fe/routes/d/[slug]/+page.{ts,svelte}` (reader),
`fe/routes/settings/+page.svelte`. Reader `load` fetches `GET /api/digests/{slug}` through the
openapi-fetch client (`{data,error}` branch). Element boundaries: domain logic in
`fe/lib/domains/{reader,library,preferences}`, presentational in `fe/lib/components/ui` (Svelte-5 runes,
`$derived` for pure pacing, `$effect` only for DOM/measure). **Pacing engine** (`domains/reader/engine.svelte.ts`):
consumes IR `Token`/`Pause`/`Block` (not a flat string), computes pivot + `dwell_ms = base × Π(mult)`
client-side from `Preferences` (the *how* the IR deliberately omits). **All three modes** — RSVP
(ORP measure-and-translate, red pivot, context above/below), Guided sweep, Fading trail; **default
guided**, last-used `mode` persisted to `Preferences`. **Full spec-001 blocks:** `Pause(block_ahead)`
shows the accent "code ahead" chip during the last prose words; on `Block` the stream auto-pauses and a
static full-width card renders per kind — code (syntax-highlighted, mobile horizontal-scroll + wrap
toggle), table grid (wide → stacked `header: value`), image/diagram card (alt fallback), math
(`linear_form` aside), quote, note; Space/tap resumes, `Left` re-shows last card. **Mobile-first:**
tap-stage = play/pause, bottom transport bar, edge speed rail, hairline progress with block notches +
time-remaining, chrome auto-hides during playback. **LAN serve:** `glyde serve --lan` binds the
**SvelteKit front door** (`adapter-node`, `HOST=0.0.0.0`), prints a QR + URL carrying a shared bearer
token (`token` → localStorage → `Authorization` header); `hooks.server.ts` asserts it on `/api`
mutations (closes the ADR-0003 CSRF gap). Phone is **read-only** in v1.

## (h) Preferences persistence

`Preferences` is the typed surface CLI/API/UI agree on, keyed by `owner_id="local"`. Server is source of
truth (`GET/PUT /preferences`); `domains/preferences/store.svelte.ts` mirrors to localStorage for
instant first paint + offline, reconciles on load, and writes through on every change — so the
**last-used mode is restored next open**.

## (i) Gated Haiku-enrich (STRETCH — `adapters/enrich.py`)

Isolated unit: `enrich(raw: str, *, api_key: str, client=None) -> str` (Glyde Markdown out, content
verbatim + in order, low temperature, **Anthropic Messages API** `client.messages.create`, a
Haiku-class model — verify exact id/params via the `claude-api` skill at impl). Sync (adapters-async
gate clean). **Key injected** via `Settings.anthropic_api_key` (`GLYDE_ANTHROPIC_API_KEY`) passed as an
argument — never read in `core`. `deps.get_enricher()` returns the callable only when a key is present,
else `None`; `compose_digest` calls it only when `enrich AND key AND no structure detected`, wrapped
`try/except → raw` (graceful fallback to deterministic parse). Mockable via the `client` param (the
`anthropic` SDK earns the one no-mock allowlist entry). Drops cleanly if the night runs short.

---

# Work-unit decomposition

**F0 lands first and alone** (the IR + seam + spine everyone imports); the 12 fan-out units are
file-disjoint and independently mergeable on top of it. Documented shared-file hand-offs: F0 declares the
**full `Settings` surface** (data_dir, lan_host, lan_token, anthropic_api_key) and `compose`'s
enrich/parse seams, so no two units edit `settings.py`/`compose.py`.

**Shared verify primitives** — *GATES-BE*: `uv sync && uv run ruff format --check . && uv run ruff check . && uv run ty check && uv run lint-imports && uv run pytest --cov`. *GATES-FE*: `cd frontend && npm run gen:api && npm run check:api-drift && npm run lint && npm run boundaries && npm run check && npm run typecheck && npm run test && npm run build`. *E2E-SEAM*: `uv run glyde serve` then `curl`. *E2E-READER*: `uv run glyde serve` + `cd frontend && npm run dev`, open `http://localhost:5173/...`, screenshot via the **run/verify skill**.

- **F0 — Digest IR + typed-seam spine.** owned: `core/models/*`, `core/parsing/*`, `core/ports/{digest_store,errors,__init__}.py`, `core/__init__.py`, `adapters/sqlite/{digest_store.py,schema.sql,migrations/0002_digests.sql,__init__.py}`, `api/{compose.py,slug.py,wordbank/*,settings.py,deps.py,app.py}`, `api/schemas/{digests.py,preferences.py,__init__.py}`, `api/routes/{digests.py,preferences.py,__init__.py}`, `docs/schemas/openapi.json`, `fe/lib/api/schema.d.ts`, `backend/tests/{core,adapters,api,support}/…(digest)`. summary: the IR + parser + slug + store + four routes + regenerated seam — handoff→store→typed read end to end (pre-segmented **and** parsed text). depends_on: —. verify: GATES-BE; `uv run glyde export-openapi && cd frontend && npm run check:api-drift`; E2E-SEAM `curl -X POST localhost:8000/digests -H 'content-type: application/json' -d '{"name":"t","text":"## H\n==big== news.\n\n```py\nx=1\n```"}'` → slug; `curl -s localhost:8000/digests/<slug> | jq .segments`, `curl -s localhost:8000/digests`, `curl -X PUT localhost:8000/preferences -d '{"owner_id":"local","mode":"rsvp"}'`.
- **R1 — Reader shell + pacing engine + route.** owned: `fe/lib/domains/reader/{engine.svelte.ts,Stage.svelte,index.ts}`, `fe/routes/d/[slug]/{+page.ts,+page.svelte}`. summary: IR-consuming timeline + pivot/dwell engine; mode/block slots. depends_on: F0, X1. verify: GATES-FE; vitest on `engine` (dwell/pivot golden numbers); E2E-READER `/d/<slug>` streams prose.
- **R2 — RSVP ORP mode.** owned: `fe/lib/domains/reader/modes/Rsvp.svelte`. summary: red-pivot measure-and-translate, context above/below. depends_on: F0, R1. verify: GATES-FE; E2E-READER screenshot pivot centred.
- **R3 — Guided + Fading modes.** owned: `fe/lib/domains/reader/modes/Flow.svelte`. summary: full-text flow, discrete jump (no teleprompter). depends_on: F0, R1. verify: GATES-FE; E2E-READER screenshot each mode.
- **R4 — Block cards (full spec-001).** owned: `fe/lib/domains/reader/blocks/*` (Code/Table/Image/Math/Quote/Note + BlockAheadCue). summary: auto-pause, static cards, highlight, grid, mobile fallbacks, re-show. depends_on: F0, R1. verify: GATES-FE; vitest table→stacked; E2E-READER screenshot code+table pause + cue + resume + `Left` re-show.
- **R5 — Transport + chrome + progress.** owned: `fe/lib/domains/reader/Transport.svelte`, `fe/lib/domains/reader/Progress.svelte`. summary: tap-stage play/pause, bottom bar, speed rail, notched progress, time-left, auto-hide. depends_on: F0, R1. verify: GATES-FE; E2E-READER screenshot mobile viewport (DevTools 390px).
- **L1 — Library home.** owned: `fe/lib/domains/library/*`, `fe/routes/+page.{ts,svelte}`. summary: newest-first feed, name + mono slug deep-link, provenance, shape badges. depends_on: F0, X1. verify: GATES-FE; E2E-READER `/` lists seeded digests, tap → `/d/<slug>`.
- **P1 — Settings + Preferences client.** owned: `fe/lib/domains/preferences/*`, `fe/routes/settings/+page.svelte`. summary: grouped controls, live preview, server-backed store + localStorage mirror, restores last-used mode. depends_on: F0, X1. verify: GATES-FE; E2E-READER change mode → reload → restored; `curl -s localhost:8000/preferences`.
- **B1 — CLI handoff.** owned: `api/cli.py`, `backend/tests/api/test_cli.py`. summary: `glyde add` (arg/stdin/file) + `glyde list`, in-process compose, prints slug + URL. depends_on: F0, B2. verify: GATES-BE; `echo "## R\ncode ahead:\n\n\`\`\`py\nx=1\n\`\`\`" | uv run glyde add --name P` prints slug; `uv run glyde add ./README.md`; `uv run glyde list`.
- **B2 — LAN serve + QR + token.** owned: `api/lan.py`, `api/routes/meta.py`(token-mint endpoint), `fe/hooks.server.ts`, `fe/lib/api/token.ts`. summary: `--lan` 0.0.0.0 bind + QR + shared bearer; hooks asserts token on mutations. depends_on: F0. verify: GATES-BE+FE; `uv run glyde serve --lan` prints QR+token; mutation without token → 401, with header → 201.
- **B3 — Haiku-enrich (STRETCH).** owned: `adapters/enrich.py`, `deps.py:get_enricher` body, `backend/tests/adapters/test_enrich.py`. summary: key-gated sync Anthropic structuring, graceful raw fallback. depends_on: F0. verify: GATES-BE (fake `client`); `printf 'a raw log line' | GLYDE_ANTHROPIC_API_KEY= uv run glyde add --enrich` → passthrough digest (no key → deterministic).
- **X1 — App shell + theme tokens + fonts.** owned: `fe/app.css`, `fe/app.html`, `fe/routes/+layout.svelte`, `fe/lib/components/ui/*`. summary: dark/light/sepia `@theme inline` tokens, Atkinson/Lexend, mobile-first base. depends_on: F0. verify: GATES-FE; E2E-READER screenshot three themes.
- **D1 — Glossary + ADRs + authoring guide.** owned: `docs/glossary.md`, `docs/decisions/0005-digest-ir.md`, `docs/decisions/0006-lan-token.md`, `docs/product/glyde-handoff-authoring.md`. summary: canonicalise Digest/Segment/slug, record the IR + pacing-split + LAN-token decisions, agent authoring rules. depends_on: F0. verify: `prek run --all-files`; links resolve.
