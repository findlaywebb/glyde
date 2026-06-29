# RSVP reading modes: research synthesis

Background research behind Glyde's reader. Captures a four-agent investigation into how
speed readers present text, what the reading science says (especially for dyslexia), and
how to handle non-prose technical content. The reader prototype lives in `prototype/`; this
document is the durable "why" behind its design. See also `decisions/0004-reader-modes.md`
(the decisions taken) and `../specs/001-block-pause/` (the next feature).

## What RSVP is

RSVP (Rapid Serial Visual Presentation) streams words one at a time at a fixed screen point,
so the eye stops moving (no saccades, no line tracking). The signature refinement is the
ORP (Optimal Recognition Point): a single pivot letter, slightly left of centre, highlighted
and x-locked, where a word is recognised fastest. This is the Spritz / Spreeder lineage.

## Showing context around the focal word

Pure single-word RSVP removes the two things normal reading relies on, and the research is
consistent that both losses hurt comprehension:

- **Parafoveal preview.** In normal reading the eye previews the next word(s) before fixating
  them, and that preview carries semantic content (it modulates the N400, a neural index of
  meaning integration). RSVP removes it. Showing the upcoming word restores part of it.
- **Regression.** Normal reading lets you look back to repair comprehension (~10-15% of
  fixations). RSVP forbids it. Showing the previous word is a partial substitute.

Comprehension holds to roughly 300 wpm and degrades above ~350-450 wpm, inferential content
first. The ORP red letter reduces saccade need but has **no proven comprehension benefit** on
its own.

### Crowding is the dominant risk for dyslexia

Flankers placed too close to the focal word cause visual **crowding**, which impairs
recognition. Dyslexic readers are markedly more sensitive: they need roughly **1.5x more
separation** than controls to escape crowding. This is the single most important constraint.
Consequences for the design:

- Show at most **one word each side**. More raises crowding and clutter for little gain.
- **Dim** the context (reduced contrast / opacity) so it reads as peripheral, not competing.
- Separate it generously. Placing context **above and below** the focal word sidesteps the
  horizontal crowding that hurts dyslexic readers most, which is why Glyde defaults there.

### Dyslexia specifics worth keeping straight

- "RSVP is great for dyslexia" is largely **marketing, not evidence**. The comprehension cost
  applies to dyslexic readers too, so generous pause / step-back controls matter.
- **Dyslexia fonts (OpenDyslexic, Dyslexie) show no reliable benefit**, sometimes slower. A
  clean sans (Glyde defaults to Atkinson Hyperlegible) performs as well or better. Keep
  OpenDyslexic as an option, do not push it.
- **Generous letter/word spacing** is the best-supported manipulation, but it slows skilled
  readers, so it belongs as an adjustable control, not a forced global default.
- **Per-letter colour gradients** are not evidence-backed and sometimes worsen dyslexic
  reading. Colouring only the single ORP pivot is fine; rainbow-per-letter is not.

### Context-preserving alternatives (the strongest comprehension results)

The largest measured effects are not single-word RSVP at all, they keep the whole text visible:

- **Guided reading** (Werth): full text shown, a marker paces you in small chunks, already
  read text is removed to discourage regression. Reported ~70% reduction in reading errors.
- **Text fading** (Reading Acceleration Program): text visible, each word fades shortly after
  you reach it, pushing pace while keeping comprehension.

Glyde ships both as modes (Guided sweep, Fading trail) alongside RSVP, because they are likely
the lower-fatigue choice for long, comprehension-heavy sessions.

## How shipping tools actually do it

- The famous tools (Spritz, OpenSpritz, jetzt, Squirt, Sprits-it, Spray) show **one word, no
  flanking context**. Context, where present, is bolted on as peek-on-pause (Reedy),
  rewind-to-sentence-start (Squirt), or a different non-flashing mode.
- Tools that show real multi-word context (Spreeder chunks, Outread guide) **drop the ORP
  pivot entirely**. That is the universal trade-off: nobody both flanks with words and keeps a
  true x-locked pivot, except open-source implementations.
