# <Tutorial title — "Build a <thing> with Claude">

> Learning-oriented (Diátaxis tutorial mode): hold the reader's hand to a working result. Keep reference and theory out — link to them instead. Every code block must run if pasted into a fresh file. Real model IDs, complete imports, no `...` in the load-bearing line.

## What you'll build

One sentence describing the end state, plus a sample of the output (a screenshot, the expected stdout, the artifact). This is what makes the reader commit the next 20 minutes.

```
<paste the actual end-state output here>
```

## Prerequisites

Be exact — unstated prerequisites are the #1 cause of a failed tutorial.

- <Language + version, e.g. Python 3.10+>
- `pip install anthropic` (version <x> if it matters)
- An Anthropic API key set as `ANTHROPIC_API_KEY`
- <any account / data / service needed before step 1>

## Step 1 — <smallest thing that produces a result>

Get them to output fast (time-to-first-success). One runnable block, then show what they should see.

```python
import os
from anthropic import Anthropic

client = Anthropic()  # reads ANTHROPIC_API_KEY

resp = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=512,
    messages=[{"role": "user", "content": "<minimal prompt>"}],
)
print(resp.content[0].text)
```

You should see:

```
<expected output>
```

## Step 2 — <add one layer of complexity>

Build on step 1. Still runnable on its own (or note the dependency on step 1's variables explicitly). Show the output again.

```python
# ...builds on step 1...
```

## Step 3 — <next layer: error handling / streaming / caching / tools>

Progressive complexity. Each step earns its place; don't open with the production version.

```python
# ...
```

## Verify it works

The concrete check — how they *know* they succeeded. Expected output, a one-line test, or a command that returns success. Never end at "and that's it!".

```bash
<command to run>
# expected: <exact result>
```

## Troubleshooting

The real errors they'll hit, with the exact fix:

- **`AuthenticationError`** → `ANTHROPIC_API_KEY` not set, or set in the wrong shell.
- **`model: not found`** → check the model ID against the current model list.
- **`RateLimitError`** → lower concurrency / add backoff.
- **`AttributeError` on `resp.text`** → it's `resp.content[0].text` (content is a list of blocks).

## Next steps

Where to go to extend this — link out to how-to guides and reference (don't inline them here).

- <link: a how-to for the next task>
- <link: reference docs for the API surface used>
- <link: a runnable exemplar, e.g. build-evals' scripts/>
