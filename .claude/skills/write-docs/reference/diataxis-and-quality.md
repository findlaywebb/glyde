# Diátaxis + quality principles (for restructuring a docs set)

The full framework for when you're not writing one document but organising or auditing a whole documentation set. Sources: Diátaxis (Daniele Procida); "Documentation done right" (Ellich & Browning, GitHub, 2025).

## The two axes

The four modes are not arbitrary — they fall out of two questions about the reader:

```
                    PRACTICE (working)        THEORY (studying)
ACQUISITION   ┌─────────────────────────┬──────────────────────────┐
(learning)    │   TUTORIAL              │   EXPLANATION             │
              │   learning-oriented     │   understanding-oriented  │
              ├─────────────────────────┼──────────────────────────┤
APPLICATION   │   HOW-TO GUIDE          │   REFERENCE               │
(doing)       │   task-oriented         │   information-oriented    │
              └─────────────────────────┴──────────────────────────┘
```

- **Acquisition vs application** — is the reader *learning*, or *doing*?
- **Theory vs practice** — is the reader *studying*, or *working*?

Tutorial and how-to are both *practice* (hands on the tool); reference and explanation are both *theory* (thinking about it). Tutorial and explanation are both *acquisition* (taking knowledge in); how-to and reference are both *application* (putting it to use).

## The compass test (quality heuristic)

For any document, ask: **"What mode is the reader in here?"** If the honest answer is mixed, the document is doing too much — split it. This single question is the framework's main quality tool. The diagnosed failure mode across all bad developer docs is one document trying to be tutorial + reference + explanation at once: readers can't find anything, contributors don't know where new content goes.

## Diátaxis as a gap detector

The four quadrants aren't only for classifying existing docs — walk them to find what's *missing*:

- Is there a **tutorial** so a newcomer can get a first success?
- Is there a **how-to** for each common task?
- Is there **reference** for every tool / flag / endpoint?
- Is there **explanation** for the design decisions people keep asking about?

A product with great reference but no tutorial can't onboard; one with tutorials but no how-tos strands competent users.

## The three quality principles (every mode)

GitHub's practitioner layer on top of Diátaxis:

1. **Clear** — plain language; define or remove acronyms; check the target reader actually knows the terms.
2. **Concise** — document only necessary information; one document per topic/task; link out for adjacent material.
3. **Structured** — most important information first; headings + a table of contents; keep text highlighting (bold/italic) under ~10% so emphasis still emphasises; consistent styling across docs.

## Docs-as-tests

Where examples are runnable, wire them into CI (docs-as-tests) so they can't silently rot. Copy-paste-ready examples that are also tested are the gold standard for the how-to and tutorial modes.

## House voice

Layer the FMP/vault voice on all of it: natural, technical, direct; contractions fine; NB/parenthetical asides fine; no bureaucratic openings; **no em-dashes** (run `emdash-audit`). See `~/.claude/toolkit/instructions/writing-style.md`.

## Adoption note

Diátaxis is used by Django, Cloudflare, Gatsby, Canonical, and (per the GitHub post) GitHub's internal docs — and Anthropic's own developer surface is structurally Diátaxis: *Get started* = tutorial, *Documentation* = reference, *Insights* = explanation, with how-tos in the Cookbook.
