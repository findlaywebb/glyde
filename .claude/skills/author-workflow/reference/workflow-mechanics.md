# Workflow mechanics

The runtime surface for a dynamic workflow script, and the gotchas that bite. Read this before writing the script body.

## The meta block (required, first thing in the file)

Every script begins with a **pure-literal** `export const meta`:

```js
export const meta = {
  name: 'find-flaky-tests',                 // kebab-case
  description: 'Find flaky tests and propose fixes',  // one line, shown in the permission dialog
  phases: [                                 // one entry per phase() call; titles matched exactly
    { title: 'Scan',  detail: 'grep CI logs for retry markers' },
    { title: 'Fix',   detail: 'one agent per flaky test' },
  ],
  // optional: whenToUse (shown in the workflow list), and `model` on a phase entry
}
```

It must be a pure literal — **no variables, function calls, spreads, or template interpolation**. Required: `name`, `description`. Use the same phase titles in `meta.phases` as in `phase()` calls.

## The hooks

- `agent(prompt, opts?) => Promise<any>` — spawn a subagent. Without `schema`, returns its final text (string). With `schema` (a JSON Schema), the agent is forced to call a StructuredOutput tool and you get a validated object back — no parsing. Returns `null` if the user skips it mid-run (`.filter(Boolean)`).
  - `opts.schema` — JSON Schema for structured output (validated at the tool layer; model retries on mismatch).
  - `opts.label` — display label override.
  - `opts.phase` — assign this agent to a progress group explicitly (use inside `pipeline()`/`parallel()` to avoid racing the global `phase()` state).
  - `opts.model` — model override. **Default: omit** — inherits the session model, almost always correct.
  - `opts.isolation: 'worktree'` — fresh git worktree. EXPENSIVE (~200-500ms + disk). Use ONLY when agents mutate files in parallel and would conflict.
  - `opts.agentType` — use a custom subagent type (e.g. `'Explore'`) instead of the default workflow subagent; composes with `schema`.
- `pipeline(items, stage1, stage2, ...) => Promise<any[]>` — each item flows through all stages independently, **no barrier between stages**. The default for multi-stage work. Each stage callback gets `(prevResult, originalItem, index)`. A stage that throws drops that item to `null` and skips its remaining stages.
- `parallel(thunks) => Promise<any[]>` — run thunks concurrently; **barrier** (awaits all). A throwing thunk resolves to `null` (the call never rejects) — `.filter(Boolean)` the results.
- `log(message)` — narrator line shown above the progress tree. Use it to report what was dropped/capped.
- `phase(title)` — start a new phase; subsequent `agent()` calls group under it.
- `workflow(nameOrRef, args?) => Promise<any>` — run another saved workflow (by name) or a script file (`{scriptPath}`) inline as a sub-step. Shares concurrency cap, agent counter, abort signal, token budget. Nesting is one level only.
- `args` — the value passed as the Workflow tool's `args` input, verbatim. Pass arrays/objects as real JSON, NOT a JSON string.
- `budget` — `{total: number|null, spent(), remaining()}`. `total` is the turn's token target (null if unset). Shared pool across main loop + all workflows. Hard ceiling: past `total`, `agent()` throws. Guard loops on `budget.total` (else `remaining()` is `Infinity` and you hit the 1000-agent cap).

## Concurrency and limits

- Concurrent `agent()` calls cap at `min(16, cores - 2)` per workflow; excess queues. You can still pass 100 items — only ~10-16 run at once.
- Total agents across a workflow's lifetime cap at 1000 (runaway backstop).

## Structured output — always use it for hand-offs

```js
const FINDINGS = {
  type: 'object',
  properties: {
    findings: { type: 'array', items: {
      type: 'object',
      properties: { title: {type:'string'}, file: {type:'string'}, line: {type:'integer'}, severity: {type:'string'} },
      required: ['title', 'file'],
    }},
  },
  required: ['findings'],
}
const result = await agent('Review src/auth for bugs.', {schema: FINDINGS})  // result.findings is validated
```

A vague subagent hand-off (no objective, no output shape) is the dominant multi-agent failure mode. `schema` eliminates it.

## Resume

Every invocation persists its script under the session dir and returns the path in the tool result. To iterate or recover after a pause/kill/edit:

- Relaunch with `Workflow({scriptPath, resumeFromRunId})`. The longest unchanged prefix of `agent()` calls returns cached results instantly; the first edited/new call and everything after runs live.
- Same script + same args → 100% cache hit. Stop the prior run (`TaskStop`) before resuming.

## JS-not-TS gotchas

- The script is **plain JavaScript**. Type annotations (`: string[]`), interfaces, generics fail to parse.
- Runs in an async context — `await` directly at top level.
- **`Date.now()`, `Math.random()`, argless `new Date()` all throw** — they'd break resume determinism. Pass timestamps via `args`; stamp results after the workflow returns; vary agent prompts/labels by index for pseudo-randomness.
- No filesystem or Node API access from the script body (agents have tools; the orchestration script does not).
- Standard JS built-ins (JSON, Math except random, Array) are available.
