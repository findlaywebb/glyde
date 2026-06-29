---
name: author-workflow
description: Use when authoring a Claude Code dynamic workflow — a JS orchestration script that fans out subagents (pipeline / parallel / loop-until-dry / adversarial-verify / tournament) for work too big or too verification-heavy for one context window. Triggers include "write a workflow", "create a workflow", "fan out agents", "orchestrate subagents", "parallelise this across agents", "ultracode this", "should this be a workflow". Embodies pipeline-by-default and adversarially-verify-before-you-trust.
---

# author-workflow

Author a dynamic workflow — a custom *harness* for one task, written as a JavaScript script that spawns and coordinates subagents. (Anthropic, "A harness for every task" / "Introducing dynamic workflows in Claude Code", 2025.) The default Claude Code loop is one context window doing everything; a workflow is the right move when that single window is the bottleneck.

## The one principle

**A workflow exists to beat the failure modes of single-context reasoning — agentic laziness, self-preferential bias, and goal drift.** It does that with fresh context windows (a clean agent can't get lazy or drift) and independent verification (an agent that didn't produce the work grades it, killing self-preference). If your task doesn't suffer from those, you don't need a workflow — the cost (often 10×+ the tokens of a normal session) isn't earned.

The second principle, mechanical but load-bearing: **pipeline by default.** `pipeline()` runs each item through all stages with no barrier between stages, so item A can be verifying while item B is still being reviewed. Reach for a barrier (`parallel()` between stages) *only* when a stage genuinely needs all prior results at once — dedup across the full set, an early-exit on zero, or a cross-item comparison. Most "I need to flatten/map first" is not a barrier; do the transform inside a stage.

## When to use

- Codebase-wide work: bug hunts, dead-code sweeps, large migrations, multi-file audits
- High-value answers that must be *right*: security review, root-cause investigation, anything you'll act on
- Deep research: fan-out sources, verify claims, synthesise a cited report
- Triage at scale: classify N items, dedup, act — especially on untrusted content
- Anything where you'd want a fresh model to refute the finding before you trust it
- The user said "ultracode", "use a workflow", "fan out agents", or invoked a skill that calls the Workflow tool

## When NOT to use

- A simple or routine coding task → just do it inline; a workflow is pure overhead
- The control flow is fixed and single-threaded → that's a plain script or one agent, not a fan-out
- You're deciding *whether* a problem needs an agent at all → use the `design-agent` skill (agent vs workflow vs one call)
- The user hasn't opted into multi-agent orchestration → **do not** call the Workflow tool; the user must explicitly ask (the tool fans out dozens of agents and costs a lot). Describe what a workflow could do and let them opt in.

## The shape of every workflow

A workflow script is plain JavaScript (not TypeScript) that starts with a pure-literal `export const meta = {...}` and then uses the runtime hooks. The skeleton, the hook reference, and the JS gotchas (no `Date.now()`/`Math.random()`, `args` is a real value not a JSON string, the 16-concurrency cap) are in `reference/workflow-mechanics.md`. A ready-to-edit starting point is in `templates/workflow_skeleton.js`.

The core decision is **which orchestration pattern**, and most real workflows compose several.

## The patterns

Full definitions, code, and the choose-by-task guidance are in `reference/orchestration-patterns.md`. The menu:

- **Pipeline** — items flow through stages independently, no barrier. The default. (`pipeline()`)
- **Fan-out + synthesise** — split into subtasks, run concurrently, merge. Barrier only at the merge. (`parallel()`)
- **Classify-and-act** — route each item by type to the right handler.
- **Adversarial verify** — N independent skeptics try to *refute* each finding; kill it unless it survives. The single highest-value pattern — it's what makes a workflow's output trustworthy. Use *perspective-diverse* verifiers (correctness / security / reproduce) when a finding can fail in more than one way.
- **Generate-and-filter / tournament** — produce many candidates, score them, keep the best (pairwise for tournaments).
- **Loop-until-dry** — keep spawning finders until K consecutive rounds surface nothing new; for unknown-size discovery where a fixed count would miss the tail.

