---
name: docstrings
description: Write, refine, or review Python docstrings against a consolidated Google/PEP-257 + house-style rubric. Use when adding docstrings to code that lacks them, improving weak or inaccurate existing docstrings, or auditing docstring quality on a diff/PR (e.g. a docstring-compliance ticket). Adapts to the target repo's configured docstring convention. Triggers include "add docstrings", "fix these docstrings", "review the docstrings", "are these docstrings any good", "document this module". For multi-file PR audits it fans out a parallel review.
---

# docstrings

Write, refine, and review Python docstrings to a single consolidated standard.
The reusable home for FMP's docstring rules — works on your own code and on any
codebase you review.

## The one principle

**The docstring must tell the truth about the code.** A grammatically perfect
docstring that misdescribes behaviour, lists the wrong arguments, or documents
exceptions the code never raises is worse than no docstring — it lies with
confidence. Accuracy-against-the-code beats every stylistic concern. Always read
the implementation, never grade the docstring text in isolation.

## Reference files

- `reference/conventions.md` — how a good docstring looks (the style definition,
  with worked good/bad examples). Read before **writing** or **refining**.
- `reference/rubric.md` — the severity-tagged scoring grid and structured finding
  shape. Read before **reviewing**.

## Step 0 — detect the project's convention (always)

Docstring rules are per-repo. Before doing anything, establish the local bar:

