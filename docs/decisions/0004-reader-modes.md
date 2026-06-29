# 0004 — Reader modes, ORP lock, and context display

Status: accepted

Applies to the reader (currently the `prototype/` standalone; the design carries into the app).
Rationale and citations in `../research/rsvp-reading-modes.md`.

## Context

The reader must serve a dyslexic primary user across two needs that pull apart: fast skimming
(favours single-word RSVP) and comfortable, low-fatigue, comprehension-heavy reading (favours
keeping text visible). The reading science adds hard constraints: visual crowding
disproportionately harms dyslexic readers, single-word RSVP removes parafoveal preview and
regression, and the ORP red pivot has no proven comprehension benefit on its own.

## Decision

1. **Three reading modes, switchable, not one.** RSVP flash, Guided sweep, and Fading trail.
   The two flow modes (full text visible, position moves through it) exist because the
   strongest comprehension results in the literature keep the whole text visible, and they are
   the likely low-fatigue choice for long sessions. The user switches per task.

2. **ORP pivot via measure-and-translate**, not flex/grid columns. Render the word, measure
   the pivot glyph, translate so its centre hits a fixed reticle. It is font-agnostic and stays
   stable across proportional fonts and every context mode, which the column approach does not.

3. **RSVP context defaults to above/below**, dimmed, one word each side. Crowding is the
   dominant risk for dyslexic readers (they need ~1.5x more separation), and vertical offset
   sidesteps the horizontal crowding that hurts most. Same-line and Sentence modes are offered
   too, with a context-size control, but above/below is the default. Never more than one word
   each side.

4. **Flow modes never scroll continuously.** The text stays still; the highlight moves through
   it; the view jumps discretely (instantly) only when the current word leaves a comfortable
   band. Continuous re-centring scrolls like a teleprompter and caused motion sickness.

5. **Atkinson Hyperlegible is the default font, not a dyslexia font.** OpenDyslexic and Dyslexie
   show no reliable benefit and are sometimes slower; a clean sans performs as well or better.
   OpenDyslexic stays as an option. Only the single ORP pivot is coloured (no per-letter colour).

6. **Settings persist** (localStorage in the prototype): wpm, mode, context, sizes, font, theme,
   ramp. Generous controls (speed ramp, step-back, pause) matter because RSVP's comprehension
   cost is real for everyone, dyslexic readers included.

## Consequences

- The reader is genuinely multi-mode, which is more code than a single RSVP view, justified by
  the dyslexia-comfort goal and the fatigue trade-off the modes address.
- Spacing is currently a single global control; tuning it negative for OpenDyslexic mangles
  Atkinson. Per-font spacing memory is deferred (see the research doc's future work).
- Non-prose content (code, tables, diagrams) must not be streamed in any mode; that is handled
  by the block-pause feature, specified separately in `../specs/001-block-pause/`.
- These choices are reader-design decisions, not backend/frontend boundary changes; they are
  recorded here because they are load-bearing and easy to regress otherwise.
