# Glyde v1 — open questions for the human

Decisions the panel **cannot** make for you, ordered by leverage. Each has options, a
recommended default (**bold**), and one line of why. Companion to `SCOPING.md`; the
panel-decided calls are listed at the bottom so you can override any of them.

The top four also went to your phone as taps — they are the ones that most change what gets
built tonight.

---

## High leverage — these change the overnight build

### 1. Default reader mode

The reader ships three modes (RSVP, Guided sweep, Fading trail; ADR 0004). Which is the
**default** the first-run user lands on?

- **Guided sweep** *(recommended)* — full text visible, a marker paces you; strongest measured
  evidence (~70% fewer reading errors), preserves parafoveal preview + regression, and **fails
  safe** (a first-run user can't get lost in a flashing stream). RSVP stays one keypress away.
- RSVP flash — the signature single-word ORP stream; lowest eye-movement, the mode the red pivot
  is built for; the dyslexia-skim instinct.
- Adaptive — pick the mode by content (short status → RSVP, long explanation → Guided); powerful
  but adds a decision surface v1 doesn't need.

_Why:_ this is a **lived-preference call** — evidence and fail-safe favour Guided, but **you are
the dyslexic primary user; your instinct overrides the literature.**

### 2. Block-pause in overnight v1

What does the reader do with code / tables on night one?

- **Minimal block-pause** *(recommended)* — code and tables **halt the stream and render
  statically**, a keypress resumes. No cue/re-show/grid polish yet.
- Prose-only — strip/flatten blocks (today's prototype behaviour); all block-pause is Phase 2.
- Full spec 001 — block-ahead cue, re-show-last, rendered grid, image/math cards, highlighting.

_Why:_ the #1 use-case (code-heavy PR digests) means **stripping code loses the content that
matters most**, but full polish blows the night — minimal is the thread.

### 3. Reader delivery

How is the reader served tonight?

- **Serve the modified prototype `reader.html`** *(recommended)* — inject the Digest IR; fastest
  path to a working loop. (Note: it still needs a real rewrite to consume `segments` instead of a
  flat string — "as-is" is a half-truth.)
- Port the reader into SvelteKit now — gets the typed seam + mobile-first layout immediately, but
  it is the night's biggest time-sink and risks the loop not closing.

_Why:_ the goal tonight is the **loop end-to-end**; the SvelteKit port is Phase 2 and the
injected-HTML reader gets there fastest.

### 4. Handoff surface

What is the v1 entry point for handing off?

- **CLI only** *(recommended)* — `glyde add` / pipe; the deterministic, testable spine. MCP is the
  immediate fast-follow.
- CLI + a thin MCP tool — adds the in-Claude-Code `glyde_handoff` tool now; truer to where your
  dogfood lives, but extra overnight surface over an API that must land first.

_Why:_ MCP is a thin wrapper over `POST /digests`; **ship the API + CLI solidly first**, add the
wrapper next — don't risk a half-working headline path overnight.

---

## Medium leverage — shape the contract or the parser

### 5. Haiku enrichment default

- **Opt-in (`--enrich`, default off)** *(recommended)* — keeps the headline path key-free,
  deterministic, local; raw markup-less input passes through as unstructured prose unless asked.
- Auto-enrich raw text — piped logs "just work" with structure, at the cost of an API-key
  dependency and nondeterminism in v1.

_Why:_ the "reading in seconds, local, deterministic" promise is poison to a model round-trip on
every handoff.

### 6. Syntax scope for v1

- **spec-001 blocks + `==highlight==`** *(recommended)* — `==highlight==` is one mark, maps to the
  `emphasis` token, and powers agent-flagged salience; cheap and high-value.
- spec-001 block set only — least to parse and teach; no prose-pacing layer.
- blocks + highlight + beat markers — also explicit author-forced pauses; more syntax to teach.

_Why:_ emphasis is already a first-class token property; surfacing it in the syntax is nearly free.

### 7. Frequency lexicon + clause-parser in v1

- **Defer** *(recommended)* — v1 paces on punctuation only (as the prototype does today); low-
  frequency / clause-boundary dwell lands as a fast-follow without changing the contract.
- Ship now — richer dwell from night one, at the cost of a lexicon asset + a parser pass overnight.

_Why:_ it's additive to the reader, not a contract change — defer it cleanly.

### 8. Letter-spacing default

- **Small positive (~0.04em)** *(recommended)* — spacing is the single best-evidenced dyslexia
  lever; the slider dials it back for skilled-reader speed.
- Zero — skilled-reader-neutral default; spacing is opt-in.

_Why:_ you are both dyslexic and a fluent reader; the evidence pulls toward a small positive
default with an easy escape.

### 9. Memorable-link uniqueness

- **Local-unique** *(recommended)* — the slug is `UNIQUE` in the local DB; enough for LAN sharing
  and the speakable handle.
- Globally-unique / shareable-off-device now — makes the slug a first-class shareable id, but pulls
  hosting and a global namespace forward into v1.

_Why:_ shareability is a named feature, but global uniqueness is a Later concern — don't pull
hosting forward.

### 10. Provenance richness

- **Permissive single-hop** *(recommended)* — `source_kind`, `origin` (path/url/repo@sha/run-id),
  `producer`, `ingested_via`; capture origin even when unused (free, hard to backfill later).
- Minimal label only — `source_kind` + time + agent label; less to capture, but enrichment later
  needs a re-handoff.
- Rich multi-hop lineage — promote provenance to its own table with a parent link now.

_Why:_ origin/producer are a one-way door — capture them permissively now; lineage waits for
digest-from-digest.

---

## Low leverage — taste / aesthetics (still yours to call)

### 11. Slug collision style

- **Suffix-on-collision (`pale-fire`)** *(recommended)* — reads like a phrase; suffix only after a
  clash. Collisions are vanishingly rare at N=1.
- Always-suffixed (`pale-fire-417`) — never collides, drops the retry logic, reads less like a phrase.

_Why:_ the phrase is the point; collisions are cheap to handle when they're rare.

### 12. Slug corpus flavour

- **Curated literary pairs** *(recommended)* — on-brand, public-domain (no licensing), two words
  stay thumb-able.
- Adjective-animal (MLflow style) — trivial and collision-cheap, less evocative.

_Why:_ the literary phrase is the brand; public-domain + two words removes the only real objections.

### 13. Authored reading hint on the digest

- **Optional hint, ignored by default** *(recommended)* — an agent may suggest "long, default to
  Guided"; the reader ignores it unless you opt in. Live settings stay per-user.
- None — the digest carries no reading metadata at all; settings are purely per-user preference.

_Why:_ honours the brief's "reading settings" mention without coupling content to preference (the
data architect's correct line).

---

## Panel-decided (flag if you disagree)

These the panel resolved with strong consensus; listed so nothing is hidden:

- **`Digest` replaces `Record`** as the canonical entity — formalise in the glossary + an ADR now,
  so every surface builds against it.
- **Tokenise at ingest** (not in the reader) — forced by emphasis being a per-token property.
- **Pacing split** — semantic signals (emphasis, pause reason+scale, token kind) in the IR; pivot
  index + flash-ms in the reader.
- **Phone is read-only over the LAN** in v1 — laptop agents produce, phone consumes; smallest
  attack surface.
- **`owner_id` + `ir_version` + `content_sha` baked into every table now** — cheap now, the
  migration-from-hell later.
- **`/d/{slug}` is a real navigable route**, not a cosmetic label.
- **Minimal library list in v1** (rich library — read-state, search, grouped feed — is Phase 2).
- **Shared bearer token is a guard, not authentication** — and we say so.
- **Segments stored as one serialised-IR JSON column**, not normalised segment rows (the reader
  always fetches a whole digest; no cross-digest segment query exists yet).
- **One SQLite DB in the OS app-data dir** (`GLYDE_DB_PATH` override), not the CWD.