## How to work

1. **Justify the workflow.** State which failure mode it beats (laziness / self-preference / drift) or which scale it handles. If you can't, stop — do it inline.
2. **Discover the work-list inline first, then orchestrate.** Often the right move is hybrid: scout (list the files, find the channels, scope the diff) in the main loop, *then* pipeline over the result. You don't need the shape before the task, only before the orchestration step.
3. **Pick the spine pattern, then compose.** e.g. fan-out finders → loop-until-dry → adversarial-verify each fresh finding.
4. **Use `schema` for any structured hand-off.** Pass a JSON Schema to `agent()` and it returns a validated object — no parsing, the model retries on mismatch. Vague subagent hand-offs are *the* dominant multi-agent failure.
5. **Default model = omit it.** Agents inherit the session model, which is almost always right. Only override when you're confident a tier fits (e.g. a cheap classifier).
6. **Budget tokens and never cap silently.** Scale fleet size to `budget`, and if you bound coverage (top-N, no-retry, sampling) `log()` what you dropped — silent truncation reads as "covered everything".
7. **Persist the script and iterate by editing it.** Every run writes the script to disk and returns its path; edit that file and re-invoke with `scriptPath` + `resumeFromRunId` rather than resending. See `reference/workflow-mechanics.md` on resume.
8. **Save good workflows as skills.** A workflow that proves its worth becomes a reusable harness — wrap it in a skill (use `make-skill`) so it's a one-word invocation.

## Reference material (read on demand)

- `reference/workflow-mechanics.md` — the `meta` block, the hooks (`agent`/`pipeline`/`parallel`/`log`/`phase`/`workflow`/`args`/`budget`), `schema` for structured output, worktree isolation, resume/`resumeFromRunId`, concurrency cap, and the JS-not-TS gotchas.
- `reference/orchestration-patterns.md` — every pattern with runnable code, when each applies, and the pipeline-vs-barrier decision spelled out with the smell test.

## Templates

- `templates/workflow_skeleton.js` — a minimal valid workflow (meta + a pipeline with a review stage and an adversarial-verify stage) to copy and edit.

## Related skills

- `design-agent` — the upstream decision: is this one call, a workflow, or an agent? Come here once "it's a workflow" is settled.
- `make-skill` — wrap a proven workflow as a reusable skill.
- `build-evals` — adversarial verification is a runtime check; to *measure* a harness's quality over time, build an eval.

## Gotchas

- **Calling the Workflow tool without the user's opt-in.** It spawns dozens of agents and burns tokens. Requires explicit opt-in ("ultracode", "use a workflow", a skill that calls it). When unsure, describe and offer — don't launch.
- **`parallel()` where `pipeline()` belongs.** The classic over-barrier: a middle `transform()` between two `parallel()` calls that has no cross-item dependency. Wall-clock suffers for nothing. Put the transform inside a pipeline stage.
- **Looping on `confirmed` instead of `seen` in loop-until-dry.** Dedup against *everything seen*, not just confirmed findings — else judge-rejected items reappear every round and the loop never converges.
- **Trusting the agent that did the work to grade it.** Self-preferential bias is real. The verifier must be a *separate* agent prompted to refute, defaulting to "refuted" when uncertain.
- **`Date.now()` / `Math.random()` / argless `new Date()` in the script.** They throw (they'd break resume). Pass timestamps via `args`; vary by index for pseudo-randomness.
- **Forcing a model tier you're not sure about.** Omit `model` and inherit the session model unless you have a clear reason.

## Anti-patterns

- **A workflow for a task one agent handles.** Overhead, latency, and token cost with no payoff. Name the failure mode it beats or don't reach for it.
- **No verification stage on a high-value answer.** The whole point of a workflow is that a fresh model checks the work. Skipping verify throws away the main benefit.
- **Silent truncation.** Bounding coverage without `log()`-ing what was dropped. Reads as complete when it isn't.
- **Knowing the shape before the task.** You don't have to — scout inline, then orchestrate over what you found.
