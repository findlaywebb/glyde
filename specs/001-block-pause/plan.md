# 001 — Block-pause: plan

Status: draft. **Not yet reviewed by the plan-reviewer agent.** Per
`../../docs/decisions/0001-agentic-gates.md`, run the plan-reviewer (blocking) before
implementing.

## Approach

Two changes: the launcher emits structured segments; the reader consumes them and pauses on blocks.

### 1. Launcher (`prototype/launch.py`) — structured segmentation

Replace the flat-string output with an ordered segment list, injected as JSON:

```
[ {type: "prose", text: "..."},
  {type: "block", kind: "code"|"table"|"image"|"note", content: "...", lang?: "..."},
  ... ]
```

- Parse markdown into segments before substitution: fenced code -> `code` (capture `lang`);
  pipe tables -> `table` (keep the raw grid); `![alt](src)` -> `image` (src + alt);
  `:::pause … :::` -> `note`; everything else accumulates into `prose` runs.
- Inline math stays inside prose; display math (its own block) -> a block (kind `note` or a
  dedicated `math`).
- Keep `strip_markdown` for the prose runs only; do not strip block content.
- Inject the segment list (JSON) into the reader template in place of the current single string.

### 2. Reader (`prototype/reader.html`) — pause/resume on blocks

- Model the timeline as the ordered segments. Prose runs tokenise as today; a block is a single
  stop.
- On reaching a block: **auto-pause**, hide the RSVP/flow stage, render a **static card** sized
  to the viewport (code: monospace + line height; table: grid; image: `<img>` or alt; note:
  prose). Show "Press Space/Enter to continue".
- `Space`/`Enter` dismisses the card and resumes the next prose run. `Left` re-shows the last block.
- **Block-ahead cue**: while the last ~N prose words before a block stream, show a small icon /
  label so the stop is anticipated.
- Persist nothing new beyond existing settings.

## Files to touch

- `prototype/launch.py` — segmentation + JSON injection (the bulk of backend-side work).
- `prototype/reader.html` — segment timeline, card rendering, pause/resume, block-ahead cue.

## Files to LEAVE ALONE

- The ORP measure-and-translate lock, the three reading modes, context modes, settings
  persistence: unchanged. Blocks are orthogonal to how prose is presented.
- The `rsvp` command / `scripts/rsvp.sh` / shell function: unchanged.

## Test plan

The prototype has no harness yet; verify by example:

- A fixture `stream.md` with prose + a fenced code block + a table + an image + a `:::pause:::`.
- Confirm: prose streams, each block auto-pauses and renders statically, Space resumes, Left
  re-shows, block-ahead cue appears, and a prose-only document behaves exactly as before.
- If this reader graduates into the app frontend, segmentation moves behind the typed API and
  gets real unit tests; until then, example-based verification is the bar.

## Delegation

Single-context change; no fan-out needed. If it grows, the launcher segmentation and the
reader rendering are file-disjoint and could split.
