# Skill-authoring rubric

The canonical reference for what makes a Claude skill good. Distilled from Anthropic, "Lessons from building Claude Code: how we use skills" (2025) and house practice. `make-skill` writes against it; `improve-skill` audits against it.

## The governing test: does it change behaviour?

A skill earns its existence only by encoding knowledge that **pushes Claude out of its default behaviour**. Before any line goes in, ask: *would Claude do this anyway?* If yes, cut it. The best skills are dense with the non-obvious; the worst pad general advice Claude already follows.

This is why "write clean code", "add tests", "handle errors gracefully" are forbidden — not because they're wrong, but because they're free. They cost context and return nothing.

## The nine categories

Every good skill fits cleanly into **one** of these. A skill that straddles several is confusing to select and is usually two skills.

1. **Library and API reference** — how to use an SDK/CLI, with the gotchas and edge cases the docs gloss over.
2. **Product verification** — testing/verification flows, often driving playwright or tmux. *Highest measured quality impact — invest here.*
3. **Data fetching and analysis** — connections to monitoring stacks, query patterns, dashboards.
4. **Business process and team automation** — standups, status posts, recurring workflows.
5. **Code scaffolding and templates** — framework boilerplate generation.
6. **Code quality and review** — style enforcement, peer-review assistance.
7. **CI/CD and deployment** — build/test/deploy flows.
8. **Runbooks** — multi-tool investigation → structured report.
9. **Infrastructure operations** — routine maintenance behind guardrails.

If a candidate skill fits none of these, question whether it should exist — or whether it's really a hook, an MCP, a workflow, or an instructions doc.

## The description — the highest-leverage line

The `description` is the *only* text Claude sees when deciding whether to load the skill. It is a **trigger, not a summary**.

Strong descriptions:
- Open with **"Use when…"** and name concrete situations.
- Quote **verbatim phrases** the user might type: `Triggers include "make a ticket", "draft a ticket"`.
- Name the *symptom*, not just the topic: not "database skill" but "Use when querying the billing Postgres — the subscriptions table is append-only".
- End with the **one-line mental model** the skill embodies, if it has one.

Weak descriptions are summaries ("This skill helps with X"), topic labels ("Database utilities"), or anything a human would write for a README. Those under-trigger — the skill exists but never loads.

Length: long is fine. The description is cheap to read and the cost of *not triggering* dwarfs the cost of a few extra tokens. Pack it with triggers.

## The body — structure for scanning

A SKILL.md is read by a model mid-task. Optimise for fast selection of the right section:

- **Lead with the core move** — "The one principle" / "The core move". One bold sentence the rest hangs off.
- **"When to use" + "When NOT to use"** — the NOT list is as valuable as the use list; it prevents misfires and points to the right alternative skill.
- **Procedure or knowledge** — numbered steps for a workflow; structured headings for reference knowledge.
- **Anti-patterns** — the failure modes, named. Often the most-read section.
- Keep the SKILL.md itself **scannable and short** (rule of thumb: under ~150 lines). Everything else is progressive disclosure.

## The gotchas section — highest-signal content

> "The subscriptions table is append-only. The row you want is the one with the highest version, not the most recent created_at."

That single sentence is worth more than a page of generalities. A gotchas section is a list of concrete traps + the fix, ideally harvested from real failures. It's empty on day one — that's honest. Grow it every time the skill (or you) gets burned. If a skill has *no* gotchas after real use, suspect it isn't encoding anything non-obvious.

## Progressive disclosure — the skill is a folder

A skill is a *folder*, not a markdown file. Use the filesystem as a context-loading mechanism:

- `reference/*.md` — detailed signatures, alternative approaches, background research. Each file stands alone and is read only when the task needs it. Split by concern so Claude loads one, not all.
- `scripts/` — helper code Claude runs or composes. Ship boilerplate here so Claude spends tokens on composition, not reconstruction. Keep dependency-light and put usage in the file header.
- `templates/` — fill-in artifacts the skill produces (design docs, configs, reports).
- The SKILL.md points to these explicitly ("…in `reference/foo.md`") so Claude knows what's available and when to read it.

## Configuration and memory

- `config.json` — only if the skill needs setup. Prompt for required config; use the `AskUserQuestion` tool for structured choices rather than free-text where options are known.
- `${CLAUDE_PLUGIN_DATA}` — the env var for persistent skill data. Use an append-only log or a small JSON file so the skill can read its own history ("what changed since last run?"). Only add memory if the skill genuinely needs it.

## On-demand hooks

A skill can register a hook that activates *only while the skill is in use* — e.g. a `/careful` mode that blocks destructive commands during a risky runbook. Distinct from always-on settings.json hooks. Reach for this when a skill needs a guardrail scoped to its own execution.

## Distribution

- **Repo-based** — check into `./.claude/skills` for a small team in a few repos.
- **Marketplace-based** — an internal plugin marketplace for org-wide discovery and install, with setup flows. Anthropic's path: a skill starts in a sandbox folder, earns organic traction, then PRs into the main marketplace.
- Skills can reference each other by name; Claude invokes a named skill if installed. There's no native dependency manager yet — composition-by-naming works in practice, but don't build deep dependency chains.

## Measurement

A `PreToolUse` hook that logs skill usage reveals which skills are popular and which **under-trigger relative to expectation** — the latter usually means the description is a summary, not a trigger. Fix the description, not the body.

## Final quality checklist

Before declaring a skill done:

- [ ] **Behaviour test:** every section changes what Claude does; nothing restates the default.
- [ ] **One category:** the skill fits cleanly into a single one of the nine.
- [ ] **Description is a trigger:** opens "Use when…", names situations, quotes verbatim phrases.
- [ ] **When-NOT-to-use present**, and points to the right alternative (skill / hook / workflow / MCP / instructions).
- [ ] **Gotchas section exists** (even if thin), built from real traps.
- [ ] **Progressive disclosure:** SKILL.md is scannable (~<150 lines); detail lives in `reference/`.
- [ ] **Scripts bundled** for any boilerplate Claude would otherwise rebuild.
- [ ] **Frontmatter is just `name` + `description`**; name is kebab-case and matches the folder.
- [ ] **Anti-patterns section** names the real failure modes.
- [ ] Reads like the other skills in the library (tone, structure, density).
