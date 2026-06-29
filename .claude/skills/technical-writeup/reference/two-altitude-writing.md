# Two-altitude writing

The core craft of this skill: explaining one idea so it lands for an engineer *and* a non-technical stakeholder. These aren't a "real" version and a "dumbed-down" version. They're two honest views of the same truth at different resolutions — the engineer needs the mechanism (precise, implementable), the stakeholder needs the decision (outcome, cost, trade-off).

## The two readers

| | Engineer | Stakeholder |
|---|---|---|
| **Decides** | how to build it | whether to fund / ship it |
| **Reads for** | mechanism, edge cases, failure modes, the API shape | outcome, cost, risk, timeline, the ask |
| **Trusts** | precision, named trade-offs, runnable code | clear outcome, honest downside, a number |
| **Bails when** | it's vague or hand-wavy | it's jargon they can't act on |
| **First sentence they want** | "It's an orchestrator-workers loop with a bounded retry." | "This cuts manual review time ~60% for about $0.04 a document." |

The mistake is writing one document for the average of these two people. That average reader doesn't exist. You end up with a doc too vague to build from and too technical to fund. Write two passages (or two sections, or a doc with a stakeholder summary up top and an engineering appendix below) — same subject, two altitudes.

## The moves

### 1. Lead with the decision/outcome, not the mechanism

For stakeholders especially, the first sentence is the outcome and why it matters. The mechanism comes later, if at all. People read top-down and bail early; spend the first line on the thing they came for.

- **Mechanism-first (loses them):** "Claude is a large language model that, given a prompt, predicts the most likely continuation token by token..."
- **Outcome-first (keeps them):** "We can auto-draft the first response to 70% of support tickets, leaving agents to review and send. The model handles the typing; the human keeps the judgement."

### 2. Translate the mechanism into a consequence

Engineers care that prompt caching reuses a KV prefix. Stakeholders care that it cuts cost and latency. Always carry the mechanism *through* to the consequence the reader cares about — don't stop at the mechanism and assume they'll do the translation.

### 3. "The model is not the product"

The single most useful framing for stakeholders (from the "Year of Building with LLMs" essay). The product is the *workflow around* the model: the retrieval, the validation, the human-in-the-loop, the fallback when it's unsure, the eval that proves it works. A stakeholder who thinks "we bought the model, we're done" will be disappointed; one who understands "the model is one component in a system we build and measure" will fund the right things. Lead non-technical readers here early.

### 4. Quantify, don't adjective

"Much faster", "very accurate", "cheap" are noise to both readers. "p95 latency 1.2s", "92% of extractions need no human edit", "$0.011 per call" are signal. If you don't have the number yet, say so — "we'll need an eval to confirm, but the rough order is..." — which is more credible than a confident adjective.

### 5. Name the downside (it's what makes you believable)

Both audiences trust a writer who volunteers the cost. For the stakeholder: "the trade-off is ~2s of latency and it'll be wrong about 1 in 20 times, which is why a human reviews the low-confidence ones." For the engineer: "this caps at ~30 tool calls before we bail; long-horizon tasks will hit that." Naming the downside up front disarms the sceptic and saves the meeting where they "discover" it.

## Worked before/after examples

### Concept: prompt caching

**Engineer altitude:**
> Prompt caching lets us mark a stable prefix (the system prompt + tool definitions, ~4k tokens here) with `cache_control`. On a cache hit, Anthropic skips re-processing that prefix: cached input tokens bill at ~10% of the base rate and don't re-incur the prefill latency. The prefix has to be byte-identical and the cache has a ~5-minute TTL, so we order the prompt stable-prefix-first (system, tools, few-shots) and put the variable user input last. With a 4k cached prefix on a 4.5k-token request, we cache ~89% of input.

**Stakeholder altitude:**
> Most of what we send Claude on every request is the same boilerplate (the instructions and the tool list). "Prompt caching" lets us pay full price for that once and a fraction of the price on every repeat for the next few minutes. For our traffic that's roughly a 40-50% cut in per-request cost and a faster first response, with no change to output quality. The catch: it only helps when requests share that boilerplate, which ours do.

Same fact. The engineer can implement it; the stakeholder can decide it's worth doing.

### Concept: "an agent"

**Engineer altitude:**
> An agent is an LLM running in a loop with tools: it reasons, emits a `tool_use` block, we execute it and return a `tool_result`, and it loops until it decides it's done or hits a stop condition (max turns / token budget / error). Unlike a fixed workflow, the *control flow is decided by the model at runtime* — which is the power and the risk. We bound it with a turn cap, a token budget, and a per-tool timeout.

**Stakeholder altitude:**
> An "agent" is Claude given a goal and a set of tools (search, the database, the ticketing API) and left to work out the steps itself, instead of us scripting every step in advance. It's more flexible — it can handle cases we didn't anticipate — but less predictable, so we put guardrails on how long it can run and check its work before anything reaches a customer. We use it only where the steps genuinely vary; where they don't, a fixed script is cheaper and safer.

### Concept: RAG vs fine-tuning

**Engineer altitude:**
> RAG supplies *knowledge* at inference time: we retrieve relevant chunks and put them in context, so the model answers from documents it's never seen in training. Fine-tuning changes *behaviour/format/style* by updating weights on labelled examples; it does not reliably teach new facts and it bakes them in (stale the moment the docs change). For a knowledge base that updates weekly, RAG is correct — re-index, no retrain. We'd fine-tune only to lock in a hard-to-prompt output format or tone, and only after prompt engineering and RAG are exhausted.

**Stakeholder altitude:**
> Two ways to make Claude expert in our domain. "RAG" is like giving it a search tool over our documents — it looks things up when answering, so when the docs change it's instantly up to date and there's no retraining bill. "Fine-tuning" is more like sending it on a training course — expensive, slower to update, and better at teaching a *style* than facts. For a knowledge base that changes every week, the search approach (RAG) is the right call. We'd only consider the training course later, for a specific tone or format we can't get any other way.

## A reusable shape for the composite doc

When one document must serve both, structure it as descending altitude:

```
1. One-line outcome            (stakeholder — the headline)
2. The decision + the trade-off (stakeholder — what we chose and gave up)
3. Cost / latency / risk        (stakeholder — the numbers)
4. The architecture diagram     (the hinge — both audiences read it)
5. How it works, in detail      (engineer — mechanism, edge cases)
6. Sample code / API shape       (engineer — implementable)
```

A stakeholder reads 1-4 and stops. An engineer skims 1-3 for context and lives in 4-6. Nobody has to read at the wrong altitude.

## Anti-patterns

- **The mushy middle** — one doc pitched at neither reader. Two passages beat one average.
- **Mechanism with no consequence** — explaining *how* prompt caching works to a VP without ever saying it saves money.
- **Adjectives instead of numbers** — "fast", "accurate", "cheap". Quantify or flag that you can't yet.
- **Hiding the downside** — a stakeholder doc with only upside reads as a sales pitch and a sceptic stops trusting it.
- **Jargon as a flex** — `tool_choice`, `top_p`, `KV cache` in a stakeholder doc. If a term doesn't change their decision, cut it or define it in five words.
- **Talking down** — the stakeholder altitude is *simpler*, not *condescending*. "The model is one part of a system we build and measure" respects the reader; "AI is like a smart robot brain" insults them.
