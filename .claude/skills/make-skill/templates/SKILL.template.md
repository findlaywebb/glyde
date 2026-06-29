---
name: skill-name-kebab-case
description: Use when <concrete situation> — <the non-obvious detail or symptom that distinguishes this from neighbours>. Triggers include "<verbatim phrase a user types>", "<phrase>", "<phrase>". <Optional one-line stance the skill embodies, e.g. "Embodies eval-first development.">
---

# skill-name-kebab-case

<One sentence stating what this skill makes Claude do that it would NOT do by default. If you can't write this sentence, this probably shouldn't be a skill — see make-skill's "When NOT to use".>

## The one principle

**<The single load-bearing sentence the whole skill hangs off. Bold it. Everything below should serve this.>**

<Optional: one short paragraph of the most important non-obvious context. A corollary, a key trade-off, a link to a sibling skill.>

## When to use

- <concrete situation>
- <concrete situation>
- <someone asks "<verbatim question>">

## When NOT to use

- <case> → <the correct alternative and why: another skill by name / a hook / a workflow / an MCP / an instructions doc>
- <case> → <alternative>

## The procedure   <!-- for workflow skills; use structured headings instead for reference-knowledge skills -->

1. <step — specify the outcome and the constraint, not every keystroke; trust the model on tactics>
2. <step — point to reference/ and scripts/ where detail lives>

## Reference material (read on demand)   <!-- delete if the skill has no reference/ files -->

- `reference/<file>.md` — <what's in it and when to read it>

## Bundled scripts   <!-- delete if none -->

- `scripts/<file>` — <what it does; keep dependency-light; usage in the file header>

## Templates   <!-- delete if none -->

- `templates/<file>` — <the artifact the skill produces>

## Gotchas

- <concrete trap> → <the fix>. Harvest these from real failures; this is the highest-signal section. Thin on day one is honest.

## Anti-patterns

- <the named failure mode this skill exists to prevent>
- <a tempting-but-wrong move and what to do instead>
