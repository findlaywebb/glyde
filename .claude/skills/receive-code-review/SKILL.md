---
name: receive-code-review
description: Use when responding to code-review feedback on your own work — review comments on a PR, a reviewer's checklist, Findlay relaying a teammate's comments, or findings from an automated review — before implementing any suggestion. Triggers include "address the review feedback", "the reviewer says X", "fix the review comments", review items arriving mid-task, or noticing you're about to reply "You're absolutely right". Embodies verify-then-act: feedback is a claim to check against the codebase, not an order; push back with technical reasoning when it's wrong; no performative agreement.
---

# receive-code-review

Makes Claude treat review feedback as claims to verify rather than instructions to execute — the default failure is enthusiastic agreement followed by blind implementation of a suggestion that's wrong for this codebase.

## The one principle

**Verify before implementing; push back with evidence when the reviewer is wrong.** Technical correctness over social comfort. The reviewer and you both serve the same goal — a correct codebase — not each other's feelings.

## When to use

- Any review feedback on work you produced: PR comments, a review checklist, relayed teammate comments, `peer-review`/`launch-deep-review` output being acted on.

## When NOT to use

- *Giving* a review → `peer-review` (teammate's PR) or `review-code` / `launch-deep-review` (own changes).
- Rolling posted comments into a checklist → `collect-pr-comments`.

## The procedure

1. **Read all of it before reacting to any of it.** Items are often related; partial understanding produces wrong implementations.
2. **Clarify everything unclear first.** If items 4 and 5 are ambiguous, don't implement 1–3 while waiting — say "I understand 1, 2, 3, 6; I need clarification on 4 and 5 before starting."
3. **Verify each item against the codebase.** Is it technically correct *here*? Does it break existing behaviour? Is there a reason the code is the way it is (compat, platform, a decision already made)? For "implement X properly" suggestions, grep for actual usage first — if nothing calls it, the right response is "remove it (YAGNI)?", not a fuller implementation.
4. **Respond technically.** Correct feedback: fix it and state what changed — "Fixed — the cache key now includes the version." Wrong feedback: push back with specifics — failing behaviour it would cause, the constraint the reviewer can't see, the test that documents the current choice. If it conflicts with an architectural decision Findlay already made, stop and raise it rather than silently complying either way.
5. **Implement one item at a time**, blocking issues first, testing each, then verify no regressions across the set.
6. **Distil the lesson.** After the dust settles, apply the standing convention: real questions in the review get real reasoning in reply, and any generalisable lesson becomes a check, doc, or rule rather than a one-off fix. Irreducible taste gets left alone.

## Forbidden responses

- "You're absolutely right!" / "Great point!" / "Excellent feedback!" — performative agreement; say what's true instead, or just act.
- Any gratitude filler ("Thanks for catching that"). The fix itself shows the feedback landed.
- "Let me implement that now" before step 3 has happened.

If pushback turns out wrong, correct it factually and move on: "Verified — you're correct; my assumption about X was wrong. Fixing." No apology spiral, no defending the original pushback.

## Gotchas

- **Posting replies on GitHub is repo-gated.** In Findlay's **private/personal repos**, replying via `gh` is fine — reply in the comment thread (`gh api repos/{owner}/{repo}/pulls/{pr}/comments/{id}/replies`), never as a top-level PR comment (it orphans the thread). In **work FMP repos** (tagged `fmp` in `~/.claude/toolkit/repos.yaml`), never post review replies — not as Findlay, not as the agent. Draft the reply text for Findlay to post himself. When unsure which kind of repo it is, check repos.yaml; default to drafting, not posting.
- **"Can't easily verify" is a state to report, not route around**: "I can't verify this without X — investigate, ask, or proceed?"
- **Batch-implementing a whole review then testing once** hides which change broke what; one item, one test.
- **External/automated reviewers lack context by construction** — they haven't seen the spec or the decisions. Higher verification bar, same politeness bar (none needed, just facts).

## Provenance

Forked from `superpowers:receiving-code-review` (plugin v5.1.0), amended: house tone, wired to the review-comments-become-conventions practice and the `peer-review`/`collect-pr-comments` ecosystem.
