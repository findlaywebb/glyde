# 001 — Block-pause: tasks

Status: not started. Tick off during implementation. Order is dependency-aware.

- [ ] Run the plan-reviewer agent on `plan.md`; address blocking feedback before coding.
- [ ] Add a fixture `prototype/` document mixing prose + fenced code + table + image + `:::pause:::`.
- [ ] `launch.py`: parse markdown into an ordered segment list (prose runs + typed blocks).
- [ ] `launch.py`: keep `strip_markdown` for prose runs only; capture code `lang`, table grid,
      image src/alt, note content.
- [ ] `launch.py`: inject the segment list as JSON into the reader (replace the flat string).
- [ ] `reader.html`: model the timeline as segments; prose tokenises as today, a block is one stop.
- [ ] `reader.html`: render static cards per kind (code monospace, table grid, image, note prose).
- [ ] `reader.html`: auto-pause on a block; Space/Enter resumes; Left re-shows the last block.
- [ ] `reader.html`: block-ahead cue during the last few prose words before a block.
- [ ] Verify against the fixture in all reading modes; confirm prose-only docs are unchanged.
- [ ] Update the reader authoring guidance (lead-ins, summarise-then-show) and the "rsvp that"
      memory note so streamed documents flow between prose and pauses.
