# Orchestration patterns

The pattern menu, with runnable code and the choose-by-task guidance. Most real workflows compose several of these. Mechanics (hooks, schema, limits) are in `workflow-mechanics.md`.

## Pipeline (the default)

Each item flows through all stages independently; no barrier between stages. Item A can be in stage 3 while item B is still in stage 1. Wall-clock = slowest single-item chain, not sum-of-slowest-per-stage.

```js
const results = await pipeline(
  DIMENSIONS,
  d => agent(d.prompt, {label: `review:${d.key}`, phase: 'Review', schema: FINDINGS}),
  review => parallel(review.findings.map(f => () =>
    agent(`Adversarially verify: ${f.title}`, {phase: 'Verify', schema: VERDICT})
      .then(v => ({...f, verdict: v}))))
)
const confirmed = results.flat().filter(Boolean).filter(f => f.verdict?.isReal)
```

Use for: any multi-stage per-item work. Reach for it first.

## The pipeline-vs-barrier decision

A barrier (`parallel()` between stages) is correct **only** when stage N needs cross-item context from all of stage N-1:
- Dedup/merge across the full result set before expensive downstream work.
- Early-exit on a total ("0 findings → skip verification entirely").
- Stage N's prompt references "the other findings" for comparison.

A barrier is **not** justified by "I need to flatten/map/filter first" (do it inside a pipeline stage), "the stages are conceptually separate" (pipeline models that), or "it's cleaner" (barrier latency is real).

Smell test — if you wrote:
```js
const a = await parallel(...)
const b = transform(a)              // flatten/map/filter, no cross-item dependency
const c = await parallel(b.map(...))
```
that middle transform doesn't need the barrier. Rewrite as `pipeline(items, stageA, r => transform([r]).flat(), stageB)`. When in doubt: pipeline.

## Fan-out + synthesise (a justified barrier)

Dedup across all findings before expensive verification:
```js
const all = await parallel(DIMENSIONS.map(d => () => agent(d.prompt, {schema: FINDINGS})))
const deduped = dedupeByFileAndLine(all.filter(Boolean).flatMap(r => r.findings))  // needs ALL at once
const verified = await parallel(deduped.map(f => () => agent(verifyPrompt(f), {schema: VERDICT})))
```

## Classify-and-act

Route each item by type to the right handler. A cheap classifier (a tier override may be justified here) tags items; a `switch` dispatches.

## Adversarial verify (the highest-value pattern)

Spawn N independent skeptics per finding, each prompted to *refute*. Kill the finding unless it survives a majority. Prevents plausible-but-wrong findings surviving.
```js
const votes = await parallel(Array.from({length: 3}, () => () =>
  agent(`Try to refute: ${claim}. Default to refuted=true if uncertain.`, {schema: VERDICT})))
const survives = votes.filter(Boolean).filter(v => !v.refuted).length >= 2
```
**Perspective-diverse** variant — when a finding can fail in more than one way, give each verifier a distinct lens instead of N identical refuters:
```js
const vs = await parallel(['correctness','security','reproduce'].map(lens => () =>
  agent(`Judge "${claim}" via the ${lens} lens — real?`, {schema: VERDICT})))
```

## Generate-and-filter / tournament

Generate many candidates from different angles, score with parallel judges, keep the best. For a tournament, score pairwise. Beats one-attempt-iterated when the solution space is wide (e.g. design proposals: MVP-first / risk-first / user-first → judge → synthesise from the winner, grafting the best of the runners-up).

## Loop-until-dry

For unknown-size discovery (bugs, edge cases). Keep spawning finders until K consecutive rounds surface nothing new — a fixed count misses the tail.
```js
const seen = new Set(), confirmed = []
let dry = 0
while (dry < 2) {
  const found = (await parallel(FINDERS.map(f => () => agent(f.prompt, {phase:'Find', schema: BUGS}))))
    .filter(Boolean).flatMap(r => r.bugs)
  const fresh = found.filter(b => !seen.has(key(b)))      // dedup vs ALL seen, not vs confirmed
  if (!fresh.length) { dry++; continue }
  dry = 0; fresh.forEach(b => seen.add(key(b)))
  const judged = await parallel(fresh.map(b => () =>
    agent(`Verify "${b.desc}" — real?`, {phase:'Verify', schema: VERDICT}).then(v => ({b, real: v?.real}))))
  confirmed.push(...judged.filter(v => v.real).map(v => v.b))
}
```
**Critical:** dedup against `seen` (everything ever found), not `confirmed` — else judge-rejected findings reappear each round and the loop never converges.

## Loop-until-budget

Scale depth to the user's token target. Guard on `budget.total` — with no target, `remaining()` is `Infinity` and you'd run to the 1000-agent cap.
```js
const bugs = []
while (budget.total && budget.remaining() > 50_000) {
  const r = await agent('Find bugs in this codebase.', {schema: BUGS})
  bugs.push(...r.bugs)
  log(`${bugs.length} found, ${Math.round(budget.remaining()/1000)}k remaining`)
}
```

## Completeness critic

A final agent asks "what's missing — a modality not searched, a claim unverified, a source unread?" What it finds becomes the next round of work. Pairs well with loop-until-dry.

## Scaling to the request

- "find any bugs" → a few finders, single-vote verify.
- "thoroughly audit this" / "be comprehensive" → larger finder pool, 3-5 vote adversarial pass, synthesis stage.
- Lean thorough for research/review/audit; lean brief for quick checks.

These aren't exhaustive — compose novel harnesses when the task calls for it (staged escalation, self-repair loops, bracket tournaments).
