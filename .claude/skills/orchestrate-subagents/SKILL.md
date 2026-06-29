---
name: orchestrate-subagents
description: Use when you (the main Claude Code agent) are deciding whether to delegate work to a sub-agent during a live session — a context-heavy investigation, several independent tasks you could run in parallel, mechanical work you could hand to a cheaper model, fanning out isolated code sections from a plan, or a fresh-context review of your own changes. Triggers include "use subagents for this", "parallelise this", "fan this out", "should I delegate this", "spin up agents to investigate X", "offload this to Sonnet", "don't bloat your context", or noticing you're about to read dozens of files into the main window. Embodies the scarce resource is the main context window; delegate proactively to keep every context lean, and let a written plan carry the shared decisions across the handoff.
---

# orchestrate-subagents

How the main orchestrator agent should use sub-agents *during interactive work* — the `Agent`/Task tool you reach for mid-session, not a product you're designing. The whole craft is knowing which work survives leaving the main context and which doesn't.

## The one principle

**Extra agents should contribute *intelligence*, not conflicting *actions*.** (Cognition, "Multi-Agents: What's Actually Working", 2026: *"multi-agent systems work best today when writes stay single-threaded and the additional agents contribute intelligence rather than actions."*) So: **parallelise reads, reviews, and attempts freely; keep writes single-threaded or strictly isolated; carry the shared decisions in a written plan; route everything through one integrator.** A sub-agent buys a fresh context window and parallelism, paid for in shared context, steerability, and ~15× tokens — worth it when the work is self-contained and returns a distillation, wasteful when it's coupled, iterative, or trivial.

Two axes decide every call below:
- **Read vs write.** Parallel *reading* can't conflict — investigation, review, best-of-N attempts are the safe, settled, universally-endorsed uses. Parallel *writing* is where the fragility lives: two agents make implicit, conflicting choices no merge reconciles (Cognition's original "Don't Build Multi-Agents" failure mode). It's not banned — it's *engineered*: a plan prescribes the cross-cutting decisions, **isolation** (worktrees / disjoint file ownership) prevents same-surface clobbering, and an integrator owns the merge. Absent those guards, keep writing single-threaded.
- **Context as the binding constraint.** *"The context window is the most important resource to manage"* (Claude Code best practices); performance rots as it fills. That's *why* you delegate — to keep each context lean. A near-full context is the worst place to hand off from, so delegate *proactively*, not at the redline.

> "Maximise a single agent first" is advice for *architecting a product*, not for running a session. The session question is "should I delegate this piece *now*?" — answered by the two axes above, not by complexity-minimisation.

## When to reach for orchestration

Default to a single agent doing the work directly. Escalate to delegation/fan-out when one context window provably can't carry the task — Boris Cherny's three failure modes of a single window (2026) are the cleanest trigger list:

- **Agentic laziness** — it stops before finishing (declares done at 20 of 50 items). → fan the items out.
- **Self-preferential bias** — it rates its own work generously when asked to verify against a rubric. → a *fresh-context* reviewer/judge that never saw the work.
- **Goal drift** — fidelity decays across turns, worst right after compaction. → separate, freshly-scoped contexts per goal.

Plus the everyday triggers: a context-heavy *read* you don't want in the main window, and *mechanical* work routable to a cheaper model. If none of these bite — *"if you could describe the diff in one sentence, skip the plan"* and just do it. Most tasks don't need five reviewers.

## The house pattern: plan-context → execute-context

