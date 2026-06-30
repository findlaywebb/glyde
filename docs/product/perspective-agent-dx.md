# Perspective: Agent developer-experience

_Role: Agent DX specialist. How agents and the CLI feed Glyde, and the one typed digest they all produce._

The promise: an agent finishes a wall of analysis, runs **one command**, and the dyslexic
developer is reading it in the low-fatigue reader on their phone **seconds later**. Everything
below protects that sentence.

## The one decision: direct-emit first, Haiku as fallback

The reading syntax is a **small Markdown superset agents emit directly** (call it **Glyde
Markdown**). Haiku is **not** in the headline path. This is the right call because:

- Claude is already excellent at markdown, and the producing agent *knows* what it wrote —
  which lines are code, which sentence is the decision, what must not be streamed. A second
  model re-deriving that from flat text is redundant and lossy.
- The headline path must be **deterministic, zero-latency, and local-first**. A Haiku
  round-trip on every handoff adds seconds, a cost, an API key, and nondeterminism — poison
  for a gate-driven, contract-first project and for the "reading in seconds" promise.
- Spec 001 already commits to markdown as the authoring contract (fenced code, tables, images,
  `:::pause:::`). Direct-emit is DRY with a decision the project has made.

**When Haiku runs:** only when input arrives as **raw, unstructured text with no markup signal**
(a piped log, a plain `.txt`, a non-Glyde-aware producer) **and** enrichment is explicitly
requested (`--enrich`). Default **off**. The rule is crisp: **structure present → passthrough;
structure absent AND enrichment asked → Haiku annotate.** Haiku emits the *same* Glyde Markdown
an agent would — it is just one more producer of the syntax, never a privileged one.

## One syntax, one digest, many producers

This is the house principle made concrete. **Glyde Markdown** (the wire/authoring surface)
parses to a **Digest** (the typed structure). CLI, HTTP, MCP, Haiku and the UI all speak these
two things and nothing else. One parser. One contract.

- **Glyde Markdown** = CommonMark subset + the block markers from spec 001 (`code` / `table` /
  `image` / `:::pause:::` note), plus a thin prose-pacing layer (`==highlight==` → a held,
  emphasised pivot). The block set is already designed; I would keep the prose-pacing additions
  minimal in v1.
- **Digest** (the typed digest the brief calls for) wraps the spec-001 segment list with the
  handoff metadata:

```
Digest:   id · name · link · created_at · source · segments[] · tags[]
Segment:  {type:"prose", text} | {type:"block", kind, content, lang?}   # spec 001, reused verbatim
Provenance(source): kind("agent"|"cli"|"file"|"pipe"|"api") · origin(path|url|repo@sha|session) · producer · enriched(bool)
```

- **Parsing is pure and deterministic** (a domain concern — it belongs in `core`, reused by
  every surface). **Enrichment is a model call at the edge** (an adapter; never in `core`). The
  hexagonal boundary already tells us where each lives.
- `id` minted and `created_at` stamped server-side (per `backend/CLAUDE.md`). Digests are
  **immutable**; re-handing-off the same source mints a new one with lineage in `origin`, never
  an overwrite.

**The memorable link** is the magic handle. Agent supplies a human `name` ("Auth risk review");
Glyde generates a short evocative `link` (`pale-fire`, `quiet-leviathan`) — the LAN URL path
(`glyde.local/r/pale-fire`) and the thing the dev taps or thumbs on their phone. Short and
typeable matters more than clever.

## The ingestion surfaces

- **CLI (v1 headline).** `glyde "<text>"`, `cat notes.md | glyde`, `glyde ./review.md`. Flags:
  `--name`, `--tag`, `--enrich`, `--source-kind`, `--open/--no-open`. Thin surface: it parses
  options and calls the **same compose function the API uses** (per `backend/CLAUDE.md`), prints
  the link, exits with a code.
- **HTTP API.** `POST /digests` (raw Glyde Markdown **or** pre-segmented, plus metadata) →
  stored Digest + link. `GET /digests/{link}` feeds the reader through the typed seam. Agents
  POST direct to the bare path; every route OpenAPI-documented so agents discover it without docs.
- **MCP server (Phase 2).** A thin wrapper over `POST /digests` — **not** a parallel
  implementation. One tool, `glyde_handoff(text|path, name, tags, source_kind) → link`, plus
  `glyde_read(link)`. The tool description *is* the teaching surface.

## The Haiku transform: a structuring pass, never a rewrite

- **Input:** raw text + optional `source_kind` hint.
- **Output:** Glyde Markdown — the one syntax.
- **Guarantees:** (1) **content is preserved verbatim and in order** — Haiku only *inserts*
  structure (fence detected code, mark tables, wrap non-prose in `:::pause:::`, `==highlight==`
  key terms, paragraph breaks for pacing); it never paraphrases. This faithfulness is
  non-negotiable for a provenance tool. (2) Low temperature. (3) **Fails safe:** on
  error/timeout, fall back to raw-prose passthrough — the digest still reads, just unstructured.

## The agent skill + prompt library

- **`glyde-handoff` skill** (installed into agent environments): *when* to hand off (you have
  produced a large NL digest a human must read), *how* to write it (the spec-001 authoring
  rules — lead into a block with a prose sentence, summarise long code then show it, one idea per
  pause, `==highlight==` the decision), and the *one command* to run.
- **Prompt library:** reusable system-prompt fragments ("Write your answer as a Glyde digest:
  lead-ins before code, highlight the decisions, pause anything 2-D, keep prose skimmable") so
  any agent setup produces good digests without bespoke wiring.

## The headline path (what we optimise)

```
agent finishes  →  glyde "## Risk review  The auth change ==widens== the token scope. :::pause::: ```py ...``` " --name "Auth risk review"
              →  core parses → segments → mint id → generate link "pale-fire" → store → (opt) push to phone
              →  stdout:  glyde.local/r/pale-fire
              →  phone buzzes; tap; RSVP reader, seconds later.
```

No model in the loop. Local. Deterministic. That is the product.

## Open questions for the human

- **Enrichment default.** Ship with Haiku enrichment strictly opt-in (my recommendation — keeps
  the headline path key-free and deterministic), or make raw piped text "just work" with markup
  out of the box (an API-key dependency in v1)?
- **Memorable-link source.** Famous-novel phrases (evocative, but a corpus/licensing question and
  longer to thumb on mobile) vs MLflow-style adjective-animal (trivial, collision-cheap)? Start
  literary, or start adjective-animal and upgrade?
- **Syntax scope for v1.** Exactly the spec-001 block set, or also ship the prose-pacing
  extensions (`==highlight==`, beat markers) now? More syntax = more to teach and more parser.
- **Formalise `Digest` now?** The domain entity is still the template `Record`. Commit
  `Digest` / `Provenance` / `Segment` into the glossary + an ADR now (so the other panels build
  against it), or keep prototyping the reader and formalise the contract later?
- **CLI-only v1, or a minimal MCP tool too?** Is the overnight headline the CLI alone (MCP firmly
  Phase 2), or do your primary agents (Claude Code / desktop) hand off via MCP naturally enough
  that a thin tool earns its place in v1?
