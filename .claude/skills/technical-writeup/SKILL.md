---
name: technical-writeup
description: Use when producing technical content that has to land with two audiences at once — architecture diagrams, trade-off / decision docs (ADRs), developer tutorials, sample code, and stakeholder one-pagers. Triggers include "write up this architecture", "draw an architecture diagram", "explain this for a stakeholder", "write a trade-off doc", "decision doc / ADR", "write a tutorial", "make a one-pager", "explain this for two audiences", "turn this design into docs". The core move: write the same idea at two altitudes — engineer (precise, implementable) and stakeholder (outcome, trade-off, cost) — and make the trade-offs explicit instead of asserting one right answer.
---

# technical-writeup

Turning a design into content that lands. Architecture diagrams, decision docs, tutorials, sample code, stakeholder one-pagers. The hard part is rarely the content. It's that the same artifact often has to convince a sceptical staff engineer *and* a VP who controls the budget, and those two people read for completely different things.

## The one principle

**Write at two altitudes.** The engineer needs the mechanism: which model, which retrieval strategy, what the agent loop looks like, where it can fail. The stakeholder needs the decision: what outcome this buys, what it costs, what you traded away, what you're asking for. Same idea, two renderings — not a dumbed-down version and a real version, but two honest views of one truth at different resolutions.

The corollary, and the thing that separates a trustworthy write-up from marketing: **make the trade-offs explicit.** Don't assert one right answer. Lay out the options, name what each costs (latency / quality / cost / complexity / risk), and *then* recommend — with the reasoning visible. A sceptical reader trusts a doc that argues against itself before it argues for itself. "Here's what we'd give up" earns more credibility than any confident claim.

## When to use

- Writing up a designed architecture for a customer or internal audience (diagram + narrative)
- A decision needs recording: model choice, RAG vs long-context vs fine-tune, agent vs workflow, build vs buy
- Producing a developer tutorial or sample code that someone else has to actually run
- A stakeholder asks "what is this, what does it cost, why this way?" and you need a one-pager
- Any time the request is "explain X for two audiences" or "make this presentable to leadership"
- Any brief that asks you to "document", "explain your design", or "write it up for the team"

## When NOT to use

- The artifact is a quick code comment, a PR description, or a Slack message — just write it, don't reach for the machinery
- You're still *scoping* the problem (what are we even building, is it worth it) → use the `scope-ai-use-case` skill first
- You're still *designing* the system (what's the agent loop, which patterns) → use the `design-agent` skill first
- You need to *measure* whether the thing works → use the `build-evals` skill. A write-up describes the system; an eval proves it. Don't let a beautiful diagram stand in for evidence.

A good write-up sits *downstream* of scoping and design and *alongside* evals. The strongest technical content ties all three together: here's the use case (scope), here's the architecture (design), here's how we know it works (evals).

## Pick the right artifact

The most common failure is reaching for the wrong format — a 12-page design doc when a diagram would do, or a diagram when the reader needed the cost number.

```
Reader needs to SEE the shape (components, flow, boundaries)?   → diagram        (reference/architecture-diagrams.md)
A decision needs recording + defending to engineers?           → ADR / trade-off (reference/tradeoff-docs.md)
A non-technical reader needs outcome + cost + the ask?         → one-pager       (templates/one_pager.md)
A developer needs to build/run the thing themselves?           → tutorial        (reference/tutorials-and-sample-code.md)
The same idea must reach both audiences?                        → write twice, two altitudes (reference/two-altitude-writing.md)
```

NB most real deliverables are a *composite*: a one-pager with a diagram embedded, or an ADR whose "options" section each carry a small Mermaid sketch. Pick the spine, then borrow.

## How to work

