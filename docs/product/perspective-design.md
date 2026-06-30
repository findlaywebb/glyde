# Perspective — Visual & Interaction Design

_Role: visual & interaction designer. Product altitude; choices made, not a menu._

**Note on screenshots:** none are committed (the only images in the repo are framework
favicons and coverage assets). I grounded this in the live prototype — `prototype/reader.html`
+ `launch.py` — and pulled the palette from its CSS. **Capturing real reader screenshots into
`docs/product/` should be a v1 chore**, because right now the design memory lives only in code.

## The palette is the brand — keep it

The coral-red pivot is Glyde's signature; preserve it everywhere. Dark-first (matches the
frontend's `dark` default). The three prototype themes carry over verbatim:

- **Dark (default):** bg `#11151c`, text `#e6edf3`, muted `#7d8590`, **accent `#ff5c5c`**,
  panel `#1b2027`, hairline `#2a313b`.
- **Light:** bg `#fdfdf8`, text `#1a1a1a`, accent `#d12`, panel `#f0efe8`.
- **Sepia:** bg `#f4ecd8`, text `#3a2f23`, accent `#b3402a`, panel `#ece1c8`.

Type: **Atkinson Hyperlegible** for reading (the research-backed default, not a "dyslexia
font"), **Lexend** for UI chrome, OpenDyslexic as an option only. Accent is used with
discipline — the pivot glyph, the progress fill, the primary action. Nothing else competes.

## The core move: the reading screen is the word, not the controls

The prototype is a **desktop control panel** — a twelve-control flex-wrap bar with 13px
labels and 110px sliders. That is exactly wrong for the north star (one-handed mobile over
the LAN). Invert it. v1's reading screen is **almost entirely the stage**; chrome
**auto-hides during playback** and returns on tap/pause. Everything configurable moves to
Settings. Low fatigue means the eye rests on one still point and sees nothing else move.

## Reader — three modes, one calm stage

- **RSVP:** the red ORP pivot stays x-locked at a fixed reticle (the two faint ticks),
  context dimmed **one word above / one below** — keep that default; it is the crowding-safe
  choice and the thing that makes Glyde feel calm, not frantic.
- **Guided sweep / Fading trail:** full text, left-aligned, comfortable measure; the
  highlight moves, the page jumps discretely (never teleprompter-scrolls).
- **Pauses** (sentence/paragraph) are felt as a _beat_, not a UI event — the pivot holds a
  fraction longer. No card, no chrome.
- **Pause-and-show blocks** (code / table / image / note, per `specs/001-block-pause/`) are
  the one place the stage transforms: the stream halts and a **static, full-width card**
  slides up, held still for non-linear reading. A small accent **"code ahead" chip** appears
  at the top edge during the last few prose words so the stop never jars. A big thumb-zone
  **Resume** continues; back re-shows the last card. On mobile: code cards scroll
  horizontally with a wrap toggle; wide tables fall back to stacked **header: value** rows
  (the screen-reader lesson). Block kind is labelled — structure is provenance too.

## The control surface — thumb-first

- **Tap the stage = play / pause.** This is the headline affordance: no aiming for a small
  button one-handed.
- A slim **bottom transport bar** in the thumb arc: replay-word (regression substitute —
  matters for the dyslexic reader), play/pause (large, centre), step-forward. A **speed rail**
  on the right edge (drag up = faster) keeps the most-adjusted control under the thumb without
  occluding the word.
- **Mode switch** lives one swipe up in a quick-sheet (changed per task, not per second).
- **Progress** is a hairline bar pinned to the stage bottom: accent fill on the `line` track,
  **tap to scrub**, with **notches marking upcoming blocks** so "three code blocks ahead" is
  visible. Show **time-remaining prominently** ("~2m 14s left", tabular-nums) — it is the
  "can I finish this before the kettle boils" signal — with position (142 / 980) secondary.

## Library — the home screen (new surface)

The prototype has none; v1 needs it. A newest-first **feed of digests**, grouped by day. Each
card:

- **Agent-given name** as the title; the **memorable link** (e.g. `the-luminous-fen`) beneath
  it in a distinct mono treatment — tappable, copyable, the shareable handle.
- **Provenance:** source (file / agent / CLI), who handed it off, when, originating repo/task
  where known.
- **Shape badges:** word count, est. read time, block mix ("3 code · 1 table") — you know what
  you're walking into.
- **Read-state:** unread / in-progress (thin resume bar at the left-off point) / done. Tap =
  open at last position; re-read is one tap. The slug doubles as a **deep link**
  (`glyde.local/the-luminous-fen` opens that digest) — the navigable version of MLflow's slugs.
- Search/filter by name, source, date.

## Settings / preferences

The full prototype control set, **off the reading screen**, grouped: **Reading** (mode,
speed, chunk, ramp), **Comfort** (font, size, spacing, theme), **Context** (treatment, size).
A **live preview** word at the top so each change is felt instantly. Persisted (localStorage
today; server-side per user when hosted).

## The data this implies (first-class contract)

This design replaces the template **Record** with a **Digest**: `id`, `name`,
`slug` (memorable link), `created_at`, `provenance {source_kind, source_ref, agent, repo?,
task?}`, **`segments`** (ordered `prose` runs + typed `block`s `{kind, payload, lang?}`),
`counts {words, blocks_by_kind}`, `est_read_time`, and per-user `read_state {position,
status, updated_at}`. Plus a typed **Preferences** object. One typed surface: the library is a
projection (name, slug, counts, read-state); the reader consumes full `segments`; CLI / API /
MCP mint the same shape. The reader UI is only as good as `segments` — the block-pause
pipeline (`specs/001-block-pause/`) is the data prerequisite, not a polish item.

## Open questions for the human

- **Is the Library in the v1 cut, or reader-only?** Handoff could open straight into the
  reader with history deferred. This is the biggest scope fork for an overnight v1.
- **Gesture-first vs button-first transport?** I lean hybrid (tap-to-pause + a visible thumb
  bar) for predictability, but a dyslexic primary user may want _only_ explicit buttons.
- **Is the memorable link a real navigable deep-link/route in v1, or a cosmetic label?** It
  changes routing and the slug's uniqueness guarantees.
- **Per-digest read-state (resume / unread / done) in v1, or defer?** It's the line between a
  "library" and a flat history list.
- **Wide blocks on mobile: horizontal-scroll the real grid, or auto-stack to header: value —
  and do we attempt syntax highlighting in v1, or monospace-only?**