Two clean orchestrator contexts in sequence, with a written plan as the handoff artifact between them. This is the default shape for any non-trivial coding task, and the 2026 consensus architecture (Cognition's "manager coordinates child agents", Anthropic agent teams, Cursor/Devin parallel agents all converge on it):

1. **Plan-context (Orchestrator 1).** Stays lean by delegating the *reading*: fan out research/investigation sub-agents (each with a four-part brief), each returns a 1–2k distillation. Orchestrator 1 synthesises and **writes the plan**. The plan's job is to prescribe the cross-cutting decisions (interfaces, naming, data shapes, **which files each section owns**) *upfront*, so they're no longer implicit. Cherny's rule: *"pour your energy into the plan so Claude can one-shot the implementation"* — he starts ~80% of tasks in plan mode.
2. **Execute-context (Orchestrator 2).** Starts fresh, reads the plan (not Orchestrator 1's full trace — the plan *is* the distilled, decision-bearing context). Fans out code sections to sub-agents, each briefed against the plan and **each owning a disjoint set of files** (and, for heavier work, its own git worktree — dispatch it with the `Agent` tool's `isolation: "worktree"`, which gives each sub-agent an isolated checkout so edits can't clobber each other and the conflict defers to integration). Orchestrator 2 owns integration: it ties the parts together and resolves the seams.

The three guards that make parallel writing safe here, all required together:
- **Plan** prescribes the shared decisions → no conflicting *cross-cutting* choices (the "share context" Cognition demands, supplied by prescription).
- **Isolation** (disjoint files / worktrees) → no concurrent edits to the same surface. The durable hard rule survives 2026: *two agents must never write the same file concurrently.*
- **Integrator** owns the merge and the seams → one coherent decision-maker at the join.

If the plan *can't* carve the work into file-disjoint sections, that's the signal the writing is genuinely coupled — keep it single-threaded (Cognition's standing default for writes). The residual risk even when it can (Cognition's open problem): a child agent discovers something that *should* change a sibling's work and can't tell it. The integrator catching that on merge, and re-planning, is the backstop.

The plan is a real file (e.g. `PLAN.md`), not a chat message — it survives the context boundary and doubles as the brief source for both the execute fan-out and a later fresh-context review.

## The three reasons to delegate (and what each demands)

1. **Context scope refinement** — the primary reason. Exploration reads many files; each consumes the main window and performance degrades as it fills. Send the read into a sub-agent's window; get back a 1–2k-token distillation (the worker may burn tens of thousands of tokens internally). Keeps the main conversation clean for the actual implementation.
2. **Parallel streaming** — independent subtasks run simultaneously. Real speedup *only when the paths don't depend on each other*. Scale the count to complexity: a simple lookup is 1 agent, not 5. Many agents each returning verbose results re-flood the context you were protecting.
3. **Defer to a cheaper model** — the main agent stays on Opus; route mechanical, well-bounded work (bulk edits, log grepping, test scaffolding, a fixed transform over a file list) to Sonnet or Haiku. The handoff must be tight enough that a smaller model can't misread it.

## Delegate when / keep in main when

**Delegate to a sub-agent when:**
- The task produces verbose output you won't reference again (search results, logs, file dumps).
- The work is self-contained and can return a summary.
- You want a fresh, unbiased context — especially to **review your own changes** (the writer shouldn't grade the work; a reviewer that sees only the diff + criteria judges it on its own terms).
- You want to enforce tool/permission restrictions on a risky step.
- The work is mechanical and routable to a cheaper model.

**Keep it in the main conversation when:**
- It needs frequent back-and-forth or iterative refinement.
- Multiple phases share significant context (planning → implementation → testing).
- It's a quick, targeted change — fresh-context startup cost outweighs the benefit.
- Latency matters — sub-agents start cold and must re-gather context.
- The decisions are coupled to decisions elsewhere in the task (see the write-fragility trap).

## The handoff brief — the highest-leverage thing you write

A vague brief is *the* dominant failure mode: *"research the semiconductor shortage"* is vague enough that sub-agents misinterpret the task or run the exact same searches as each other → duplicated work, gaps, no coverage. Every brief carries **four parts** (Anthropic's multi-agent research system):

1. **Objective** — the one question this agent answers / the one outcome it produces.
2. **Output format** — exactly what to return and how (a summary? a file list with line numbers? a verdict + findings?). This is what lands back in *your* context, so specify it tightly.
3. **Tools & sources** — where to look, which tools to use, what to ignore.
4. **Boundaries** — what's in scope, what's explicitly *not*, where to stop. Prevents the "infinite exploration" that defeats the purpose.

For parallel agents the boundaries also **partition the work** so two agents don't cover the same ground. Template: `templates/subagent-brief.md`.

## Gotchas

- **Two agents must never write the same file concurrently.** This is the one rule that survives every revision of the debate (2025 → 2026). Concurrent edits to a shared surface clobber or produce conflicting implicit choices no merge reconciles. Partition by file ownership, or isolate in worktrees. Parallelise writes only across *disjoint* surfaces, under a plan, with an integrator — never let the partition overlap.
- **"Clean handoff" does not by itself make parallel writes safe.** A plan removes *cross-cutting* conflicts (interfaces, naming); it does **not** give a sibling visibility into another's *in-flight local* decisions, nor surface a discovery that should change a sibling's work (Cognition's standing open problem). Isolation + integrator-on-merge is what covers that gap. If you can't partition cleanly, single-thread the writes.
- **The return-flood.** Sub-agents return into your context. Five agents each returning a verbose report re-bloats the window you delegated to protect. Demand distilled summaries, not transcripts — and stagger if the combined return is large.
- **You can't steer mid-flight.** Once a sub-agent is running you can't redirect it, and it can't coordinate with its siblings; you're blocked until it returns. Front-load the brief — there's no "actually, also check Y" after launch.
- **A vague one-line brief = duplicated work.** Worth its own line because it's the most common and most expensive mistake.
- **Sub-agents can't spawn sub-agents.** No nesting. For nested fan-out, chain them from the main conversation, or write a real `author-workflow` script.
- **The reviewer always finds something.** A fresh-context reviewer prompted to find gaps will report some even when the work is sound. Brief it to flag only gaps affecting correctness or the stated requirements, or you'll chase phantom findings into over-engineering.
- **Startup latency is real.** A sub-agent re-gathers context from cold. For a 30-second targeted edit, delegating is slower than just doing it.
- **Cost is ~15× a chat (≈4× for a single agent).** Token usage explains ~80% of quality variance, so it often pays — but only when task value justifies it and the work genuinely parallelises. Don't fan out routine work.

## Anti-patterns

- **Fanning out a coupled refactor** across parallel writers → conflicting implicit decisions, an unmergeable mess. Go linear.
- **Over-spawning** — 50 agents for a simple query, or 5 where 1 would do. Match count to complexity.
- **Delegating the thing you're actively iterating on** — back-and-forth work belongs in the thread that holds the context.
- **A summary-style brief** ("look into the auth stuff") instead of objective + format + sources + boundaries.
- **Treating it like a workflow.** Deterministic multi-stage fan-out with verification gates is a script, not ad-hoc delegation → `author-workflow`.

## When NOT to use this skill

- You're **designing an agent system / product** (the loop, tool surface, single- vs multi-agent architecture) → `design-agent`.
- You want a **deterministic, reusable multi-agent orchestration** (pipeline / parallel / loop-until-dry / adversarial-verify as a JS script) → `author-workflow`.
- You just want the mechanics of one obvious isolated investigation with no decision to make → just spawn it; you don't need a skill for that.

## Reference

- `reference/research-sources.md` — the first-class source digest this skill distills, current to 2026: Boris Cherny (Claude Code creator) on orchestration, plan-first, and worktrees; Cognition's *reversal-by-refinement* from "Don't Build Multi-Agents" (2025) to "Multi-Agents: What's Actually Working" (2026); Anthropic agent teams / sub-agents docs, multi-agent research system, context engineering; the Chroma context-rot study; Cursor / Devin / Amp / Factory / Google production patterns. Direct quotes, dates, the numbers, and URLs. Read it for the warrant behind a call, or where a claim is still genuinely contested vs settled.
