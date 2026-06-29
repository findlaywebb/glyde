# ADR-NNN: <decision stated as the title, e.g. "Use a workflow, not an agent, for ticket triage">

- **Status:** Proposed | Accepted | Superseded by ADR-NNN | Deprecated
- **Date:** YYYY-MM-DD
- **Deciders:** <names / roles>
- **Tags:** #type/decision

> Title states the *decision*, not the topic. "Use Sonnet for the chat turn" — not "Model selection".

## Context

What's true that forces a decision now? The goal, the constraints, and what's explicitly out of scope. No solutions yet — just the situation. Pull in the scoped success criteria and constraints from `scope-ai-use-case`.

- Goal: <what we're trying to achieve>
- Binding constraint(s): <latency budget / cost ceiling / compliance / data residency / volume>
- Out of scope: <what this decision does NOT cover>

## Options considered

Two or three *real* alternatives, each described fairly (a straw man kills trust in the whole doc). Include "do nothing" if relevant.

1. **<Option A>** — <one-line description>
2. **<Option B>** — <one-line description>
3. **<Option C>** — <one-line description>

## Trade-offs

Score each option against the axes that matter. Put the *consequence* in each cell, not a grade ("$0.04/call", "p95 2.1s") — not ("good"/"bad").

| Option | Cost | Latency | Quality (eval) | Complexity | Risk |
|---|---|---|---|---|---|
| A | | | | | |
| B | | | | | |
| C | | | | | |

State which axis is the **binding constraint** — the one that actually decides it.

## Decision

The choice, with the reasoning *visible*. Tie it back to the binding constraint from Context.

> We chose **<X>** because, given <binding constraint>, the <cost/quality/etc.> of <Y> isn't justified here.

Name the strongest argument *against* the choice and why it didn't win — this is the highest-trust move with a sceptic:

> The case for <Y> is real: <its genuine upside>. We're not choosing it because <reason>.

## Consequences

What becomes true now — good and bad.

- **Easier:** <what this unlocks>
- **Harder / new cost:** <what we now have to build, operate, or accept>
- **Reversal trigger:** <the specific change that would make us revisit — "if volume 10x's, reconsider the agent">

## Links

- Architecture diagram: <link or embedded Mermaid>
- Eval that validates this: <link — see build-evals>
- Supersedes / superseded by: <ADR refs>
