# Sub-agent brief template

Fill all four parts before launching. A brief missing any one of them is the #1 cause of wasted, duplicated, or off-target sub-agent work. Drop this straight into the `Agent`/Task prompt.

```
OBJECTIVE
  <The single question to answer or single outcome to produce. One sentence.
   Not "look into auth" — "Determine which module validates the session JWT and
   whether it checks expiry.">

OUTPUT FORMAT
  <Exactly what to return, and how. This is what lands back in MY context, so be
   strict and demand distillation, not a transcript. Examples:
   - "A 5-bullet summary + the file:line of the validation call. No code dumps."
   - "A verdict (REAL / NOT-REAL) per finding + one-line justification each."
   - "A list of {file, line, current value, proposed value}.">

TOOLS & SOURCES
  <Where to look, what to use, what to ignore.
   - "Search src/auth/ and src/middleware/ only. Ignore tests and vendored code."
   - "Use ripgrep + Read. Do not run the app or call external services.">

BOUNDARIES
  <In scope, explicitly out of scope, and the stop condition — kills "infinite
   exploration." Examples:
   - "Stop once you've found the validation path; don't trace downstream usage."
   - "Read-only. Do NOT edit any file."
   - "Budget ~15 tool calls; if not found by then, report what you ruled out.">
```

## Parallel fan-out — add a PARTITION line

When several agents run at once, the boundaries must also carve the work so two agents don't cover the same ground (the duplication failure mode). Give each agent a disjoint slice:

```
Agent A — BOUNDARIES: only src/ingest/**
Agent B — BOUNDARIES: only src/transform/**
Agent C — BOUNDARIES: only src/publish/**
```

State the partition explicitly in each brief; agents can't see each other and won't deconflict on their own.

## Cheaper-model handoff — tighten further

Routing to Sonnet/Haiku? The brief must be unambiguous enough that a smaller model can't misread it: concrete file paths over "the relevant files", an exact output shape, and a worked example of one input → expected output. If you can't make it that tight, keep it in the main thread.

## Fresh-context review handoff

```
OBJECTIVE      Review the diff against PLAN.md / the acceptance criteria below.
OUTPUT FORMAT  Findings only, each tagged [correctness] or [requirement-gap],
               with file:line. No style preferences. If none, say "no gaps found".
TOOLS&SOURCES  The diff (git diff <base>) and PLAN.md. Don't read my prior reasoning.
BOUNDARIES     Flag ONLY gaps affecting correctness or a stated requirement.
               Do not propose refactors or chase hypothetical edge cases.
```
The cap on the last line is load-bearing: an uncapped reviewer always finds something and pushes you into over-engineering.
