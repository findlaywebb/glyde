# Trade-off docs and ADRs

How to record a decision so a sceptical engineering leader trusts it. The format is the Architecture Decision Record (ADR): a short, dated document that captures *context → options → trade-offs → decision → consequences*. The discipline is honesty: present the trade-off, don't assert a verdict. The doc that argues against itself before it argues for itself is the one people believe.

## Why ADRs (not a wiki page, not a Slack thread)

A decision made in a meeting and never written down gets relitigated every time a new engineer joins or the original reasoning is forgotten. An ADR is the immutable record: *here's what we knew, here's what we chose, here's why, here's what it cost us.* It's dated and append-only — you don't edit an old ADR, you write a new one that supersedes it. That history is the point: six months later "why did we pick Sonnet over Opus here?" has a one-paragraph answer instead of an archaeology project.

Keep them short. An ADR is one to two pages. If it's longer, it's a design doc with an ADR buried in it — split them.

## The structure

Use `templates/architecture_decision_record.md` to fill in. The sections:

1. **Title + status.** `ADR-007: Use a workflow, not an agent, for ticket triage` — `Status: Accepted` (or Proposed / Superseded by ADR-012 / Deprecated). The title states the *decision*, not the topic.
2. **Context.** What's true that forces a decision now? Constraints (latency budget, cost ceiling, compliance, data residency), the goal, and what's *out* of scope. No solutions yet — just the situation. This is where you pull in the output of `scope-ai-use-case`.
3. **Options considered.** The real alternatives, including "do nothing" where relevant. Each gets a fair description — if an option is a straw man, the reader stops trusting the whole doc. Two or three is usually right; one means you didn't decide anything.
4. **Trade-offs.** The heart of it. Score each option against the axes that matter (below). A small table beats prose. Name what each option *costs*, not just what it gives.
5. **Decision.** The choice, and the reasoning *visible*. "We chose X because, given the latency budget is the binding constraint, the 4x cost of Y isn't justified by its quality edge here." Tie the decision back to the context's constraints.
6. **Consequences.** What becomes true now — good and bad. What we've made easy, what we've made hard, what we'll have to revisit, and *the trigger that would make us change our mind* ("if volume 10x's, revisit the agent option").

## The trade-off axes

For an AI/LLM system, almost every decision moves along these five. Make them explicit:

| Axis | The question |
|---|---|
| **Cost** | $ per request / per task, at expected volume. Include the model tier, retries, and caching. |
| **Latency** | p50 / p95 on the critical path. Does it meet the interaction's budget (chat vs batch)? |
| **Quality** | accuracy / faithfulness / pass-rate on the eval that matters. Cite the number or flag it's TBD. |
| **Complexity** | how much there is to build, operate, and debug. Complexity is a recurring tax, not a one-off. |
| **Risk** | failure modes, blast radius, reversibility, compliance/safety exposure. |

A clean trade-off table puts options as rows and these as columns, with a short honest cell in each. Don't fill cells with "good/bad" — fill them with the actual consequence ("~$0.04/call", "p95 2.1s", "needs a vector store + reranker to operate").

## Presenting honestly to a sceptic

A sceptical engineering leader has seen confident docs be wrong. What earns their trust:

- **Lead with the binding constraint.** Say which axis decides it. "Latency is the constraint; everything else is secondary here." It shows you know what actually matters and stops the reader hunting for the catch.
- **Name the strongest argument *against* your choice.** "The case for the agent is real: it'd handle the long tail we're punting on. We're not choosing it because..." This is the single highest-trust move. A reviewer who sees their objection already addressed relaxes.
- **Quantify or admit you can't.** "We'll need an eval to confirm the quality delta; the rough order is..." beats a confident unfounded number. Sceptics smell made-up precision.
- **Show the reversal trigger.** "If X happens, this decision flips." Decisions with a stated expiry are trusted more than ones presented as permanent.
- **Don't hide complexity cost.** If your choice adds a vector DB, a reranker, and an eval pipeline to operate, say so. The reader will find out anyway; better they hear it from you.

## Worked decisions

### 1. Model selection (Opus vs Sonnet vs Haiku)

**Context:** real-time chat assistant, p95 latency budget 2.5s, ~500k requests/day, quality bar = "resolves without escalation 80% of the time" on our eval set.

