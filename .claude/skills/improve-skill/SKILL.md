---
name: improve-skill
description: Use when auditing or refining a Claude skill that already exists — tightening a description that under-triggers, cutting content that states the obvious, extracting gotchas, splitting a skill that does too much, or fixing one that loads at the wrong time. Triggers include "improve this skill", "refine this skill", "why doesn't this skill trigger", "audit my skill", "this skill is too long", "make this SKILL.md better", "review this skill". Audits against the make-skill rubric and applies the fixes.
---

# improve-skill

Refine an existing skill against the authoring rubric. Most skills don't fail because the body is wrong — they fail because the **description under-triggers** (so the good body never loads) or because the body is **padded with the obvious** (so the signal that matters gets lost). This skill finds and fixes both.

## The one principle

**Diagnose before you rewrite.** A skill that "isn't working" almost always has a specific, locatable fault — and the fix is usually small. Run the diagnosis below, name the fault, then apply the targeted fix. Rewriting a whole skill when the only problem was a summary-style description wastes effort and risks losing hard-won gotchas.

## When to use

- A skill exists but never seems to load when it should → description diagnosis
- Claude loads a skill at the wrong time / too often → over-trigger diagnosis
- A SKILL.md has grown long and Claude ignores parts of it → progressive-disclosure refactor
- A skill restates general knowledge and adds little → signal-density cut
- A skill has accumulated several jobs → split diagnosis
- Periodic hygiene pass across the skill library
- You just finished a new skill with `make-skill` and want a second-pass audit

## When NOT to use

- The skill doesn't exist yet → use the `make-skill` skill to author it
- The "skill" should really be a hook (always-on behaviour) or an MCP (external access) → it's mis-categorised; see `~/.claude/toolkit/rules/agentic-extension.md`
- You want to change *what the skill does*, not *how well it's written* → that's a redesign; treat it as a new authoring pass

## The rubric

This skill audits against the canonical rubric in the `make-skill` skill: `~/.claude/skills/make-skill/reference/skill-authoring-rubric.md` (the nine categories, description-as-trigger, gotchas, progressive disclosure, the don't-state-the-obvious test, the final checklist). Read it first — it's the standard everything below scores against. The description-craft examples live alongside it in `reference/description-examples.md`.

## The diagnosis (run in order)

1. **Trigger audit (highest yield).** Read *only* the `description`. Without reading the body, would you know exactly when to load this — and the specific words a user would type? If it's a summary ("This skill helps with X") or a topic label, that's the fault. Most "my skill never fires" problems end here.
2. **Signal-density scan.** For each line of the body, apply the governing test: *would Claude do this anyway?* Mark every line that restates a default ("write tests", "handle errors"). These are deletions.
3. **Category check.** Does the skill fit cleanly into one of the nine categories? If it straddles several, it's a split candidate.
4. **Gotchas check.** Is there a gotchas section? Is it built from real traps or generic advice? A skill with real usage and no gotchas is usually not encoding anything non-obvious — question its existence.
5. **Disclosure check.** Is the SKILL.md scannable (~<150 lines)? Is detail that's read-only-sometimes living in the body instead of `reference/`? Is boilerplate inlined that should be a `scripts/` file?
6. **Disambiguation check.** Are there neighbour skills? Does the description name them and the boundary ("for X use Y instead")? Missing boundaries cause the wrong-skill-loads misfire.
7. **Frontmatter check.** Exactly `name` + `description`? Name kebab-case and matching the folder?
8. **Pressure check (discipline skills only).** If the skill enforces a rule agents are tempted to break, has it ever been pressure-tested? Run the loop in `make-skill`'s `reference/pressure-testing-skills.md` — a multi-pressure scenario with a fresh subagent, rationalizations captured verbatim, loopholes countered explicitly. A discipline skill that's never been seen holding under pressure is unverified, however well written.

## The fixes

| Diagnosis | Fix |
|-----------|-----|
| Description is a summary | Rewrite as a trigger: "Use when…", concrete situations, verbatim phrases. See `make-skill`'s `reference/description-examples.md`. |
| Under-triggers | Add the missing verbatim phrases (mine the user's actual prompts) and the symptom, not just the topic. |
| Over-triggers | Narrow the situations; add a `When NOT to use` and disambiguation boundaries to the description. |
| States the obvious | Delete the line. No replacement. |
| Too long / ignored | Move read-sometimes detail to `reference/*.md`; leave a one-line pointer in SKILL.md. |
| Does too much | Split into multiple skills, one category each; cross-reference them by name. |
| No gotchas | Add the section; seed it from the failures that prompted this audit. |
| Inlined boilerplate | Extract to `scripts/`; point to it from the body. |
| Missing disambiguation | Add "for X use Y instead" to both descriptions. |

## How to work

1. Locate the skill folder (default `~/.claude/skills/<name>/`; repos use `./.claude/skills/<name>/`).
2. Read the rubric, then run the seven-step diagnosis. **Report the findings before editing** — a short list of faults, highest-yield first.
3. Apply fixes surgically with `Edit`. Preserve gotchas and any hard-won specifics; never delete signal to make room.
4. Re-run the rubric's final checklist. Confirm the description would now trigger on the user's real phrasing.
5. If you split a skill, leave the original's description pointing at the successors.

## Gotchas

- **The fix for under-triggering is almost never in the body.** Resist rewriting the body when the description is the fault — it's the only text read at selection time.
- **Don't delete a thin gotchas section to "tidy up".** Thin is honest; empty-after-real-use is the smell. Grow it, don't cut it.
- **Length is a symptom, not the disease.** A long SKILL.md ignored by Claude usually means buried signal, not too many words per se — move detail to `reference/`, don't just compress prose.
- **"Improve" can mean "split".** The senior move on a sprawling skill is to recognise it's two skills, not to polish one bloated one.

## Anti-patterns

- **Rewriting before diagnosing.** Produces churn and loses specifics. Name the fault first.
- **Adding more rather than cutting.** Improvement is usually subtraction — the obvious lines, the duplicated context, the third paragraph of rationale.
- **Polishing prose while the description still under-triggers.** A beautiful body behind a dead description is still a dead skill.
- **Generic gotchas.** "Be careful with edge cases" is not a gotcha. A gotcha is a *specific* trap and its fix.
