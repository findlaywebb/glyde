# Glyde v1 — consolidated scope

_Product lead synthesis of the five-person scoping panel
(`perspective-product.md`, `-accessibility.md`, `-agent-dx.md`, `-architecture.md`,
`-design.md`), reconciled against the repo grounding (`docs/architecture.md`,
`docs/glossary.md`, `docs/decisions/0003`–`0004`, `specs/001-block-pause/`, and the
`prototype/` reader). Decisions the human must make tonight live in
`open-questions.md`._

## What Glyde is

Your agents write a lot; Glyde lets you **read** it — fast, low-fatigue, and never lost.
It is the **digest layer for the agent-output firehose**, built for the one user who feels
that firehose worst: the **dyslexic software engineer who works with coding agents**. An
agent (or the CLI) hands off a wall of natural-language output and gets back a **named,
traceable, low-fatigue digest** with a speakable retrieval handle, kept in a personal
library. The dyslexia-tuned reader is the last mile; the product is the **handoff loop +
provenance + library** around it. v1 is N=1 dogfood: if the builder stops reading raw
agent output in the terminal, it works.

---

## The keystone: the Digest IR

Everything in Glyde is a projection of **one typed object**. The reading syntax **parses
into** it, SQLite **persists** it, the API **serves** it, the reader **renders** it, and the
CLI / API / MCP all **mint and return the same shape**. One Pydantic model graph in
`core`, persisted by `adapters`, projected once by `api`, flowed to the frontend through
the existing typed seam (`openapi.json` → `schema.d.ts`). **This is the DRY spine and the
whole reason to invest in the IR up front: get it right and every surface is thin; get it
wrong and we pay in every consumer.** It **replaces the template `Record`** as Glyde's
canonical entity (the glossary invites exactly this).

A **Digest** = metadata + an ordered list of typed **segments**.

```text
Digest
  meta: DigestMeta
  segments: list[Segment]            # the ordered reading timeline

DigestMeta
  id:                 str            # opaque, api-minted; the relation-stable key (FKs point here)
  slug:               str            # the memorable two-word link; UNIQUE; the human/agent handle
  name:               str            # agent-given semantic title ("Auth risk review")
  provenance:         Provenance     # 1:1, immutable, born with the digest
  created_at:         str            # canonical ISO-8601 UTC, api-stamped (the one clock site)
  token_count:        int            # derived once at ingest
  est_reading_time_s: int            # derived once at a baseline wpm
  content_sha:        str            # dedup + integrity
  ir_version:         int            # the shape evolves without a destructive migration
  owner_id:           str            # "local" sentinel in v1; hosted-ready from day one
  reading_hint:       ReadingHint | None   # OPTIONAL agent-authored default (see note below)

Provenance                          # the "what produced this, and how it got here"
  source_kind:  "agent" | "file" | "cli" | "paste" | "pipe" | "api"
  origin:       str | None          # path | url | repo@sha | agent-run-id | session
  producer:     str | None          # the producing agent / model label
  ingested_via: "cli" | "api" | "mcp"
  enriched:     bool                # did a structuring pass (Haiku) touch it

Segment  =  ProseSegment | Block | Pause      # discriminated union on `type`

  ProseSegment                      # the streamed body
    type:   "prose"
    role:   "heading" | "body" | "list_item"   # knowing where you are fights fatigue
    tokens: list[Token]

  Block                             # the pause-and-show family; a single stop in the timeline
    type:       "block"
    block_kind: "code" | "table" | "image" | "quote" | "math" | "note"
    content:    str                 # raw block content — NEVER streamed word-by-word
    lang:       str | None          # code language
    lead:       str | None          # the prose runway sentence it follows
    alt:        str | None          # image/diagram/figure alt text
    linear_form: str | None         # spoken form for promoted math ("x squared plus one")

  Pause                             # a felt beat (the brief's "pause with duration + reason")
    type:           "pause"
    reason:         "clause" | "sentence" | "paragraph" | "block_ahead"
    duration_scale: float           # coarse beat weight; the reader maps reason+scale → ms

Token                               # the streaming atom
  text:     str
  kind:     "word" | "punct"
  emphasis: "none" | "strong" | "em" | "code"   # agent-authored salience
  hold:     float | None            # OPTIONAL coarse agent dwell hint (not milliseconds)
```

`image` covers diagrams and figures (the `![alt](src)` card); it is the canonical name
because it matches the markdown token. The block set deliberately spans the brief's
code/table/diagram/quote plus spec 001's `math`/`note`.

### What is deliberately OUT of the IR (the reconciled line)

The panel's accessibility specialist wanted full pacing baked into the IR; the data
architect wanted it kept out. **The reconciliation: semantic signals live in the IR; render
math lives in the reader.**

