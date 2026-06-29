// workflow_skeleton.js — a minimal valid dynamic workflow to copy and edit.
//
// The shape: review N dimensions in a pipeline, and as soon as each dimension's
// review returns, adversarially verify its findings with a fresh agent. No barrier
// between review and verify — dimension B verifies while dimension C still reviews.
//
// Pass this script inline to the Workflow tool (do NOT Write it to disk first; the
// tool persists it for you and returns the path for resume/iteration).

// meta MUST be the first statement and a PURE LITERAL (no variables/calls/spreads).
export const meta = {
  name: 'review-changes',
  description: 'Review changed files across dimensions, adversarially verify each finding',
  phases: [
    { title: 'Review', detail: 'one agent per review dimension' },
    { title: 'Verify', detail: 'fresh skeptic per finding, prompted to refute' },
  ],
}

// JSON Schemas force structured, validated hand-offs (no parsing; model retries on mismatch).
const FINDINGS = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          title: { type: 'string' },
          file: { type: 'string' },
          line: { type: 'integer' },
          detail: { type: 'string' },
        },
        required: ['title', 'file', 'detail'],
      },
    },
  },
  required: ['findings'],
}

const VERDICT = {
  type: 'object',
  properties: {
    isReal: { type: 'boolean' },
    reason: { type: 'string' },
  },
  required: ['isReal', 'reason'],
}

// The dimensions to review. Edit these for your task; `args` can supply them at call time.
const DIMENSIONS = (args && args.dimensions) || [
  { key: 'correctness', prompt: 'Review the current diff for correctness bugs. Report each as a finding.' },
  { key: 'security',    prompt: 'Review the current diff for security issues. Report each as a finding.' },
  { key: 'simplicity',  prompt: 'Review the current diff for needless complexity. Report each as a finding.' },
]

// pipeline(): each dimension flows review -> verify independently, no barrier between stages.
const results = await pipeline(
  DIMENSIONS,

  // Stage 1 — review one dimension.
  (d) => agent(d.prompt, { label: `review:${d.key}`, phase: 'Review', schema: FINDINGS }),

  // Stage 2 — adversarially verify every finding from this dimension, concurrently.
  // A fresh agent (not the reviewer) tries to refute each finding -> kills self-preference bias.
  (review, d) =>
    parallel(
      (review?.findings || []).map((f) => () =>
        agent(
          `Adversarially verify this finding. Try to REFUTE it; default to isReal=false if uncertain.\n` +
            `Dimension: ${d.key}\nFile: ${f.file}${f.line ? ':' + f.line : ''}\n` +
            `Claim: ${f.title}\nDetail: ${f.detail}`,
          { label: `verify:${f.file}`, phase: 'Verify', schema: VERDICT }
        ).then((v) => ({ ...f, dimension: d.key, verdict: v }))
      )
    )
)

// Flatten, drop skipped/failed (null), keep only confirmed findings.
const confirmed = results.flat().filter(Boolean).filter((f) => f.verdict?.isReal)

log(`${confirmed.length} confirmed finding(s) after adversarial verification`)

return { confirmed }
