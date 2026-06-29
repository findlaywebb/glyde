---
name: make-skill
description: Use when creating a new Claude skill from scratch — turning a repeated workflow, a hard-won gotcha, domain knowledge, or a set of bundled scripts into a SKILL.md folder. Triggers include "make a skill for X", "turn this into a skill", "I keep doing this manually", "capture this as a skill", "scaffold a skill", "write a SKILL.md". Embodies the Anthropic "a skill is a folder, not a file" discipline — description-as-trigger, a gotchas section, progressive disclosure, bundled scripts, and don't-state-the-obvious.
---

# make-skill

Author a Claude skill the way Anthropic's own teams do — as a *folder of instructions, scripts, and resources an agent discovers and uses on demand*, not a wall of markdown. (Anthropic, "Lessons from building Claude Code: how we use skills", 2025.)

## The one principle

**A skill carries only the knowledge that changes what Claude does.** Claude already knows general programming, common APIs, and how to write tests. A skill earns its place by encoding what Claude *wouldn't* do by default: the domain gotcha, the house pattern, the append-only table that bites you, the verification step everyone forgets. If a line restates what Claude would already do, delete it — it is pure context cost. The whole craft is *signal density*.

The corollary: **the description is the most important line in the skill.** It is the only thing Claude reads when deciding whether to load the skill. Write it as a *trigger*, not a summary — first-person situations and verbatim phrases the user might say. A skill that never triggers is worthless however good its body.

## When to use

- Capturing a workflow you've done by hand more than twice
- Encoding domain knowledge or gotchas Claude keeps getting wrong
- Distributing a house pattern, runbook, or verification routine across a team
- Bundling helper scripts so Claude composes them instead of rewriting boilerplate
- Promoting a one-off prompt that worked into a reusable capability

## When NOT to use

- The content just restates general programming knowledge → it adds context weight, no value
- It's a *single* gotcha → drop it in the relevant CLAUDE.md or an instructions doc, not a whole skill
- It's automatic, every-time behaviour ("always run ruff after editing") → that's a **hook**, not a skill (use `update-config`)
- It's pure connectivity to an external system → that's an **MCP server**, not a skill
- It's a complex multi-agent orchestration → that's a **workflow** (see the `author-workflow` skill)
- You're improving a skill that already exists → use the `improve-skill` skill instead

For the full skill-vs-hook-vs-workflow-vs-MCP-vs-instructions decision, see `~/.claude/toolkit/rules/agentic-extension.md`.

## The procedure

1. **Extract the real value first.** Before writing anything, answer in one sentence: *what does this make Claude do that it wouldn't do by default?* If you can't, stop — this may not be a skill (see "When NOT to use"). This sentence becomes the body's spine.
2. **Decide the category.** Place it in exactly one of the nine categories (`reference/skill-authoring-rubric.md`). A skill that straddles several is two skills — split it.
3. **Scaffold the folder.** Run `scripts/scaffold_skill.sh <skill-name>` to create the folder with a pre-filled `SKILL.md`, `reference/`, `scripts/`, and `templates/`. By default it creates the skill in the version-controlled toolkit (`~/.claude/toolkit/skills/`) and symlinks it into `~/.claude/skills/` — **never create a skill directly in `~/.claude/skills/`, it would be untracked by git.** Pass an explicit target dir (e.g. `./.claude/skills`) only for a repo-local skill. Delete the subdirs you don't use.
4. **Write the description as a trigger.** Open with "Use when…", list concrete situations, then quote verbatim phrases ('Triggers include "…"'). This is the highest-leverage edit — see the rubric's description section and the worked examples in `reference/description-examples.md`.
5. **Write the body — signal only.** Lead with the one principle / the core move. "When to use" + "When NOT to use". Then the procedure or knowledge. Cut anything Claude does by default.
6. **Build the gotchas section.** The highest-signal content in any skill. Each entry is a concrete trap and the fix, ideally from a real failure. Empty at first is honest — grow it as the skill gets used.
7. **Push detail down (progressive disclosure).** Long signatures, alternative approaches, background → `reference/*.md`, read on demand. The SKILL.md stays a scannable index.
8. **Bundle scripts, don't inline boilerplate.** If Claude would reconstruct the same code each run, ship it in `scripts/` so it spends tokens composing, not retyping.
9. **Add `config.json` only if setup is needed.** Prompt for required config; use the `AskUserQuestion` tool for structured choices. Persist state via `${CLAUDE_PLUGIN_DATA}` only if the skill needs memory across runs.
10. **Self-audit with the checklist.** Run the skill through `improve-skill`'s rubric (or the checklist at the foot of `reference/skill-authoring-rubric.md`) before declaring it done.
11. **Pressure-test discipline skills before trusting them.** If the skill enforces a rule agents will be tempted to break (test-first, no-fix-without-investigation), run the eval loop in `reference/pressure-testing-skills.md`: baseline a subagent *without* the skill under a multi-pressure scenario, capture its rationalizations verbatim, write the skill against those, re-test until compliant. Reference skills and workflow digests skip this — there's nothing to violate.

## Anatomy of the folder

```
my-skill/
  SKILL.md            # required — frontmatter (name, description) + a scannable body
  reference/          # progressive disclosure — read on demand, each file stands alone
  scripts/            # bundled helpers Claude runs/composes (keep dependency-light)
  templates/          # fill-in artifacts the skill produces
  config.json         # optional — setup prompts / user preferences
```

The frontmatter is exactly two fields: `name` (kebab-case, matches the folder) and `description` (the trigger). Nothing else is load-bearing.

## Reference material (read on demand)

- `reference/skill-authoring-rubric.md` — the full rubric: the nine categories, description craft, gotchas, progressive disclosure, distribution, the don't-state-the-obvious test, and a final quality checklist. The canonical authoring reference — `improve-skill` audits against it too.
- `reference/description-examples.md` — before/after description rewrites and a bank of strong trigger phrasings, since the description is where skills most often fail.
- `reference/pressure-testing-skills.md` — eval-driven skill validation: baseline a subagent without the skill, pressure scenarios (3+ combined pressures), loophole-closing, and rationalization-resistance techniques for the rare rigid skill.

## Bundled scripts

- `scripts/scaffold_skill.sh` — creates `<name>/` with a pre-filled SKILL.md, the standard subdirs, and a `.gitkeep`-free clean layout. Run it first; delete what you don't need.

## Templates

- `templates/SKILL.template.md` — the skeleton SKILL.md with section prompts and inline reminders of the rubric.
- `templates/config.example.json` — an annotated `config.json` showing a setup prompt and a preference field.

## Anti-patterns

- **Stating the obvious.** "Write clean, well-tested code." Claude does this already. Every such line dilutes the signal that matters.
- **Description as summary, not trigger.** "This skill helps with database work" never fires. "Use when querying the billing Postgres — the subscriptions table is append-only…" fires exactly when it should.
- **Railroading.** Over-specifying every step removes Claude's ability to adapt. Specify outcomes and constraints; trust the model on tactics.
- **One giant SKILL.md.** If it's over ~150 lines, you're not using progressive disclosure. Push detail into `reference/`.
- **No gotchas section.** The single highest-value section, and the easiest to skip because it's empty on day one. Add it anyway and grow it.
- **A skill that should be a hook.** "Every time X, do Y" is automatic behaviour — the harness runs hooks, not Claude. Skills are *discovered and chosen*, hooks *always fire*.
- **Inlining boilerplate Claude will rebuild each run.** Ship it as a script.