- **IN (the *what*)**: token `kind` + `emphasis`, explicit `Pause` segments with
  `reason` + coarse `duration_scale`, an optional agent `hold` hint, block typing. These are
  signals a client cannot cheaply re-derive and that let an **agent override pacing
  semantically** (flag the key result, force a beat).
- **OUT (the *how*)**: the **ORP pivot index** (a font-glyph measurement),
  **per-word flash milliseconds** and **pixel offsets** (functions of the user's wpm / font /
  mode), and **per-full-stop micro-pauses** (reader-derived from punctuation). Baking these in
  freezes them against settings changes and couples `core` to reading-science constants that
  belong in the reader. The reader computes pivot + dwell-ms from `Token` + user settings + the
  science constants (the dwell multipliers and pause weights in `perspective-accessibility.md`).

**Reading settings are NOT digest content.** A digest is content; wpm / mode / theme are
per-user **preference**, and one digest is later read by many users at different settings.
The settings *used for a given read* belong on the reading session (history). The digest may
carry at most an **optional `reading_hint`** (an agent suggesting "this is a long
explanation, default to Guided") — ignored unless the reader opts in. This honours the
brief's mention of reading settings without coupling content to preference.

The IR taxonomy spans several files under `core/models/` (one concept per file —
`digest.py`, `segment.py`, `provenance.py`, `token.py`), never one giant `models.py`, per the
400-line budget.

---

## The reading syntax (Glyde Markdown)

The human/agent-authorable surface that maps onto the Digest IR is **Glyde Markdown**: a
CommonMark subset plus the block markers from spec 001 (fenced code, pipe tables,
`![alt](src)` images, `:::pause:::` notes) plus a **thin prose-pacing layer** — `==highlight==`
for an emphasised, held token. Agents emit it **directly** (Claude is already excellent at
markdown and *knows* which line is code and which sentence is the decision); a structuring
model is never on the headline path. **One syntax, one parser, one IR, many producers.**

The **syntax → IR parser is the only ingest path**: pure, deterministic, living in `core`
(text in, typed segments out). The prototype's `launch.py` segmentation is its embryo; it
graduates into the core parser and every channel ingests through it.

**Before** (Glyde Markdown the agent emits):

```markdown
## Risk review

The auth change ==widens== the token scope. The handler now trusts the upstream claim:

```py
def authorize(claim):
    return trust(claim.scope)  # second check removed
```

That change is the risk.
```

**After** (the parsed Digest IR, abbreviated):

```text
Digest(meta={name:"Auth risk review", slug:"pale-fire", provenance:{source_kind:"agent", producer:"claude-code", ingested_via:"cli"}, ...},
  segments=[
    Prose(role=heading, tokens=[{text:"Risk"}, {text:"review"}]),
    Prose(role=body,    tokens=[..., {text:"widens", emphasis:"strong"}, ..., {text:"claim", kind:"word"}, {text:":", kind:"punct"}]),
    Pause(reason="block_ahead"),
    Block(block_kind="code", lang="py",
          lead="The handler now trusts the upstream claim:",
          content="def authorize(claim):\n    return trust(claim.scope)  # second check removed"),
    Prose(role=body,    tokens=[{text:"That"}, {text:"change"}, ...]),
  ])
```

The reader streams the prose tokens, holds the `==widens==` token, shows a "code ahead" cue
during the last words before the `Pause`, then halts and renders the code **statically** for
non-linear reading, and resumes on a keypress.

---

## v1 scope (overnight build) — ordered

The novelty is **handoff → store → read**, end to end, on the one IR. Build in dependency
order; **the parser and the reader-rewire are the two test-first centrepieces** (a wrong
parser poisons every surface; "serve the prototype" hides a real reader change).

1. **The Digest IR** — `Digest` / `DigestMeta` / `Provenance` / `Segment` / `Token` in
   `core/models/`, replacing `Record`. Frozen, `extra="forbid"`, `ir_version`, `content_sha`.
   Formalise in the glossary and an ADR so every surface builds against it.
2. **The syntax → IR parser** (`core`, pure, deterministic) — Glyde Markdown → segments
   (prose tokens + emphasis + typed blocks + pauses). The only ingest path. Golden-vector tests.
3. **`DigestStore` port + SQLite adapter** — `digests` table (`id` PK, `slug` UNIQUE, `name`,
   inline provenance columns, `created_at`, counts, `content_sha`, `ir_version`, `owner_id`,
   and `segments` as a serialised-IR JSON column — one round-trip, no segment-row joins).
   Forward migration + `schema.sql` anchor. Stored in the OS app-data dir (see Cross-cutting).
4. **Memorable-slug generator** (api layer) — `new_slug(is_taken)` over the offline word-bank;
   suffix-on-collision. (Scheme below.)
5. **API surface** — `POST /digests` (Glyde Markdown **or** pre-segmented + metadata → stored
   Digest + slug), `GET /digests/{slug}` (the typed IR the reader renders), `GET /digests`
   (the library-list projection: name · slug · provenance · counts). Every route OpenAPI-
   documented (agents discover it without docs). Re-export `openapi.json`; regenerate `schema.d.ts`.
6. **CLI handoff** (the v1 headline) — `glyde add <file>` / `glyde "<text>"` / `cat x | glyde`
   → calls the **same compose function the API uses** → prints `name`, `slug`, and the LAN URL.
   Flags: `--name`, `--tag`, `--source-kind`, `--open/--no-open`. Plus `glyde list`.
7. **Serve the reader** — `GET /d/{slug}` serves the prototype `reader.html` with the Digest
   IR **injected** (not rebuilt in SvelteKit overnight). The reader is **rewired to consume the
   injected IR `segments`** (today it paces a flat string client-side) and given **minimal
   block-pause**: code and tables halt the stream and render statically, a keypress resumes.
8. **Preferences** — a typed `Preferences` object (wpm, mode, context, sizes, font, theme,
   ramp), keyed by `owner_id`. localStorage night one; the server-side table scaffolded.
9. **LAN-to-mobile** — `glyde serve --lan` binds the **SvelteKit front door** (not FastAPI) to
   `0.0.0.0`, prints the LAN URL **plus a QR code**, mints a **shared bearer token** carried in
   the QR URL → localStorage → header; `handle()` asserts it on mutations (closes the ADR-0003
   CSRF gap). Phone is **read-only** in v1.
10. **Minimal library** — `glyde list` + a minimal served index (newest-first: name · slug ·
    provenance · shape counts → tap to read). The personal library is a core value prop, and it
    is nearly free once digests persist and the list route exists.

### Phase 2 — agent-native + mobile

- **MCP server** — a *thin wrapper over `POST /digests`*, not a parallel implementation:
  `glyde_handoff(text|path, name, tags, source_kind) → slug` + `glyde_read(slug)`. The tool
  description is the teaching surface.
- **Haiku enrichment** (`--enrich`, opt-in, default off) — structures **raw, markup-less** input
  into the *same* Glyde Markdown; content preserved verbatim and in order, low temperature, fails
  safe to raw-prose passthrough.
- **Full block-pause polish** (spec 001) — block-ahead cue refinement, re-show-last-block,
  rendered table grid, image/diagram/figure cards, math, syntax highlighting; wide-block mobile
  fallback (stacked `header: value`).
- **Reader ported into the SvelteKit typed seam** — off the injected-HTML crutch; thumb-first
  mobile transport (tap-stage = play/pause, bottom transport bar, edge speed rail).
- **Rich Library** — read-state (unread / in-progress / done), resume bars, shape badges,
  search/filter, grouped-by-day feed.
- **Reading history / sessions** table — resume-on-phone; where "settings used" lives.
- **Frequency lexicon + light clause-parser** — richer dwell (low-frequency / clause-boundary)
  if deferred from v1.
- **Agent `glyde-handoff` skill + prompt library** — *when* and *how* to author a good digest.

### Later — hosted, multi-user

Accounts / OAuth / API keys; cross-user sharing + team libraries + ACLs; **globally-unique,
shareable-off-device links**; synced reading-preference profiles; opt-in reading analytics;
the public API + distributed prompt library; multi-device sync (local→hosted is a CRDT-shaped
problem, explicitly out); per-row encryption.

---

## The memorable-link scheme

Glyde's literary take on MLflow's adjective-animal: a **two-word `evocative-evocative` slug**
(`pale-fire`, `salt-marsh`, `hollow-lantern`). Two words, not three — shorter is more
memorable to say and thumb, which is the low-fatigue north star, and resolves the panel's
"too long on mobile" worry. It is the **speakable, shareable retrieval key**: *"did you read
pale-fire?"* is easier for a dyslexic user to recall and say aloud than `digest #4471`.

- **Corpus** — a **curated word-bank drawn from public-domain novels** (Project Gutenberg),
  shipped as a **packaged offline asset** (`importlib.resources`, like the migrations). Public
  domain dodges the licensing question; curation dodges the classic unfortunate-pairing /
  profanity gotcha. Two pools of words → pairs. **Overnight: ship ~200 × 200 ≈ 40k pairs**
  (ample at N=1), expandable to ~1k × 1k ≈ 1M later — do **not** hand-audit a million pairs tonight.
- **Minted at the api layer**, beside `ids.new_id` (the purity test forbids `random` inward).
  `new_slug(is_taken)` takes an **injected collision-check**, retries on the `UNIQUE` clash, and
  appends a short numeric suffix (`pale-fire-2`) only after K misses.
- **Mapping** — the slug is a stable **secondary** key, 1:1 with `id`. FKs point at `id`
  (opaque, relation-stable); the route `/d/pale-fire` resolves slug → digest. Regenerating a slug
  (import collision, profanity strike) leaves the `id` and every relation untouched. The slug is a
  **real navigable route** in v1, not a cosmetic label.

---

## Cross-cutting

- **Local-first storage** — one SQLite DB in the **OS app-data dir**
  (`~/Library/Application Support/glyde/` on macOS, XDG on Linux), overridable via
  `GLYDE_DB_PATH` — not today's CWD `glyde.db`. Holds the DB + WAL/SHM + backups + cached block
  images; the word-bank ships in the package. Block images land as **content-addressed files**
  (DB holds hash/path), never BLOBs — and only once images actually arrive (rule of three).
- **LAN-to-mobile serving** — FastAPI stays on localhost behind the SvelteKit proxy, never
  exposed. `glyde serve --lan` binds the **front door** to `0.0.0.0` + QR + shared bearer token.
  The token is a **guard, not authentication** — it stops the curious roommate, not an attacker on
  a hostile network, and we say so. The mobile mutating surface is small (phone is a reader).
- **Preferences persistence** — the typed `Preferences` object off localStorage and into the
  typed surface so CLI / API / UI agree; keyed by `owner_id`. Server-side table scaffolded v1,
  fully wired when hosted.
- **Provenance & history** — `Provenance` is 1:1 inline with the digest, immutable, **single-hop**
  ("where did this come from"), born at ingest. Multi-hop lineage (digest-from-digest) promotes it
  to its own table later. The **history / reading-sessions** table (resume + settings-used) is
  scaffolded now, wired in Phase 2.
- **Hosted-ready insurance, baked now** (cheap now, the migration-from-hell later): `owner_id`
  on every table (defaulting to a `"local"` sentinel), `ir_version`, and `content_sha`. The typed
  IR itself — one model, all channels — *is* the hosted-ready move.

---

## Risks / over-reach (the skeptic's pass)

1. **The IR is the whole bet, and it is a lot for one night.** Four model files + a
   deterministic parser + store + slug + three routes + CLI + a reader rewire + LAN/QR. Each
   piece is small; the **integration** is the risk, and a wrong parser is inherited by every
   surface. Mitigation: the parser is the **test-first centrepiece** (golden vectors); everything
   else is a thin projection of it.
2. **"Serve the prototype as-is" is a half-truth.** `reader.html` paces a **flat string**
   client-side; consuming the server IR (`segments`) is a real reader rewrite, plus minimal
   block-pause. This is the **likeliest overnight slip**. Mitigation: make IR-consumption +
   code/table pause the second test-first centrepiece; **fallback** = inject flattened prose
   (lose blocks, keep the loop) if the night runs short.
3. **Block-pause polish creep.** Spec 001 is rich (cue, re-show, grid, images, math,
   highlighting). All of it overnight blows the night. Ship **code + table static pause only**;
   defer the rest. But note: the #1 use-case (code-heavy PR digests) means **stripping blocks —
   today's prototype behaviour — loses the content that matters most**, so *some* block-pause is
   close to non-negotiable. (This is the sharpest open question.)
4. **Library scope creep.** Read-state / resume / search / grouped feed is a Phase-2 app.
   Overnight = a **list**. Do not build a SvelteKit library route the same night you are serving
   injected HTML for the reader — it doubles the surface and contradicts "don't rebuild in
   SvelteKit overnight."
5. **MCP temptation.** The builder lives inside Claude Code, so MCP feels like the truer entry
   point — but it is a thin wrapper over an API that must land first. Building it before the API +
   CLI are solid risks a half-working headline path. Hold to Phase 2 unless the API lands with
   hours to spare.
6. **Slug curation is a time sink.** Auditing large word pools for unfortunate pairings is
   fiddly. Ship a **small hand-curated bank + suffix** tonight; expand later.
7. **Don't let the IR freeze the reader's render-time freedoms.** If `pivot_index` / flash-ms
   leak into the IR, a settings change can't re-pace stored digests. Keep them out.
8. **Provenance under-capture is a one-way door.** If `origin` / `producer` aren't captured at
   ingest you can't enrich later without re-handing-off. Capture a **permissive** `origin: str |
   None` + `producer` now even if unused — it's free.
9. **Pacing fork drift.** If the IR-vs-reader pacing split is left implicit, two surfaces will
   compute pacing differently and drift. Resolve it before building (the reconciled line above).
10. **Reader-mode default is a lived-preference call, not an evidence call.** The literature
    favours Guided sweep; the primary user's body may favour the RSVP flash. Don't let the panel's
    evidence overrule the dyslexic user's instinct — confirm it (see `open-questions.md`).
