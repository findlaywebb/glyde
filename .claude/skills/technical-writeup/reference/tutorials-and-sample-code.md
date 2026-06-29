# Tutorials and sample code

Developer content lives or dies on one thing: does the code run when they paste it? A tutorial whose sample fails on line 12 burns more trust than no tutorial at all, because now the reader doubts everything else you wrote. This file covers the structure of a tutorial that gets someone to a working result, and the rules for sample code that survives copy-paste.

## Know which thing you're writing (Diátaxis)

The Diátaxis framework (Procida) splits developer docs into four modes that serve different needs. Mixing them is the most common reason docs feel bad:

| Mode | Serves | Shape |
|---|---|---|
| **Tutorial** | learning | a guided lesson; you hold their hand to a working result |
| **How-to** | a task | recipe for a specific goal; assumes competence |
| **Reference** | looking-up | exhaustive, dry, accurate (API docs) |
| **Explanation** | understanding | the "why" and the context (this is closer to `two-altitude-writing.md`) |

This file is mostly about the **tutorial** (learning-oriented) and the sample code inside it. Don't try to make one document do all four — a tutorial that keeps stopping to enumerate every parameter (reference) loses the learner. Link out to reference instead.

## Tutorial structure

A tutorial is a promise — "follow these steps and you'll have a working X" — kept. The reliable shape:

```
1. What you'll build   — one sentence + ideally a screenshot/output of the end state
2. Prerequisites       — exact versions, accounts, keys; what they need before step 1
3. Steps               — numbered, each one verifiable, smallest-that-works first
4. Verify it works     — how they KNOW it worked (expected output, a test to run)
5. Troubleshooting     — the 3-4 errors they'll actually hit, and the fix
6. Next steps          — where to go to extend it (link to how-to / reference)
```

Use `templates/tutorial_skeleton.md` for the fill-in.

### What you'll build

Lead with the end state. Show the output, the screenshot, the thing they'll have. A reader decides whether to invest the next 20 minutes based on this. "By the end you'll have a CLI that answers questions over your PDFs with citations" + a sample of that output beats "This tutorial covers RAG."

### Prerequisites

Be ruthlessly exact. Not "Python and an API key" but "Python 3.10+, an Anthropic API key (`ANTHROPIC_API_KEY`), and `pip install anthropic`". The number one cause of a failed tutorial is an unstated prerequisite. State versions; pin them in the snippets if it matters.

### Steps

- **Numbered and small.** Each step does one thing and the reader can check it before moving on.
- **Smallest-that-works first.** Get them to a running (if trivial) result fast — a single API call that returns text — *then* layer complexity. Time-to-first-success is the metric. A reader who sees output in 90 seconds keeps going; one who's still configuring at minute 15 leaves.
- **Progressive complexity.** Start with the happy path and hardcoded values. Add error handling, then streaming, then caching, then tools — each as its own step, each still runnable. Don't open with the production-grade version; build up to it.
- **Show the output after each meaningful step.** "You should see:" followed by the actual expected output. It's how they self-verify without running to you.

### Verify it works

Never end a tutorial at "and that's it!" End at "run this; you should see *exactly this*." Give them a concrete check — expected stdout, a one-line test, a curl that returns 200. If there's no verification step, the reader never knows if they succeeded, and a tutorial that can't be checked is a blog post.

### Troubleshooting

List the real errors, not hypothetical ones. `AuthenticationError` (key not set / wrong env var), `RateLimitError` (back off / lower concurrency), `model: not found` (wrong model ID), import errors (wrong package version). Three or four real ones with the exact fix saves you the support thread.

## The copy-pasteable rule

**If you wouldn't paste it into a fresh shell and hit run, don't ship it.** Concretely:

- **No `...` in the load-bearing line.** Ellipsis for *omitted boilerplate* the reader already has is fine; ellipsis where the actual API call should be is a trap. Show the real call.
- **Real, current model IDs.** `claude-opus-4-8`, `claude-sonnet-4-6`, `claude-haiku-4-5` — never `claude-3-opus-latest`-style guesses or invented IDs. A wrong model ID fails on the first run and reads as carelessness. (Check the current model list before shipping; IDs change.)
- **Complete imports and setup.** The snippet runs from a clean file. If it needs `import os` and `from anthropic import Anthropic`, they're in the snippet.
- **No hidden state.** If step 4 depends on a variable from step 2, either repeat it or make the dependency explicit. Readers copy individual blocks.
- **Keys from the environment, never inline.** `client = Anthropic()` (reads `ANTHROPIC_API_KEY`) — never a literal key in the sample. Modelling the secure pattern is part of the lesson.
- **Pin what breaks.** If the SDK's surface changed across versions, say which version the snippet targets.

