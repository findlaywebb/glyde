# Perspective — Accessibility & reading-science

_Role: accessibility & reading-science specialist. Grounded in `docs/research/rsvp-reading-modes.md`,
ADR `0004-reader-modes.md`, and the pacing already in `prototype/reader.html`._

Low fatigue is the north star, and in dyslexia terms it has three cost centres: **eye-movement /
tracking load**, **visual crowding**, and **vigilance / working-memory load**. Every mode and
setting trades among these. The job is to spend the reader's attention where comprehension needs
it and nowhere else — and to compute that spend *once*, as data.

## The reading syntax must carry the pacing — not the reader

This is the load-bearing product call from my chair, and it lines up with Glyde's DRY / first-class-data
principle. The typed digest should be an **ordered list of typed segments**:

- **prose segment** = a sequence of typed **tokens**, each carrying: `text`, `pivot_index` (ORP),
  `dwell_weight`, `pause_after_weight`, `emphasis`, `token_class` (`word | number | symbol | low_freq`),
  `chunk_group_id`, and an optional `linear_form` (for inline math/symbols).
- **block segment** = `type` (`code | table | image | math | note`) + payload + the prose lead-in it follows.
- **document** = agent-given name, memorable link, provenance, token count, est. read-time at default WPM.

The pacing/emphasis/pivot decisions are computed **once, server-side, deterministically** (the backend
is local, so this stays local-first) and travel in the digest. CLI, API, MCP and the UI then *play* an
identical experience instead of four reimplementations of the pacing rules. Two payoffs the science
specifically wants: (1) frequency and clause signals the reader can't cheaply derive client-side get
baked in upstream; (2) the **agent can override** pacing semantically — mark the key result for emphasis,
force a beat, supply a spoken form for an equation. Keep the prototype's client-side pacing only as a
**fallback for the paste box**; the typed digest is the canonical surface.

## The timing model (concrete)

`dwell_ms = base × Π(multipliers)`, with `base = 60000 / W`. Default **W = 300 wpm** (the comprehension
ceiling the research cites; 350 degrades inferential content first), **ramp on** so the reader eases in.
At 300 wpm, `base ≈ 200 ms`.

Per-token dwell multipliers (these are what the syntax encodes):

| Signal | Multiplier | Why |
|---|---|---|
| Long word (`len > 8`) | `1 + 0.03·(len−8)`, cap ~1.4 | longer words need more recognition time |
| Low-frequency word | ×1.2 | rare words are slower to decode (needs a frequency lexicon) |
| Number / symbol-dense | ×1.3 (scale with digit count) | numerals are read cluster-by-cluster; a known slow point |
| Agent-marked emphasis | ×1.25 + visual weight | semantic salience the author flagged |
| First token after a pause/block | ×1.15 | re-acquisition cost on resume |

Pause-*after* weights (applied to the last token of a span):

| Boundary | Multiplier |
|---|---|
| Clause comma / `;` `:` / dash / close-bracket | ×1.5 |
| Clause boundary without punctuation | ×1.4 |
| Sentence end (`. ! ? …`) | ×2.2 |
| Paragraph end | ×2.8 |
| Before a block | full stop + "block ahead" cue |

Worked example: a rare 12-letter word ending a sentence → `200 × (1+0.03·4) × 1.2 × 2.2 ≈ 591 ms`. A short
mid-sentence function word → ~180 ms. That asymmetry *is* the comprehension aid.

## Pause points, chunking, pivot

- **Chunking — glue function words, keep the pivot on content.** Don't ship the blunt 1/2/3-word selector
  as the default. Default to **adaptive chunking**: glue a short (≤3–4 char) function word to its content
  neighbour ("of the", "to run") so they flash together, pivot anchored on the **content** word. Fewer
  flashes = less vigilance load, with little added crowding. Keep group width conservative (crowding is the
  dominant dyslexia risk) and keep the fixed-chunk selector as a manual override.
- **ORP pivot** — keep the Spritz bucket table + measure-and-translate (ADR 0004); encode `pivot_index` in
  the syntax. Colour **only** the pivot red, never per-letter (per-letter colour can worsen dyslexic reading).
  The pivot has no proven comprehension benefit alone, but it earns its place by cutting saccades.

## Pause-and-show is a correctness requirement, not polish

Affirm spec `001-block-pause` fully: RSVP is valid **only for linear prose**. Code is read non-linearly
(declaration↔use jumps), tables are 2-D, display math is a figure — streaming them word-by-word is the
screen-reader linearisation failure. The syntax **typing** blocks is what makes the reader stop, render
statically, cue ahead, and resume. Inline math should ship a `linear_form` ("x squared plus one") so it
reads as prose; display math pauses like a figure; a linearised table cell must be header-prefixed.

## Typography & palette (preserve what the user likes)

- **Font**: Atkinson Hyperlegible default (dyslexia fonts show no reliable benefit — keep OpenDyslexic as an
  option, don't push it). Lexend as the second strong option; mono only inside code cards.
- **Spacing** is the single best-evidenced dyslexia lever, so give letter-spacing a **small positive default**
  (~0.04em) rather than 0, with the slider to dial back; keep flow line-height ≥1.8. Per-font spacing memory
  is rightly deferred.
- **Palette**: keep all three themes. Critically, keep **off-white on near-black** (`#e6edf3` on `#11151c`) —
  *not* pure #fff/#000; max contrast causes visual stress for many dyslexic readers. Surface the **sepia/cream**
  theme prominently — warm low-contrast backgrounds are the classic visual-stress relief. Reserve the pivot red
  **exclusively within the reading surface** so the eye keys on it as the anchor.

## The v1 default mode: **Guided sweep**

I'd default to Guided sweep, not RSVP, and switch RSVP to a one-key "turbo". Justification: the north star is
*low fatigue*, and the research flags flow modes as the lower-fatigue choice for long, comprehension-heavy
sessions — which agent reasoning/plans/explanations are. Guided preserves parafoveal preview and regression
(both losses hurt the inferential content RSVP degrades first), has the strongest measured effect (Werth, ~70%
fewer reading errors), and **fails safe**: a first-run user sees the whole text and can't get lost in a flashing
stream. RSVP stays the signature mode where the red pivot shines — it's where speed lives, one keypress away.

## Open questions for the human

- **Default mode — Guided sweep or RSVP?** I argue Guided on north-star + evidence grounds, but you are the
  dyslexic primary user; if your instinct is the low-eye-movement RSVP flash, lived preference overrides the
  literature. This is the big one.
- **Where does pacing get computed — server-side into the typed digest, or client-side in the reader?** I
  recommend server-side (DRY, richer signals, lets agents override). It makes the digest the canonical surface
  and the reader a player — an architecture-shaping confirmation.
- **Does v1 ship the frequency lexicon + light clause-parser, or defer them?** Without them, v1 paces on
  punctuation only (as the prototype does today) and gains low-frequency / clause-boundary dwell as a fast-follow.
  Materially changes v1 scope.
- **Letter-spacing default — small positive (dyslexia-helpful) or 0 (skilled-reader-neutral)?** You're both
  dyslexic and a fluent developer-reader; the evidence pulls both ways.
- **Should the default WPM/mode adapt to content?** Short agent status updates suit RSVP-skim; long explanations
  suit Guided. Adaptive defaults are powerful but add a decision surface — v1 could stay a single fixed default.