- The cleanest open-source context approach (speeedy) stacks previous/next on **separate rows
  above/below** at ~38% size and ~15% opacity, decoupled from the pivot row. This matches the
  crowding science and is what Glyde adopted.

### ORP x-lock technique

The pivot index is the length-bucketed "Spritz table" everyone converges on
(`len<2 -> 0; 2-5 -> 1; 6-9 -> 2; 10-13 -> 3; 14+ -> 4`). Two ways to keep it centred:

- **Three equal flex/grid columns** (pure CSS): left cell right-aligned, pivot centre, right
  cell left-aligned. Centres on the column.
- **Measure-and-translate** (jetzt): render the word, measure the pivot glyph, translate so its
  centre hits a fixed reticle. Font-agnostic, centres on the actual glyph. **Glyde uses this**,
  because it stays rock-stable across proportional fonts and all context modes.

## Non-prose technical content (code, tables, diagrams, math)

The evidence here is decisive: **RSVP is valid only for linear prose.** The moment content is
2-D or non-linear, streaming it word-by-word destroys the structure comprehension depends on.

- **Code is read non-linearly.** Eye-tracking (Busjahn et al.) shows programmers follow
  execution / data-flow order and jump between declaration and use, and experts do this *more*
  than novices. RSVP forcibly imposes one linear order and removes the regressions code reading
  needs. Code must be shown statically, not streamed.
- Shipping RSVP tools mostly **strip or flatten** non-prose. The one good idea in the wild
  (Reedy) is to **break out of the stream and render the block statically**, then resume.
- The general pattern is Mozilla Readability-style **content classification**: stream the
  prose, and when a structurally-typed block appears (code, table, figure, math), stop and hand
  off to a statically rendered view, then continue.
- **Tables**: a linear cell-by-cell dump is unintelligible (the screen-reader lesson). Show the
  grid; if you must linearise, prefix every cell with its header.
- **Math**: inline expressions can be linearised into the prose (ClearSpeak-style, "x squared
  plus one"); display equations behave like figures (pause and show).

This is the basis for the block-pause feature: detect blocks up front, pause the stream, render
them statically, resume on a keypress, with a small "block ahead" cue so the stop is not jarring.
Specified in `../specs/001-block-pause/`.

## Future work (roadmap)

Roadmap lives in `specs/` as stubs; smaller reader-polish items, not yet worth a full spec:

- **Block-pause + authoring instructions** for code/tables/diagrams/math. Specified:
  `../specs/001-block-pause/`.
- **Guided / Fading polish**: tune the discrete-jump band; optional page mode (no scroll at
  all, advance a screenful when the current one is fully read).
- **Per-font spacing memory**: the spacing control is global; very negative spacing tuned for
  OpenDyslexic mangles Atkinson. Remember spacing per font.
- **Context-line "preview behind"** (rollecode-style faint sentence backdrop) as a fourth
  context treatment, if same-line/above-below/sentence prove insufficient over long sessions.
- **True guided-reading mode** (Werth-style chunk pacing with read-text removal), the
  highest-comprehension option, as a distinct mode beyond the current sweep.

## Sources

Key citations from the research (full set in the agent investigation):

- Parafoveal preview / N400: Stites & Laszlo et al. 2022; Barber et al. (RSVP-with-flankers).
- RSVP comprehension: Benedetto et al. 2015 (Spritz); Rayner et al. 2016, *So Much to Read, So
  Little Time*.
- Crowding & dyslexia: Martelli et al. (crowding, reading, dyslexia); extra-large letter
  spacing studies.
- Dyslexia fonts: OpenDyslexic efficacy studies (no reliable benefit).
- Guided reading / fading: Werth (computer-guided reading); Reading Acceleration Program.
- Code reading: Busjahn, Bednarik, Begel et al., *Eye Movements in Code Reading*, ICPC 2015.
- Reading mode / classification: Mozilla Readability.js. Math: Speech Rule Engine (ClearSpeak).