1. Read `pyproject.toml` (or `setup.cfg`/`ruff.toml`):
   - `[tool.ruff.lint.pydocstyle] convention` → `google` | `numpy` | `pep257`.
     Default to **google** if unset.
   - `[tool.ruff.lint]` `select`/`ignore` → is `D` enabled? Is `D401` (mood) or
     `D417` (arg coverage) ignored? Is `E501` (line length) ignored? This tells
     you what ruff already enforces (don't re-flag it) and what's left to you.
   - `per-file-ignores` → which paths are exempt from `D` (commonly `tests/**`,
     `scripts/**`). Don't demand docstrings there. Note whether `src/**` is
     covered for *all* functions (stricter than PEP 8's public-only rule).
2. If the convention is **not** Google, the universal mechanics in
   `conventions.md` still hold; only the section syntax changes (NumPy uses
   underlined headers, etc.). Adapt the section format, keep the substance.
3. Findlay defaults (imperative mood, the house examples) apply when writing his
   own code or in FMP repos; soften to the project's committed standard when
   reviewing a third party's code (see the consistency floor in the rubric).

State the detected convention in one line before proceeding.

## Mode: Write

Adding docstrings to code that currently lacks them.

- Read `conventions.md` first.
- Read the **implementation** of each target before writing — the docstring
  describes real behaviour, real raised exceptions, real return semantics.
- Trivial/obvious function → one-line summary only. Don't manufacture empty
  `Args:`/`Returns:` sections.
- No types in `Args`/`Returns` (Google + Memento: type hints carry them).
- After writing, run the linter to confirm mechanical compliance:
  `ruff check <paths> --select D` (adjust to the repo's config).

## Mode: Refine

Improving existing docstrings.

- Grade each against `rubric.md`, then rewrite the ones that fail — prioritise
  **Inaccurate** > **Incomplete** > **Filler** > **Style**.
- Preserve any genuinely useful content; don't churn a docstring that's already
  good. Restraint: an edit must improve accuracy or information, not just taste.
- Show before/after for non-trivial rewrites so the change is reviewable.

## Mode: Review

Auditing docstring quality without editing — produces findings, not edits.

### Scope: review the diff, not the file

When the target is a **PR or commit** (not "review this whole file"), the unit of
review is the **docstrings the change actually added or modified** — not every
docstring in the touched files. A compliance commit that adds docstrings to
previously-undocumented functions does **not** own the pre-existing docstrings
that happened to already sit in those files.

For every candidate finding, classify it against the diff (`git show <sha> --
<file>` / `git diff <base>...<head>`):

- **in-diff** — either (a) the docstring was *newly written* or *substantively
  reworded* by this change, **or** (b) the **code it documents changed
  substantially** (signature, behaviour, raised exceptions, return shape) even if
  the docstring text was left untouched. Case (b) matters most: a docstring
  *unchanged* on top of *changed* behaviour is the prime staleness vector — grade
  it against the new code precisely *because* the author didn't revisit it. These
  are the PR's work; the verdict is based on them.
- **pre-existing** — the defect predates the change: docstrings the diff didn't
  touch **and** whose documented code the diff didn't substantially change, plus
  lines the diff only *brushed* mechanically (a `"""` opener collapsed, a trailing
  period added (D400), a blank line removed). Neither a whitespace/reflow touch
  nor an incidental edit elsewhere in the file pulls a stale docstring into scope
  — only a substantive change to *that object's* code does.

Report both, but keep them in **separate sections** and base the verdict only on
in-diff findings. Pre-existing defects are surfaced as *optional* ("the author
may fix these while in the file, per leave-it-better — but they don't block").
Never let a pre-existing inaccuracy inflate the PR's verdict.

When reviewing a whole file on request (no diff), skip this — everything is in
scope.

### Single file / small diff (inline)

Read each changed object's code + docstring, apply `rubric.md`, and report
findings grouped by severity. Skip anything ruff already enforces (see the
rubric's "do NOT re-flag" list).

### Multi-file PR (fan-out)

For a diff spanning many files, fan out a `Workflow` so each region is graded in
parallel with a focused context. Shape:

1. **Guard phase (1 agent)** — read the *full diff* and answer one question: is
   this docstrings-only, or did logic change under cover of a docstring PR? List
   any non-docstring edits with file:line and whether they look in-scope. This
   is the highest-value correctness check on a "just docstrings" PR.
2. **Grade phase (N agents)** — partition changed files by directory; each agent
   reads code+docstring for its slice and returns findings in the `rubric.md`
   shape (structured output). Give every agent the convention detected in Step 0
   and the rubric inline. **Tell each agent to run `git show <sha> -- <file>` and
   set `scope` per finding** (`in-diff` vs `pre-existing`, per *Scope* above) — a
   docstring the diff only reflowed is `pre-existing`.
3. **Synthesise phase (1 agent / inline)** — dedupe, sort by severity, and write
   the output (below).

Skeleton (fill the file list and convention from Steps 0):

```js
export const meta = {
  name: 'docstring-review',
  description: 'Grade docstrings across a diff, guard against smuggled logic changes',
  phases: [{ title: 'Guard' }, { title: 'Grade' }, { title: 'Synthesise' }],
}
const RUBRIC = `...paste reference/rubric.md severities + finding shape...`
const CONVENTION = args.convention   // from Step 0
phase('Guard')
const guard = await agent(`Read this diff. Is it docstrings-only or did logic change? ...`, {schema: GUARD_SCHEMA})
phase('Grade')
const findings = (await parallel(args.partitions.map(p => () =>
  agent(`Convention: ${CONVENTION}. Grade docstrings in ${p.files.join(', ')} against:\n${RUBRIC}\nRead each object's code before grading.`,
        {phase: 'Grade', schema: FINDINGS_SCHEMA})))).filter(Boolean).flatMap(r => r.findings)
return { guard, findings }
```

Use the `Agent` tool directly (not Workflow) if the user hasn't opted into
multi-agent orchestration; the structure is the same, just sequential/manual.

## Output (review mode)

For a ticketed PR review, match the house location and write findings to
`docs/plans/tickets/reviews/<TICKET>.docstrings.md`:

- **Verdict** — one line: is the PR sound (docstrings-only, in-diff docstrings
  accurate)? Based on in-diff findings only.
- **Guard result** — docstrings-only, or list of logic changes found.
- **In-diff findings** — the PR's work. Table: object | location | severity |
  issue. This drives the verdict.
- **Pre-existing (optional)** — defects in touched files the diff didn't author
  (incl. reflow-only touches). Clearly marked non-blocking.
- **Detail** — only for in-diff Inaccurate/Incomplete items: rationale and fix.
- **Excellence** — docstrings worth calling out (sparingly).

**Hyperlink every code location** so the reader can click straight to it. Use a
GitHub blob URL pinned to the reviewed SHA (not `main` — line numbers drift):
`https://github.com/<org>/<repo>/blob/<sha>/<path>#L<line>`. Get `<org>/<repo>`
from `git remote -v` and `<sha>` from the commit under review. Link text is the
readable `path:line` — **never wrap link text in backticks** (Jira and many
markdown renderers can't render links inside code spans). Example:
`[services/discovery_service.py:386](https://github.com/findmypast/discoveries/blob/72802df/src/discoveries/services/discovery_service.py#L386)`.

For ad-hoc review, an inline summary in the same shape is fine. Don't post to
GitHub — that's the reviewer's call.

## When NOT to use

- Block comments / inline `#` comments — this skill is docstrings only.
- Prose docs, READMEs, design docs — that's `technical-writeup`.
- A pure bug/architecture review — use `peer-review` or `launch-deep-review`;
  this skill is the docstring lens, which those can defer to.
