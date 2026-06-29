---
name: write-docs
description: Use when writing or restructuring documentation — a tutorial, a how-to guide, reference material, an explanation, a README, or a docs set that feels muddled. Triggers include "write docs for X", "document this", "write a tutorial", "write a how-to / guide", "write the reference", "explain how this works", "our docs are a mess", "restructure the docs", "write a README". Embodies Diátaxis — one document, one mode; mixing modes is the diagnosed failure.
---

# write-docs

Write documentation that serves the reader's actual need by classifying it into the right *mode* first. The reason most docs are bad isn't bad writing — it's that one document tries to teach, instruct, describe, and explain all at once, so it does none of them well. (Diátaxis, Daniele Procida; adopted by Django, Cloudflare, GitHub, Canonical.)

## The one principle

**One document, one mode.** There are exactly four documentation modes, split on two axes — *acquisition vs application* (am I learning, or doing?) × *theory vs practice* (am I studying, or working?):

| Mode | Need | Reader is… | The question it answers |
|------|------|-----------|------------------------|
| **Tutorial** | learning-oriented | a learner, hand-held to a guaranteed first success | "teach me, I don't know what I don't know yet" |
| **How-to guide** | task-oriented | competent, with a goal and a deadline | "how do I achieve X?" |
| **Reference** | information-oriented | working, needs a fact fast | "what exactly is the signature / flag / config key?" |
| **Explanation** | understanding-oriented | reflective, reading at leisure | "why is it built this way, what are the trade-offs?" |

Pick the mode before the first sentence. **Mixing modes in one document is the diagnosed failure** — the symptom is readers can't find anything and contributors don't know where new content goes. The compass test: ask "what mode is the reader in here?" If the honest answer is "mixed", split the document.

## When to use

- Writing any documentation artifact: tutorial, how-to/guide, reference, explanation, README
- Restructuring a docs set that feels muddled or hard to navigate
- Deciding whether a doc should teach, instruct, describe, or explain
- Finding gaps: walking the four quadrants to ask "do we have a tutorial to onboard? a how-to for the common task? reference for every flag?"

## When NOT to use

- The content must land for **two audiences at once** (engineer + stakeholder), or it's an architecture diagram / ADR / decision doc / one-pager → use the `technical-writeup` skill (two-altitude writing, trade-off docs). `write-docs` is about *reader mode*; `technical-writeup` is about *audience altitude* — they compose, but lead with the one that's the spine of the deliverable.
- It's a vault knowledge note → follow the vault conventions (jot vs refined, tags, wikilinks), not this skill
- It's a Jira ticket → use the ticket-guidelines rule
- It's a code docstring → use the `docstrings` skill

## Picking the mode

```
Reader is NEW and needs a guaranteed-success first run?     → TUTORIAL     (reference/tutorial.md)
Reader is COMPETENT and has a specific goal right now?       → HOW-TO       (reference/how-to.md)
Reader needs to LOOK UP a fact (API, flag, config)?         → REFERENCE    (reference/reference.md)
Reader wants to UNDERSTAND why / the trade-offs?            → EXPLANATION  (reference/explanation.md)
```

A docs *set* needs all four, separated. Use the quadrants as a gap-detector, not just a classifier: a product with great reference but no tutorial can't onboard anyone; one with tutorials but no how-tos strands competent users.

## The three quality principles (apply to every mode)

From GitHub's "Documentation done right" (the practitioner layer on top of Diátaxis):

- **Clear** — plain language; define or remove acronyms; check the target reader knows the terms.
- **Concise** — one topic per document; document only what's needed; link out for adjacent material.
- **Structured** — most important information first; headings + a table of contents; keep text highlighting (bold/italic) under ~10% so emphasis still emphasises.

Plus the house voice (see `~/.claude/toolkit/instructions/writing-style.md`): natural, technical, direct; contractions fine; NB/parenthetical asides fine; no bureaucratic throat-clearing ("The purpose of this document is to…"); **no em-dashes** (run the `emdash-audit` skill after).

## How to work

1. **Classify the mode** (or, for a set, map content to the four quadrants). State the mode explicitly before writing.
2. **Read that mode's reference file** for its specific discipline and shape.
3. **Write to that mode only.** If you feel the urge to explain inside a tutorial or teach inside a reference, that's the signal to link out to the other doc, not to blend.
4. **Apply clear/concise/structured** and the house voice.
5. **Make any code runnable** — copy-paste-ready, correct imports, no `...` in the load-bearing line (docs-as-tests if possible, so examples can't rot).
6. **Run `emdash-audit`** on the result.

## Reference material (read on demand)

Each stands alone; read the one for the mode you're writing.

- `reference/tutorial.md` — learning-oriented: the hand-held, guaranteed-to-succeed first experience; what to leave out; why you don't explain mid-tutorial.
- `reference/how-to.md` — task-oriented: the recipe shape; assume competence; one goal per guide.
- `reference/reference.md` — information-oriented: dry, exhaustive, mirrors the product's structure not the user's journey; consistency over prose.
- `reference/explanation.md` — understanding-oriented: discursive, the why and the trade-offs; read at leisure, not under deadline.
- `reference/diataxis-and-quality.md` — the full framework (two axes, the compass test, gap-detection) plus the clear/concise/structured principles and the docs-as-tests note. Read for restructuring a whole docs set.

## Templates

- `templates/tutorial.md`, `templates/how_to.md`, `templates/reference.md`, `templates/explanation.md` — a skeleton per mode.

## Related skills

- `technical-writeup` — two-audience technical content (diagrams, ADRs, one-pagers). Composes with this: a tutorial may need two altitudes; a decision doc is an explanation written for two audiences.
- `docstrings` — in-code reference at the function level.
- `emdash-audit` — run after writing to strip em-dashes (house rule: zero).

## Gotchas

- **The "comprehensive" doc that does everything.** A README that's part tutorial, part reference, part rationale reads as thorough and serves no one. Split it into linked docs, one mode each.
- **Explaining inside a tutorial.** A learner mid-first-run doesn't want the why — it breaks the flow and the guaranteed success. Save it for the explanation doc and link.
- **Reference written as prose.** Reference mirrors the product (every flag, every key), not a narrative. If it reads like an essay, it's the wrong mode.
- **A how-to that teaches from scratch.** How-tos assume competence. Onboarding-from-zero is a tutorial; conflating them frustrates both readers.

## Anti-patterns

- **Skipping the classify step.** Writing first, noticing the muddle later. Name the mode before the first sentence.
- **Mode-mixing rationalised as convenience.** "It's easier to keep it in one file" is exactly how docs rot. The four-way split *is* the value.
- **Bureaucratic openings and em-dashes.** Delete "The purpose of this document is to…"; run `emdash-audit`.
- **Unrunnable sample code.** `...` in the critical line, a hallucinated import. If you wouldn't paste and run it, neither will the reader.
