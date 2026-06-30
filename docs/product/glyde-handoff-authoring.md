# Glyde handoff authoring guide

_For an agent (or the CLI) handing off output to Glyde._ The promise: you finish a wall of
analysis, run **one command**, and the dyslexic developer is reading it in the low-fatigue reader
on their phone seconds later. This guide is how to make that digest read well.

The loop: you write **Glyde-Markdown**, hand it off, and Glyde parses it into the **Digest IR**
(`parse_glyde_markdown` → an ordered list of segments), mints a memorable slug, stores it, and
serves it to the reader. Your markup *is* the pacing — where the reader pauses, what it stresses,
what it pulls out of the word stream onto a card. Terms here are defined in `../glossary.md`; the
contract is ADR `../decisions/0005-digest-ir.md`.

## Hand it off

**CLI (the v1 headline).** `glyde add` takes a text argument, an existing file path, or piped
stdin; `--name` is required, `--tag` is repeatable, `--enrich` is optional.

```bash
glyde add "…Glyde-Markdown…" --name "Auth migration plan" --tag architecture
glyde add notes.md --name "Auth migration plan"        # an existing path → a file source
some-agent | glyde add --name "Auth migration plan"    # piped stdin → a pipe source
```

It prints the `name`, the `slug`, and the reader URL (`/d/{slug}`). The CLI **infers provenance**:
`source_kind` is `cli` (literal text), `file` (an existing path, with the path as `origin`), or
`pipe` (stdin); `ingested_via` is `cli`; `producer` is left unset.

**API / MCP (a Phase-2 wrapper over the same path).** `POST /digests` takes the full request, so
this is where you set provenance explicitly — supply exactly one of `text` or `segments`, plus
`name`, `source_kind`, and optionally `origin`, `producer`, `ingested_via`, `tags`. A producer that
already has structure can `POST` `segments` directly and skip Glyde-Markdown entirely.

## Name it well

`name` is the speakable, semantic title shown in the library — write it like a good commit subject:
specific and scannable. *"Auth migration plan: sessions → JWT"*, not *"Output"*. You do not choose
the `slug`; Glyde mints a memorable two-word link (e.g. `amber-otter`) as the shareable handle.

## Say where it came from (provenance)

Provenance makes a digest traceable back to its source — fill it so the reader knows what produced
this and how it arrived. Over the API set `source_kind` (`agent`, `file`, …), `origin` (a `repo@sha`,
a run-id, a url, a path), `producer` (your model/agent label), and `ingested_via`. Over the CLI these
are inferred. `enriched` is set by Glyde, not you — leave it alone.

## Write good Glyde-Markdown

The reader streams prose **one word at a time** on a fixed pivot, **pauses** at your punctuation, and
shows non-prose as a **static card**. Four habits make that read well.

### One idea per pause

Prose flows until a terminator, and each terminator is a beat the reader feels: a **clause**
terminator (`,` `;` `:`) is a short beat, a **sentence** terminator (`.` `!` `?` `…`) a longer one, a
**blank line** a paragraph beat. Write in short, complete clauses — one idea between beats. A 60-word
sentence with no commas streams as one unbroken run and exhausts the reader; the same content split at
clauses reads in comfortable steps. (A terminator mid-token, like the dot in `3.14`, stays literal —
it is not a beat.)

### Highlight the decision

`==strong==` the load-bearing words — the decision, the result, the one number that matters — and the
reader dwells a little longer on them. Use `*em*` for softer stress and `` `code` `` for identifiers,
paths, and flags. Don't highlight everything: if half the words are strong, none are.

### Headings and lists

`#` starts a heading. `-`, `*`, `+`, or `N.` start list items — each item becomes its own run with a
beat after it, which is exactly how a list wants to be paced. Reach for a list when you have parallel
points; the beats come for free.

### Blocks: pause-and-show, never streamed

Code, tables, images, math, quotes, and notes are **blocks** — shown whole on a card, never flashed
word by word. Put anything non-prose in a block; never inline a code snippet into a sentence (it would
stream as words).

- **Lead into a block with a prose sentence.** The prose run immediately before a block becomes its
  `lead` — the runway the reader sees as it approaches the card (*"Here is the migration:"*). A block
  with no lead arrives cold; write the runway.
- **Summarise long code, then show it.** Don't make the reader parse 80 lines on a card to find the
  point. Say what it does in the lead sentence, then show the block — the prose carries the meaning,
  the block is the reference.

Block markers: ```` ```lang ```` … ```` ``` ```` (code) · `| a | b |` rows (table) · `![alt](src)`
(image — covers diagrams and figures; write real alt text) · `$$ … $$` (math) · `> …` (quote) ·
`::: … :::` (note / aside).

### A worked handoff

Raw agent output — one breathless sentence with code inlined:

> I looked at the storage options and decided to use SQLite because it needs no server and the data
> is single-user, here is the migration: CREATE TABLE digests (id TEXT PRIMARY KEY, slug TEXT NOT NULL UNIQUE);

The same content as Glyde-Markdown:

````markdown
# Storage decision

I compared the options, and chose ==SQLite== over Postgres: it needs no server, and the data is single-user.

Here is the migration:

```sql
CREATE TABLE digests (
  id TEXT PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE
);
```
````

What the reader gets: a heading; a sentence that dwells on **SQLite**; a clause beat at each comma and
colon; then a runway sentence (*"Here is the migration:"*) leading into a code card the reader studies
at rest — not a wall of SQL flashed one token at a time. Hand it off:

```bash
glyde add storage-decision.md --name "Storage decision: SQLite over Postgres" --tag architecture
```

## Don't

- Inline code, tables, or math into prose — block them, or they stream as words.
- Write giant unpunctuated sentences — they stream with no beats.
- `==highlight==` everything — stress means nothing if it is everywhere.
- Paste a long file with no lead and no summary — lead, summarise, then show.
- Hand-author `linear_form`, token classes, or pacing numbers — v1 derives pacing in the reader from
  the user's `Preferences`. Write clean Glyde-Markdown and let the parser build the IR.

## A note on `--enrich`

`--enrich` asks Glyde to run an LLM pass that adds structure to **raw, unstructured** text before
parsing; it is skipped when the text already has markup and falls back to the deterministic parser when
no enricher is configured. Prefer to emit good Glyde-Markdown yourself — you know which line is the
decision and what must not be streamed; a second model re-deriving that from flat text is lossy.
