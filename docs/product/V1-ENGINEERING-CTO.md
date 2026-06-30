# Glyde v1 — Engineering feasibility, sequencing & risk (CTO / VP Eng)

_Companion to `SCOPING.md`. The product panel's "safe" overnight cut was serve-the-prototype
+ minimal blocks + CLI. The locked scope overrides two of those on the biggest levers —
**full spec-001 blocks** and a **SvelteKit reader port** — plus a Haiku stretch. That is
genuinely aggressive for one night; it roughly triples the frontend surface the panel costed.
It is **achievable-but-tight**, and only because three things hold: the prototype is a proven
reader to **port, not invent**; the IR is unusually well-specified already (low
contract-discovery risk); and we fan out heavy parallel worktrees against a **frozen seam**.
If the night slips, it slips on the SvelteKit reader — so we sequence to protect it._

## The chokepoint is a *double* chokepoint

Everyone names the **Digest IR** as the foundation: correct. The non-obvious second one is the
**typed seam** (`openapi.json → schema.d.ts`). The SvelteKit reader is simultaneously the
**longest pole and the most downstream task** — it cannot start in earnest until the IR is
modelled, projected into API response schemas, exported, and `gen:api`'d.

**The move that makes the night feasible:** in Phase 0, freeze the IR *and* publish the
OpenAPI projection against **stub routes** that round-trip a hand-built `Digest`. The seam goes
real before the parser/store are correct, so the frontend generates types and starts building
in parallel with the still-incomplete backend.

## Build sequence: foundation → fan-out → integrate

**Phase 0 — serial, one focused context (the keystone).** Plan-reviewer gate first (ADR-0001).
Land `core/models/{digest,segment,provenance,token}.py` (frozen, `extra="forbid"`,
`ir_version`, `content_sha`), pure derivation helpers (token_count, sha — `core` mints no
id/clock/random), `api/schemas/digests.py` projection, stub `POST/GET/list`, `export-openapi`,
`gen:api`. Update the glossary + add the IR ADR (Digest replaces Record). **Exit gate: seam
green both sides. Nothing forks until this is frozen.**

**Phase 1 — fan-out, disjoint worktrees against the frozen seam:**

| Worktree | Owns (disjoint files) |
|---|---|
| A · Parser | `core/parse/*` — Glyde Markdown → segments; pure; golden-vector + hypothesis tests |
| B · Store | `adapters/sqlite/digest_store.py` + migration + `schema.sql` + `DigestStore` port + contract suite |
| C · CLI+routes | `api/slug.py` + word-bank asset + `cli.py` (add/list) + real `routes/digests.py` + the shared compose fn |
| D · Reader engine | `frontend src/lib/reader/*` + `routes/d/[slug]/` — 3 modes, measure-and-translate, persist last-used mode |
| E · Block cards | `frontend src/lib/reader/blocks/*` — code/table/image/math/note cards, cue, re-show, highlighting |
| F · Shell+library+LAN | shared tokens/layout/api-client/`hooks.server`, `routes/+page` library, `serve --lan`, QR, bearer token, prefs |
| G · Haiku (stretch) | `adapters/enrich/*` — isolated, mockable, key-gated, deterministic fallback |

**Disjoint-ownership rules.** `core/models/*` is frozen after Phase 0 — no fan-out agent edits
it. F solely owns the shared frontend shell (tokens, `+layout`, api client, `hooks.server`);
D/E/F never co-edit a file. The one high-coupling seam — the reader page composing block
cards — gets a **typed prop contract declared in Phase 0**, so D and E integrate without
touching each other's files.

**Phase 2 — serial integrate.** Wire C's routes to the real parser+store; re-run the seam
(shape must not have moved); compose D+E into the reader page; fold in F. Full gate stack, then
an end-to-end smoke: `glyde add` → slug → open `/d/{slug}` → reads with blocks, default
Guided, last-used mode restored.

## Definition of done

- **Backend green:** `uv run ruff check .` · `uv run ty check` · `uv run lint-imports` ·
  `uv run pytest` (architecture tests pass; `core` 100% branch) · `prek run --all-files`.
- **Frontend green:** `npm run lint` · `check` (svelte-check, zero a11y) · `typecheck` ·
  `test` · `boundaries` · `check:api-drift` · `build`.
- **Seam:** `openapi.json` committed, `schema.d.ts` regenerated, both drift gates green.
- **End-to-end, per feature:** CLI add (text arg / stdin / file) prints name+slug+URL;
  `glyde list`; `/d/{slug}` renders the IR with all three modes + the block-card slice;
  default = Guided; last-used mode restored next open; `serve --lan` binds the front door with
  QR + token-gated mutations (phone read-only).

## Top 5 risks → mitigation

1. **The SvelteKit reader is the longest pole and most downstream.** → Freeze IR + OpenAPI in
   Phase 0 against stub routes; the frontend starts immediately; port the proven prototype
   (440 lines of working reader logic), don't reinvent.
2. **Full spec-001 blocks is rich, genuinely new UI.** → Ship the must-land slice (static
   code/table/image/note cards + block-ahead cue + re-show + Space-resume + a static math card)
   as disjoint components; **syntax-highlighting quality and ClearSpeak math linearisation are
   spec-001's own out-of-scope line** — that is the natural trim, not the feature.
3. **Contract drift mid-flight** (a producer/consumer needs a new IR field) ripples to every
   worktree and regenerates the seam. → Over-specify the IR in Phase 0 (the spec is unusually
   complete); any post-freeze change is an explicit **serial re-freeze**, never an ad-hoc field
   add in a leaf.
4. **Parallel frontend agents collide on the shared shell.** → F solely owns
   tokens/layout/client/hooks; D/E/F pre-declare file ownership; reader↔cards meet only at a
   typed prop contract.
5. **Haiku pulls a network/key dependency into a deterministic, gate-driven build.** → Last
   unit, fully isolated adapter, mockable, key-gated (key injected via adapter, never read in
   `core`), fallback to deterministic passthrough; **NO-GO the instant it isn't green or
   threatens integration.**

## Go / no-go per v1 item

| Item | Call | Tier |
|---|---|---|
| Digest IR foundation | **GO** | Keystone — serial, first |
| Syntax→IR parser | **GO** | Must — test-first centrepiece |
| DigestStore + SQLite | **GO** | Must |
| Slug + word-bank (~200×200, suffix-on-collision) | **GO** | Must |
| API POST/GET/list + OpenAPI + seam | **GO** | Must |
| CLI handoff add/list (text / stdin / file) | **GO** | Must — the headline |
| SvelteKit reader, 3 modes, default Guided, persist last mode | **GO** | Must — longest pole, primary risk |
| Full spec-001 blocks | **GO (slice)** | Must-slice; highlight/ClearSpeak polish is the relief valve |
| Preferences (localStorage + scaffolded table) | **GO** | Must |
| Library list | **GO** | Must — near-free once digests persist |
| LAN serve + QR + bearer token | **GO** | Must, lowest priority; degrade to localhost if tight |
| Haiku enrich | **CONDITIONAL** | Stretch — isolated, **cut first** |

**Bottom line:** GO on the locked scope, with the block-polish layer and the LAN niceties as
the relief valves and Haiku as the first thing overboard. The night turns on one decision —
**freeze the IR and the seam before anyone forks.** Protect that and the loop closes; miss it
and the SvelteKit reader is what doesn't ship.
