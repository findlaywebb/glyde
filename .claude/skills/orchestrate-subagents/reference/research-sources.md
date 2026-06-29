# Research sources — sub-agent delegation, first-class only (current to 2026)

The warrant behind `orchestrate-subagents`. The debate that ran 2024–2025 ("is multi-agent coding a good idea?") was largely *resolved by the principals themselves* in 2026: the answer is a specific architecture, not a yes/no. This digest leads with the 2026 sources that settle it, then keeps the 2025 foundations they build on. First-class only — frontier labs, the serious coding-agent companies, and named engineers. Where a claim is still contested, it's flagged.

## The 2026 consensus, in one line

**Parallelise reads / reviews / attempts freely; keep writes single-threaded or strictly file-isolated; carry shared decisions in a written plan; route everything through one integrator.** Every major vendor converged here independently.

---

## Boris Cherny (creator & lead of Claude Code, Anthropic) — 2026

The highest-value source: he designed the subagent system. His arc is *not* a reversal — it's "stay simple by default, escalate to orchestration only when one context window provably fails."

- **Why subagents exist (two reasons, his words, 31 Jan 2026):** *"Append 'use subagents' to any request where you want Claude to throw more compute at the problem"* and *"Offload individual tasks to subagents to keep your main agent's context window clean and focused."* (compute + context hygiene)
- **Context is the binding constraint** (team-authored Claude Code best practices, current): *"Claude's context window fills up fast, and performance degrades as it fills… The context window is the most important resource to manage."* His operational tip: context rot bites ~300–400k tokens; force earlier compaction.
- **Parallel coding agents — endorsed, via isolation** (20 Feb 2026): *"built-in git worktree support… Now, agents can run in parallel without interfering with one another. Each agent gets its own worktree and can work independently."* He calls multiple parallel sessions *"the single biggest productivity unlock, and the top tip from the team"*; runs ~5 agents at once.
- **Plan-first** (Feb 2026, Lenny's Podcast / his tips): *"I start about 80% of my tasks in plan mode."* *"Pour your energy into the plan so Claude can one-shot the implementation."* *"have one Claude write the plan, a second Claude review as a staff engineer."*
- **When to escalate — the three single-window failure modes** (Workflow/Dynamic-Workflows posts, May–Jun 2026): orchestration is justified when a single context window hits **(a) agentic laziness** (stops at 20 of 50 items), **(b) self-preferential bias** (rates its own work generously against a rubric), **(c) goal drift** (fidelity decays across turns, worst after compaction). Fix: *"a workflow orchestrates separate Claudes, each with its own context window and focused, isolated goal."*
- **Discipline / don't over-orchestrate:** *"Most traditional coding doesn't need 5 reviewers"*; *"explicitly request [subagents] for 40-file refactors, don't for a single function."* And the design philosophy: *"don't try to box the model in… give the model tools and a goal"*; *"build for the model six months from now, not the model of today."*

Sources: howborisusesclaudecode.com (verbatim aggregation of his X/Threads tips, dated); code.claude.com/docs/en/best-practices; Lenny's Podcast (19 Feb 2026); Latent Space (8 May 2025, the early "do the simple thing first" version).

---

## Cognition — the reversal-by-refinement (the single most important pair)

The original critic updated its own thesis. This is what makes the skill's "it's architecture, not prohibition" stance first-class, not wishful.

- **"Don't Build Multi-Agents" (Walden Yan, Jun 2025)** — cognition.ai/blog/dont-build-multi-agents. The failure mechanism, still valid: *"Actions carry implicit decisions, and conflicting decisions carry bad results."* Default remedy: *"just use a single-threaded linear agent."* Crucially it already flagged the limit as *capability, not principle*: parallelism *"will unlock"* as single agents get better at communicating. The diagnosis names the cause as conflicts *"not prescribed upfront"* — which is exactly what a plan addresses.
- **"Multi-Agents: What's Actually Working" (Apr 2026)** — cognition.ai/blog/multi-agents-working. The update: *"we've begun to deploy multi-agent systems that actually work in practice."* The governing principle: ***"multi-agent systems work best today when writes stay single-threaded and the additional agents contribute intelligence rather than actions."*** Three patterns they now ship: a **code-review loop** (*"Devin Review catches an average of 2 bugs per PR, of which roughly 58% are severe"* — and *"the review agent having a completely clean context… helps it go deeper"*), a cross-model **"smart friend"** consult, and **manager-child delegation** (*"A manager Devin can break a larger task into pieces, spawn child Devins… and coordinate their progress"*). Still hard / still open: *"Share as much context as possible… (todo list, plan files)"*; the open problems are *"all communication problems… How does a child agent surface a discovery that should change its siblings' work?"*; and *"the unstructured-swarm approach… is mostly a distraction."*
- **Managed Devins (Mar 2026)** — parallel agents in production, via **isolation + a coordinator**: *"The main Devin session acts as a coordinator: it scopes the work, assigns each piece to a managed Devin, monitors progress, resolves any conflicts, and compiles the results,"* each child *"running in its own isolated virtual machine."* Nubank: a migration across 100k+ implementations, "18-month project into weeks."

The pair is the spine of the skill: the failure mode is real (don't naively parallel-write), and the fix is architectural (plan + isolation + integrator), now endorsed by the people who raised the alarm.

---

## Anthropic — the foundations and the team feature

- **Multi-agent research system (Jun 2025)** — anthropic.com/engineering/multi-agent-research-system. The **four-part brief** (still the crispest delegation rule): *"Each subagent needs an objective, an output format, guidance on the tools and sources to use, and clear task boundaries."* Vague briefs → *"spawning 50 subagents for simple queries… distracting each other."* And the coding caveat (agrees with Cognition): *"most coding tasks involve fewer truly parallelizable tasks than research, and LLM agents are not yet great at coordinating… in real time."* Cost: agents ~4× chat tokens, multi-agent ~15×; token usage explains ~80% of quality variance.
- **Claude Code best practices (current)** — the context-as-constraint framing; the "infinite exploration" failure; **explore → plan → code → commit**; the SPEC.md → *fresh session* handoff (*"Time spent making the spec precise pays off more than time spent watching the implementation"*); Writer/Reviewer (*"a fresh context improves code review since Claude won't be biased toward code it just wrote"*); *"if you could describe the diff in one sentence, skip the plan."*
- **Sub-agents docs** — **"Chain subagents"** is a named, recommended pattern: *"ask Claude to use subagents in sequence. Each subagent completes its task and returns results to Claude, which then passes relevant context to the next."* Hard limit: *"Subagents cannot spawn other subagents."* Prefer the **main conversation** when *"multiple phases share significant context"* or work *"needs frequent back-and-forth."*
- **Agent teams (experimental, ~Feb 2026)** — teammates each with own context, a mailbox + file-locked shared task list. Explicitly steers *away* from parallel writes: *"Two teammates editing the same file leads to overwrites. Break the work so each teammate owns a different set of files"*; *"Start with research and review… tasks that have clear boundaries and don't require writing code."*
- **Effective context engineering (2025)** — the distillation ratio: a subagent *"might explore extensively, using tens of thousands of tokens… but returns only a condensed… summary (often 1,000-2,000 tokens)."* Origin of the "context rot" framing.

---

## The wider field (2026) — independent convergence

- **Chroma, "Context Rot" (Jul 2025)** — trychroma.com/research/context-rot. Empirical backing for "delegate before the redline": across 18 models, *"performance grows increasingly unreliable as input length grows,"* degrading *well before* the window is full. This is *why* a near-full context is a bad place to hand off from.
- **Cursor 2.0 (Oct 2025)** — *"run many agents in parallel without them interfering… powered by git worktrees or remote machines"*; best-of-N (*"having multiple models attempt the same problem and picking the best result"*); Plan Mode; "give each agent an explicit list of directories it owns and must not touch."
- **Sourcegraph Amp (May 2026)** — the sharpest handoff-quality line: ***"Sub-agents amplify whatever context layer the parent has. Bad context yields parallel wrong answers faster."*** Defaults to parallel for independent work, serialises on shared contract; the "oracle" second-opinion agent on a stronger model.
- **Factory.ai droids; Google Antigravity / Jules (2026)** — coordinator/manager decomposes → role- or task-specialised agents → verification loop. Same shape: lead + isolation + verify.
- **Caution, named:** Simon Willison's *"parallel agent psychosis where I've lost a whole feature"* (Feb 2026) — ungoverned parallelism bites real engineers. Isolation + integrator is the governor.

---

## What's settled vs still contested (2026)

| Pattern | Verdict |
|---|---|
| Read-only investigation subagents | **Settled / universal.** No writes to conflict; pure context compression. |
| Sequential / chained subagents | **Settled.** Documented Anthropic pattern; orchestrator distills between steps. |
| Parallel reviews / best-of-N attempts | **Settled.** Fresh context is a feature (unbiased grading). |
| Parallel code-*writing* agents | **Mainstream — but only with isolation (worktrees/VMs or disjoint files) + a plan + an integrator.** Free parallel writes to a shared surface: rejected by everyone, including 2026 Cognition. |
| "A good plan alone makes concurrent writes safe" | **Still false.** The plan handles cross-cutting decisions; isolation handles same-surface clobbering; the integrator handles the residual discovery-that-should-change-a-sibling gap. All three needed. |

## The synthesis the skill encodes

1. In a session, delegate *proactively* to keep contexts lean (Boris/Anthropic/Chroma) — not "single agent first," which is design-time advice.
2. **Extra agents contribute intelligence, not conflicting actions** (Cognition 2026). Read/review/attempt in parallel; serialise or isolate writes.
3. Context isolation is the main *why* — delegate the verbose read, keep the 1–2k summary.
4. The four-part brief (objective / format / tools+sources / boundaries) is the highest-leverage rule; bad briefs amplify under parallelism (Sourcegraph).
5. Parallel writing = **plan + isolation + integrator**, all three; never two agents on one file.
6. Escalate to orchestration on Boris's three single-window failure modes (laziness / self-preference / drift); otherwise stay simple.
7. ~15× token cost — only when task value is high and the work genuinely parallelises.
