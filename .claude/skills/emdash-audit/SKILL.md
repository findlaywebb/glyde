---
name: emdash-audit
description: Strip em-dashes (`—`) and en-dashes (`–`) from human-facing prose. Findlay's rule is zero em-dashes in anything a person reads — externally-facing content, messages to other people, and vault notes meant for reading. Use after writing or editing PR descriptions, Jira tickets, emails/messages, READMEs and public docs, and vault reference notes. Do NOT run it on agent-facing files (CLAUDE.md, rules, instructions, SKILL.md, internal planning docs an agent executes against) — em-dashes there are harmless and stripping them is wasted effort. The script handles the safe mechanical patterns, then surfaces the rest for contextual rewriting.
model: sonnet
effort: low
allowed-tools:
  - Read
  - Edit
  - Bash
---

# Em-dash audit

Findlay's writing convention is **zero em-dashes** and **zero en-dashes**. Em-dashes are a tell of generated-feeling prose; the goal is to force better punctuation choices.

This skill enforces that rule on any prose file (docs, tickets, plans, PR descriptions, commit message drafts).

## When to invoke

The test is **audience, not file type**: will a *human* read this as finished prose? If yes, strip em-dashes. Run after writing or substantially editing:

- PR descriptions (before posting) and commit-message drafts
- Jira tickets and anything else other people read
- Emails, Slack/Teams messages, any communication to a person
- READMEs, public docs, blog posts, anything externally facing
- Vault notes meant for reading (refined reference notes, write-ups)

Self-trigger after long-form human-facing writing without being asked - the `~/.claude/toolkit/instructions/writing-style.md` rule expects this as a post-writing step.

## When NOT to invoke

Files whose primary reader is an *agent*, not a person. Em-dashes there are harmless and stripping them is wasted effort (and they're house style in skill files):

- CLAUDE.md, rules, and instruction files
- Skill files (`SKILL.md` and their `reference/` docs)
- Internal planning docs an agent executes against (e.g. most of `docs/plans/`) - "plan-based", not reading material
- Source files (`.py` etc.) - other conventions apply; em-dashes can be legitimate inside strings/comments

NB a file can flip category: an internal plan that gets shared with a person, or a vault note promoted to a shared doc, becomes human-facing - run it then.

## Usage

```bash
python ~/.claude/toolkit/skills/emdash-audit/strip_emdashes.py FILE [FILE ...]
```

The script:

1. Replaces every en-dash with a plain hyphen-minus (`-`). No exceptions.
2. Mechanically converts the safe label-separator em-dash patterns to hyphen-minus:
   - `**bold** —` (and `**bold** (asides) —`) → `**bold** -`
   - `` `code` —`` → `` `code` -``
   - `### Step N —` / `### Phase N —` → `-`
   - `# Title — subtitle` (top-level heading) → `# Title:`
   - `- [Link](path) —` → `- [Link](path) -`
   - `| - |` (empty table-cell placeholder) → `| - |`
3. Reports remaining em-dashes per file with line numbers.
4. Exits non-zero if any em-dashes survived the mechanical pass.

Add `--check` to do a dry-run without writing.

## Workflow

1. Run the script on the files. Watch the output: it prints `replaced N, M remaining` per file plus the line content of each surviving em-dash.
2. For each remaining em-dash, **edit the file** to apply the right punctuation:
   - **Aside / supplementary clause** → comma: `the year, dev or debugging`
   - **Parenthetical** → parens: `the year (dev or debugging)`
   - **Two related thoughts** → semicolon: `safe to run mid-batch; it ignores active partitions`
   - **Introducing a definition / consequence** → colon: `Idempotent: re-running won't overwrite state`
   - **Two independent thoughts** → period split: `… is the primary job. It materialises a single partition.`
3. Re-run the script to confirm zero remaining.

## Notes

- **No keep-or-replace.** Earlier versions of this skill let some em-dashes survive on a case-by-case judgment. That convention has been replaced. Zero is the rule. Mechanical first, contextual rewriting second, no exceptions.
- The script is idempotent. Running it twice on the same file is safe.
- En-dashes (`–`) are also stripped unconditionally; they have the same generated-prose smell.
- Hyphen-minus (`-`) is the only dash that survives.
- The script masks inline-code spans (`` `...` ``) and fenced code blocks (```` ``` ````) before counting, so em-dashes inside code samples (e.g. showing the literal character) do not count.
- Run it on human-facing prose, not agent-facing files (see When to / When NOT to invoke above). The audience is the test, not the file extension or the `.md` suffix.

## Related

- `~/.claude/toolkit/instructions/writing-style.md` - general writing voice rules; references this skill.
- Memory: `feedback-no-em-dashes` (project-scoped) records the underlying preference.
