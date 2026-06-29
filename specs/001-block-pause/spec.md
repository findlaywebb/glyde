# 001 — Block-pause for non-prose content

Status: draft (not yet implemented)

## Problem

The reader streams text word-by-word. That is correct for prose and wrong for non-prose:
code, tables, diagrams, and display math are 2-D or non-linear, and streaming them one word
at a time destroys the structure comprehension depends on (see
`../../docs/research/rsvp-reading-modes.md`, and the eye-tracking evidence that code is read
non-linearly). The current launcher simply strips code/tables, which loses the content.

Desired behaviour: the reader streams the prose, and when it reaches a non-prose block it
**pauses, renders that block statically** (readable, not RSVP'd), and **resumes on a keypress**.
A small "block ahead" cue appears a few words before the stop so it is not jarring.

## Scope

Author content is markdown (Claude writes the `stream.md`). Reuse markdown structure rather
than inventing syntax:

- Fenced code blocks -> a **code** card (monospace, readable).
- Markdown tables -> a **table** card (rendered grid).
- Images `![alt](path)` -> an **image** card (show image, or alt text if missing).
- An explicit `:::pause … :::` directive -> an arbitrary **note** card.
- Inline math stays in the prose stream; display/block math is treated as a block (pause).

The pipeline becomes structured: the launcher parses the source into an ordered list of
segments (`prose` runs and typed `block`s) rather than one flat string; the reader streams
prose segments and pauses on blocks.

## Acceptance criteria

- A document mixing prose and a fenced code block streams the prose, then **auto-pauses** and
  shows the code statically (monospace, not streamed); pressing Space/Enter resumes into the
  next prose run.
- A "block ahead" cue is visible while the last few prose words before a block stream.
- `Left` (or an explicit control) re-shows the most recent block.
- Tables render as a grid card; images render (or show alt text); `:::pause … :::` renders its
  content as a note card.
- Block detection is **deterministic and up front** (the segment list is built before playback),
  not a mid-stream heuristic.
- Works in all reading modes, or, if a mode cannot host a static card sensibly, that is stated
  and the block still pauses cleanly.
- The existing prose-only behaviour is unchanged when a document has no blocks.

## Out of scope

- Syntax highlighting quality beyond "monospace, legible" (a later polish).
- Table "walk the cells" guided mode and full MathML/ClearSpeak linearisation (future work).
- Backend/frontend integration: this targets the `prototype/` reader. Moving the reader into
  the app's SvelteKit frontend is a separate spec.

## Authoring instructions (the flow-between-pauses half)

How Claude should write `stream.md` so the streamed experience flows:

- **Lead into a block** with a prose sentence ("The handler looks like this:") so the pause has
  a runway and the reader knows why it stopped.
- **Summarise long code in prose, then show it**; do not stream a 60-line dump expecting the
  card to carry it.
- Keep prose skimmable between cards; one idea per pause.

These belong in the reader's authoring guidance (and the memory note that drives "rsvp that").