A good test: hand the snippet to someone who hasn't read the prose and see if they get output. If they can't, it's not done.

## Anthropic-flavoured sample code

The minimal, correct, copy-pasteable Messages call — the spine of almost every Claude tutorial:

```python
import os
from anthropic import Anthropic

client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment

resp = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system="You are a concise technical assistant.",
    messages=[
        {"role": "user", "content": "Explain prompt caching in two sentences."},
    ],
)

print(resp.content[0].text)
```

Then a *progressive* next step the reader can actually run — adding **prompt caching** to a stable prefix (the highest-leverage cost lever, and a thing every Anthropic tutorial should model):

```python
# A large, stable prefix (instructions + reference material) reused across calls.
# Marking it cache_control means we pay full price once and ~10% on cache hits
# for the next few minutes (~5-min TTL), with no change to output.
resp = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": LONG_STABLE_INSTRUCTIONS,   # the byte-identical, reused part
            "cache_control": {"type": "ephemeral"},
        },
    ],
    messages=[{"role": "user", "content": user_question}],  # the variable part, last
)

usage = resp.usage
print(f"cache write: {usage.cache_creation_input_tokens}  "
      f"cache read: {usage.cache_read_input_tokens}  "
      f"uncached: {usage.input_tokens}")
```

The `usage` print is doing tutorial work: it's the **verify-it-works** step for caching — on the second identical-prefix call the reader should see `cache_read_input_tokens` jump and `input_tokens` drop, which proves the cache hit. (See the `claude-api` skill for the full caching playbook.)

Conventions for Claude samples specifically:
- Show `max_tokens` explicitly — it's required and a common omission.
- Access text as `resp.content[0].text` (the content is a list of blocks), not `resp.text` — the latter is a frequent reader mistake worth pre-empting.
- For tool use, show the full round-trip: the `tool_use` block out, your execution, the `tool_result` block back in. A half-shown tool loop doesn't run.
- Keep secrets in the environment; model the secure pattern even in a toy example.

## Cross-link runnable exemplars

Point readers at sample code that's already runnable rather than re-deriving it. Good in-vault exemplars:

- `build-evals` → `scripts/eval_harness.py` (async eval runner), `scripts/llm_judge.py` (calibrated judge with order-swap + prompt-cached rubric), `scripts/stats.py` (bootstrap CIs). Dependency-light, runnable standalone, with a usage header — the shape to imitate.
- `design-agent` → its agent-loop scripts for the tool round-trip pattern.

When you write a tutorial that touches evals or agents, link these rather than inlining a worse version — and note the header-comment-as-usage convention they follow (every script's first lines say how to run it).

## What a careful reader presses on

- "Run it." — readers will paste your sample. It has to work. Real model ID, complete imports, no `...`.
- "What happens on a rate limit / auth failure?" — your troubleshooting section should already answer it.
- "How does the reader know it worked?" — if you can't point to the verify step, the tutorial isn't finished.
- "Why this model / why caching here?" — sample code implies decisions; be ready to defend them as trade-offs (see `reference/tradeoff-docs.md`).

## Anti-patterns

- **Sample code that doesn't run** — the cardinal sin. `...`, fake model IDs, missing imports, hidden state between blocks.
- **No verify step** — ending at "and that's it!" with no way to confirm success.
- **Opening with the production version** — error handling, retries, and abstraction before the reader has seen a single result. Start trivial, build up.
- **Mixing Diátaxis modes** — a tutorial that detours into exhaustive reference, or a how-to that explains theory. Pick one mode, link the others.
- **Inline secrets** — a literal API key in a snippet teaches the wrong habit and leaks if copied.
- **Hypothetical troubleshooting** — listing errors nobody hits while omitting the auth error everybody hits.