1. **Name the audience(s) and the one thing they must leave with.** Before writing a word: who reads this, and what is the single decision or action you want from them? If there are two audiences, write two altitudes, not one mushy middle.
2. **Lead with the decision/outcome, not the mechanism** — especially for stakeholders. "We're using a workflow, not an agent, which cuts cost ~4x and makes failures debuggable" before "here's the orchestrator-workers topology."
3. **Diagram at one level of abstraction.** One diagram answers one question. Don't mix a system-context view with a function-call trace. See `reference/architecture-diagrams.md`.
4. **Present trade-offs honestly.** Every option gets its real downside named. The recommendation comes *after* the options and shows its working. See `reference/tradeoff-docs.md`.
5. **Make code copy-pasteable and runnable.** Correct model IDs, real imports, no `...` in the critical path. See `reference/tutorials-and-sample-code.md`.
6. **Cut the bureaucracy.** No "The purpose of this document is to". No "shall"/"hereby". Lead with substance. (Vault style: natural, technical, direct; NB/parenthetical asides fine; no em-dashes.)

## Reference material (read on demand)

Each file stands alone; read the one the task needs.

- `reference/architecture-diagrams.md` — producing clean diagrams in Mermaid (renders in Obsidian, GitHub, most docs): which diagram type for which job, conventions (label edges, show trust boundaries, one abstraction level), and ready-to-use snippets (RAG pipeline, agent loop, orchestrator-workers, request flow with eval gate)
- `reference/two-altitude-writing.md` — the core craft: the same concept for engineers vs non-technical stakeholders, worked before/after examples (prompt caching, "an agent", RAG vs fine-tune), the "model is not the product" framing
- `reference/tradeoff-docs.md` — decision docs / ADRs: context → options → trade-offs (cost/latency/quality/complexity/risk) → decision → consequences; presenting a trade-off honestly to a sceptical engineering leader; worked model-selection / RAG-vs-long-context / agent-vs-workflow decisions
- `reference/tutorials-and-sample-code.md` — developer tutorials and sample code that runs: goal → prereqs → steps → verify → next, runnable minimal examples, progressive complexity, the copy-pasteable rule, Anthropic-flavoured (Messages API, correct model IDs, prompt caching)

## Templates

- `templates/architecture_decision_record.md` — fill-in ADR
- `templates/one_pager.md` — stakeholder one-pager (problem, approach, trade-offs, cost/latency, risks, ask)
- `templates/tutorial_skeleton.md` — developer tutorial skeleton
- `templates/diagrams.mmd` — ready-to-use valid Mermaid snippets (RAG, agent loop, orchestrator-workers, request flow with eval gate)

## Related skills

A write-up is the delivery layer of a chain:

- `scope-ai-use-case` — is this worth building, and what does success look like? (upstream)
- `design-agent` — what's the architecture, agent loop, and pattern choice? (upstream; the thing you diagram)
- `build-evals` — how do we know it works? (alongside; cite eval results in the doc, don't substitute a diagram for them). Its `scripts/` (`eval_harness.py`, `llm_judge.py`) are good exemplars of runnable sample code — point tutorials at them.

## Anti-patterns

- **One altitude for two audiences** — a stakeholder doc full of `tool_choice` and `max_tokens`, or an engineer doc that hand-waves the mechanism. Write twice.
- **Asserting one right answer** — "we use RAG" with no options considered and no trade-off named. A reviewer assumes you didn't consider alternatives. Show the fork in the road.
- **The diagram that explains nothing** — every box says "Service", no edge is labelled, three abstraction levels in one picture. A diagram is an argument, not decoration.
- **Sample code that doesn't run** — `...` in the load-bearing line, a hallucinated model ID, missing imports, no "here's how you know it worked" step. If you wouldn't paste it and hit run, neither will they.
- **Mechanism-first for stakeholders** — opening with "the orchestrator dispatches to workers" when the reader wanted "this cuts handle time 30% for ~$0.04/conversation." Lead with the outcome.
- **False certainty to a sceptic** — no risks, no "what we'd give up", no failure modes. Naming the downside is what makes the upside believable.
- **Bureaucratic throat-clearing** — "The purpose of this document is to outline..." Delete it and start with the point.
