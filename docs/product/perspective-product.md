# Product perspective — Glyde v1 vision & the scope cut

_Role: Product strategist (vision & v1 scope). One panel voice; the data shape I name
here is product vocabulary, the engineers own the schema._

**Positioning in one line:** Your agents write a lot. Glyde lets you *read* it — fast, low
fatigue, and never lost.

## The reframe: the reader is the last mile, not the product

Spritz shipped one-word RSVP in 2014. The reading science (see
`docs/research/rsvp-reading-modes.md`) says the pivot-flash is oversold and that the real
dyslexia wins are crowding control and the flow modes — which the prototype already nails.
So the reader is **table stakes**, not the moat.

The wedge is the era. Coding agents moved the bottleneck from *writing* code to *reading the
firehose* of natural-language output they emit — PR summaries, research dumps, log triage,
design docs. That firehose is worst for a developer **with dyslexia**: high volume, high
fatigue, time-pressured. **Glyde is the digest layer for that firehose.** The product is the
*handoff loop + provenance + a personal library*; the dyslexia-tuned reader is the last mile
that makes the loop worth living in.

This is the call I most want the panel to internalise: build the loop, not just the reader.

## Target user

The **dyslexic software engineer who works with coding agents** (Claude Code, Cursor). Not
"all dyslexic readers," not "all developers." v1 is **N=1 dogfood** (the builder), Phase 2 is
a handful over the LAN, Later is thousands. If the builder stops reading raw agent output in
the terminal, the product works. Everything else is downstream of that.

## The job to be done

> *When my agent finishes a big piece of work and I have to absorb the natural-language
> result fast and without eye fatigue, hand it to Glyde so I get a named, low-fatigue digest
> I can re-find later.*

**Top 3 use-cases** (in priority order):

1. **PR / change digest** — agent finished a feature; "what changed and why" without opening
   40 files. Highest frequency; naturally prose+code (so block detection matters most here).
2. **Research / investigation synthesis** — a multi-agent dump like *this repo's own*
   `rsvp-reading-modes.md`. Dense, inferential, the exact thing RSVP plus flow modes is for.
   Dogfood gold.
3. **Log / failure triage** — agent triaged a CI break or incident; the narrative of what
   broke and the candidate cause, under time pressure when fatigue is highest.

## Core value proposition

Three things only Glyde does together:

- **Agent-native handoff** — an agent (or the CLI) hands off text/a file and gets back a
  readable digest. The agent is a first-class *producer*, not an afterthought.
- **Provenance** — every digest knows what produced it (agent, task, source kind, time). A
  digest is an artifact you can trust and trace, not a transient paste.
- **A personal library** — digests persist, named and addressable. You never re-paste, never
  lose one.

## Name + memorable link are features, not garnish

Two distinct handles, both first-class on the digest:

- **Digest name** — agent-given, *semantic* ("auth-refactor PR review").
- **Memorable link** — generated, *evocative* slug, MLflow-adjective-animal energy but drawn
  from novels (`pale-fire-meridian`). It is the **speakable, shareable retrieval key**.

Why this is real accessibility, not whimsy: an evocative phrase is far easier for a dyslexic
user to recall, say aloud, and re-find than `digest #4471` or a UUID. *"Did you read
pale-fire-meridian?"* is the handoff reference — speakable to a person, typeable to an agent,
shareable to a phone. The name says **what**; the link says **how you refer to it**.

## The data it implies (product altitude)

Replace the template **Record** with **Digest** as the canonical entity (the glossary invites
this). One typed surface, reused by CLI, API, MCP and UI (DRY, the house rule). A Digest
carries: source text/file pointer · **provenance** (agent, task/prompt, source kind, time) ·
the **parsed structure** (prose runs + typed blocks — what block-pause consumes) · the
**name** · the **memorable link** · reader metadata (word count, est. read time). The act is
a **handoff**. Engineers own the schema; this is the vocabulary.

## Positioning vs prior art

| | What it does | What it lacks |
|---|---|---|
| Spritz / RSVP readers | paste → flash one word | no memory, no provenance, no agent, no library |
| Bionic Reading | bolds word-prefixes | passive, no speed control, no agent, no structure |
| TTS / read-aloud | linear audio | can't skim, slow, no structure, no library |
| **Glyde** | agent handoff → named, traceable digest → low-fatigue multi-mode read | (the thing none of them is: agent-native + kept) |

## The v1 cut (opinionated)

**Overnight v1 — the loop, end to end:**
- **Digest** entity replacing Record: store text + provenance + name + memorable link.
- **CLI handoff** (`glyde add <file>` / pipe) returns a name, a memorable link, and a URL.
  Cheapest agent-native entry point; the CLI surface already exists.
- **Memorable-link generation** — evocative, deterministic, collision-handled.
- **Library list** — digests by name + link + provenance; click to read.
- **Read a stored digest by its link** — *serve the existing `prototype/reader.html`* with the
  digest injected. Do **not** rebuild the reader in SvelteKit overnight.

**Closest cut:** block-pause (spec 001) is **fast-follow (v1.1)**, not overnight. The novelty
is hand-off → store → read; a prose-stripped digest is still useful on night one. But because
the #1 use-case is code-heavy, this is the call most likely to be overturned (see below).

**Phase 2 — agent-native + mobile:**
- **MCP server** so agents hand off natively ("rsvp that") without shelling out.
- **LAN-to-mobile**: responsive reader, QR-to-phone for a link.
- Block-pause (if not pulled into v1); reader ported into the SvelteKit typed seam.
- Agent **skill / prompt library** — how to author a good digest (spec 001's authoring half).

**Later — hosted, multi-user:**
- Accounts/auth; shared digests + team libraries; synced reading-pref profiles; opt-in
  reading analytics; the public API + distributed prompt library.

## Success signals (a few, honest at N=1)

- **Dogfood frequency** — digests handed off per day; the builder stops reading raw output
  in the terminal (truest signal). Target: the default consumption path within a week.
- **Read-through rate** — fraction of opened digests finished (proxy for *low-fatigue enough*).
- **Re-find rate** — digests reopened by their memorable link (proves library + naming earn
  their keep).
- **Time-to-digest** — handoff → absorbed, vs reading raw. Faster *and* lower fatigue.
- (At multi-user) WAU dyslexic engineers; digests/user/week.

## Open questions for the human

- **Is block-pause in the overnight v1, or fast-follow?** I cut it to v1.1, but if code-heavy
  PR digests are the #1 use-case from night one, it may be non-negotiable. The sharpest lever.
- **CLI-first or MCP-first handoff?** I chose CLI (cheap, MCP Phase 2). If your dogfood lives
  entirely inside Claude Code, MCP-first may be the truer v1 entry point.
- **Reader for v1: serve the prototype `reader.html` as-is, or port into the SvelteKit typed
  seam now?** Biggest overnight scope lever; I chose serve-as-is.
- **Memorable link: local-unique (local-first) or globally-unique/shareable-off-device from
  v1?** Shareability is a named feature; making it global early pulls hosting forward.
- **Provenance depth:** minimal (source kind + time + agent label) or rich (full task/prompt
  chain, file pointer, git SHA)? It shapes the one typed surface everything else reuses.