| Option | Cost (rel.) | Latency | Quality (eval) | Notes |
|---|---|---|---|---|
| Opus | highest | slowest | highest | over-budget on latency at this volume; quality headroom we don't need |
| Sonnet | mid | within budget | meets bar | the fit |
| Haiku | lowest | fastest | below bar on multi-step turns | great for the classify-the-intent first hop |

**Decision:** Sonnet for the main turn; Haiku for a cheap intent-classification pre-step. **Reasoning:** latency is the binding constraint, which rules Opus out regardless of its quality edge; Sonnet clears both latency and the quality bar; the Haiku pre-step shaves cost on the easy turns. **Reversal trigger:** if the eval bar rises to "90% resolution" and Sonnet can't hit it after prompt/RAG work, revisit Opus and renegotiate the latency budget. (The "start-cheap-and-upgrade vs start-capable-and-optimise-down" strategies from Anthropic's model-selection doc are the framing here — and the upgrade decision is gated on an eval, see `build-evals`.)

### 2. RAG vs long-context vs fine-tune

**Context:** answer questions over a 4,000-document knowledge base that updates weekly; answers must cite sources; freshness matters.

| Option | Cost / latency | Quality | Complexity | Risk |
|---|---|---|---|---|
| **RAG** | low (only relevant chunks in context) | high if retrieval is good; citations natural | mid (vector store, chunking, reranker, retrieval eval) | retrieval miss → wrong/empty answer |
| **Long-context** (stuff docs in the prompt) | high cost + latency at 4k docs; won't fit anyway | high *if* it fits | low to build | doesn't scale past context window; expensive per call |
| **Fine-tune** | training cost; cheap inference | poor for *facts*; can't cite; stale on every update | high (data prep, retrain pipeline) | bakes in stale knowledge; weekly retrain |

**Decision:** RAG. **Reasoning:** the corpus is far too large for long-context and changes weekly, which fine-tuning handles badly (you'd retrain weekly and still couldn't cite). RAG re-indexes cheaply on update and gives citations for free. **Consequence:** we now own a retrieval pipeline and must eval *retrieval* separately from generation (a retrieval miss looks like a model failure but isn't). **Reversal trigger:** if the corpus shrinks to fit comfortably in context and freshness stops mattering, long-context becomes simpler. (Adaptation-hierarchy framing: exhaust prompt → RAG → agent before fine-tuning, per Huyen.)

### 3. Agent vs workflow

**Context:** invoice processing — extract fields, validate against a PO, flag mismatches. The steps are the *same every time*.

| Option | Predictability | Cost | Debuggability | When it wins |
|---|---|---|---|---|
| **Workflow** (fixed DAG of LLM calls) | high — same path every run | low — exactly the calls needed | easy — fixed steps, clear failure point | when the steps don't vary |
| **Agent** (LLM decides steps in a loop) | lower — model chooses the path | higher — variable tool calls, retries | harder — non-deterministic trajectory | when the steps genuinely vary per input |

**Decision:** Workflow (prompt-chaining: extract → validate → flag). **Reasoning:** the task has a fixed, known structure; an agent's runtime flexibility buys nothing here and costs predictability, money, and debuggability. **Consequence:** new invoice formats that break the fixed extractor need a code change, not "the agent figures it out" — an acceptable cost for the predictability. **Reversal trigger:** if we expand to dozens of unpredictable document types where the steps truly vary, revisit an agent. (This is the "start simple, earn the complexity" thesis from Anthropic's *Building Effective Agents* — see the `design-agent` skill for the full decision.)

## Anti-patterns

- **Straw-man options** — one real choice and two obviously-bad ones. The reader sees through it and discounts the whole doc.
- **A decision with no consequences section** — every choice closes some doors; not naming them reads as not having thought about them.
- **No reversal trigger** — decisions framed as permanent are less trusted than ones with a stated expiry.
- **Adjective trade-offs** — a table full of "good/medium/bad" instead of "$0.04/call, p95 2.1s". Score with consequences, not grades.
- **Burying the binding constraint** — making the reader infer which axis actually decided it. Say it.
- **Editing old ADRs** — they're a dated record. Supersede with a new one; don't rewrite history.
