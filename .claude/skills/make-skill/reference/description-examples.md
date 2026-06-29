# Writing the description — before/after and a phrasing bank

The `description` is the only text Claude reads when choosing whether to load a skill. It is a **trigger**, not a summary. This file exists because the description is where skills most often fail: a good body behind a summary-style description simply never loads.

## The shape of a strong description

```
Use when <concrete situation> — <the non-obvious detail or symptom>.
Triggers include "<verbatim phrase>", "<verbatim phrase>", "<verbatim phrase>".
<Optional: the one-line mental model the skill embodies.>
```

Three jobs: (1) name the *situations*, (2) quote the *words* a user actually types, (3) state the *stance* so Claude picks this skill over a neighbour.

## Before → after

**Topic label → situational trigger**
- ✗ `A skill for working with our database.`
- ✓ `Use when querying the billing Postgres — the subscriptions table is append-only and the row you want is the highest version, not the most recent created_at. Triggers include "query subscriptions", "why is this user on the wrong plan", "billing data looks stale".`

**Summary → trigger with verbatim phrases**
- ✗ `This skill helps create Jira tickets following our conventions.`
- ✓ `Use when drafting a Jira ticket or a ticket-shaped markdown file. Triggers include "make a ticket for X", "draft a ticket", "write up a ticket for Y", "turn this into a ticket". Enforces the house ticket structure — concise, outcome-first, trusts the implementer.`

**Vague capability → symptom + stance**
- ✗ `Reviews code for quality.`
- ✓ `Use when reviewing your own uncommitted changes or recent commits before pushing. Triggers include "review my changes", "check this before I commit", "is this PR-ready". Produces a structured review with severity-tagged findings; for a teammate's PR use peer-review instead.`

**Over-broad → scoped, with a NOT-boundary baked in**
- ✗ `Helps with writing and documentation.`
- ✓ `Use when writing a runbook, an internal how-to, or an onboarding doc — operational prose where a reader needs to *do* something under time pressure. Triggers include "write a runbook", "document this process", "on-call doc". For two-audience architecture/decision docs use technical-writeup; for vault knowledge notes use the vault conventions.`

## Phrasing bank

Openers that read as triggers:
- "Use when …"
- "Use after …" (post-hoc skills: review, summarise, audit)
- "Use before …" (gating skills: pre-commit checks, scoping)
- "TRIGGER when … / SKIP when …" (when false positives are costly — see the `claude-api` skill)

Always include a `Triggers include "…", "…"` clause with the *user's* words, not yours. Mine your own past prompts for these.

End with the stance when the skill has an opinion: "Embodies start-simple / earn-the-complexity." "The core move: write the same idea at two altitudes." This is what makes Claude pick the right skill among similar ones.

## Disambiguation — the most overlooked trick

When two skills are neighbours, each description should *name the other and the boundary*. `review-code` says "for a teammate's PR use peer-review instead." `make-skill` says "to improve an existing skill use improve-skill." This single sentence prevents the most common misfire: the right skill existing but the wrong one loading.
