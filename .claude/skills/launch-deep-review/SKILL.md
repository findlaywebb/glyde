---
name: launch-deep-review
description: Use when you want an exhaustive, context-isolated pre-submission review of your own changes — gathers ticket ACs, scopes the diff, launches 7 specialist reviewer agents in parallel, then a synthesiser to produce one review document. Triggers include "deep review this", "exhaustive review", "review MEM-924 thoroughly", "full panel review before I push". Preferred over code-review-deep (this is context-isolated and parallel). For a fast single-pass self-review use review-code; for the agent-team variant with peer cross-review use launch-team-review.
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
  - Agent
  - Write
  - TaskCreate
  - TaskUpdate
  - TaskList
---

# Launch Deep Review — Multi-Agent Orchestrator

Prepare context, launch 7 specialist reviewer agents in parallel, then a synthesiser to consolidate findings into a final review document.

## Inputs

`$ARGUMENTS` should include:

- **Ticket ID** (optional) — e.g. `MEM-924`. If provided, the ticket is read for acceptance criteria and goals.
- **Review scope** (optional) — e.g. `HEAD~2`, `uncommitted`, `abc123..HEAD`. Defaults to uncommitted changes.
- **Output directory** (optional) — e.g. `reviews/phase5.5/`. Defaults to `reviews/<IDENTIFIER>/`.
- **Additional context** (optional) — free text the user provides about the change, goals, or what to focus on.

Parse `$ARGUMENTS` flexibly. Examples:

```
/launch-deep-review MEM-924
/launch-deep-review MEM-924 HEAD~3
/launch-deep-review MEM-924 uncommitted + HEAD~1 — focus on the new version_target module
/launch-deep-review HEAD~5 — review the kafka consumer refactor
```

---

## Phase 1 — Gather Context

### 1a. Determine review scope

If the user specified a scope, use it. Otherwise default to uncommitted changes.

Run in parallel:
```bash
git diff HEAD --stat          # uncommitted summary
git log --oneline -10         # recent commits for context
```

If the user mentioned specific commits or a range, also run:
```bash
git log --oneline <range>
git diff --stat <range>
```

Determine:
- The exact diff command for the scope (e.g. `git diff HEAD`, `git diff HEAD~2`)
- The full diff output
- The list of changed files (excluding `docs/schemas/` and `uv.lock`)
- Which of those are test files (paths containing `/tests/`)
- Lines added/removed count

### 1b. Gather ticket context (if ticket ID provided)

Read the ticket file:
```
~/Documents/tickets/jira/<TICKET>.md
```

If it doesn't exist, check `~/Documents/FMP/tickets/jira/<TICKET>.md` as fallback.

From the ticket, extract:
- **Summary** — the ticket title/summary line
- **Acceptance criteria** — bulleted list of ACs. If the ticket uses a checklist format, extract those items
- **Goals** — what the ticket is trying to achieve at a high level

**Critical: Do NOT extract implementation details, design decisions, or technical approach from the ticket.** The reviewer should evaluate the code against goals/ACs, not against a prescribed implementation. If the ticket describes a specific approach, omit that from the brief.

### 1c. Filter caller context

The user may have provided additional context in their message. Filter it:

- **Include**: Goals, what changed, what to focus on, which modules matter, known constraints
- **Exclude**: Implementation justifications, "I chose X because Y" — reviewers should judge the approach independently

### 1d. Determine review identifier

Build `<IDENTIFIER>` for file naming:
1. Start with the ticket ID if available (e.g. `MEM-924`)
2. Append a short kebab-case descriptor (e.g. `version-target`, `consumer-refactor`)
3. If no ticket, use just the descriptor or commit range

### 1e. Determine output directory

If the user specified an output directory (e.g. `reviews/phase5.5/`), use that. Otherwise default to `reviews/<IDENTIFIER>/`.

Store this as `<OUTPUT_DIR>` for use in agent briefs. All sub-reports and the final review go in this directory.

```bash
mkdir -p <OUTPUT_DIR>
```

### 1f. Create progress tasks

Create a task for each phase so the user can track progress.

---

## Phase 2 — Launch 7 Specialist Agents (parallel)

Compose a brief for each agent. Every agent receives the **same base brief**:

```markdown
## Review Identifier
<IDENTIFIER>

## Output Path
<OUTPUT_DIR>/<IDENTIFIER>-<perspective>.md

## Ticket
<TICKET>: <summary>

## Acceptance Criteria / Goals
- <AC 1>
- <AC 2>

## Changed Files
<list of changed file paths>

## Test Files
<list of test file paths from the diff>

## Diff
<full diff output>

## Context
<Filtered caller context — goal-oriented, not implementation-biased>
```

Launch **all 7 agents in a single message** (one Agent tool call per agent, all in parallel):

| Agent | subagent_type | Model | Staging file suffix |
|-------|--------------|-------|-------------------|
| Architecture Reviewer | `deep-review-architecture` | opus | `-architecture.md` |
| Correctness Auditor | `deep-review-correctness` | opus | `-correctness.md` |
| DRY & Structure Analyst | `deep-review-dry-structure` | sonnet | `-dry-structure.md` |
| Production Readiness | `deep-review-production` | sonnet | `-production.md` |
| Test Depth Analyst | `deep-review-tests` | sonnet | `-tests.md` |
| Best Practices Researcher | `deep-review-best-practices` | sonnet | `-best-practices.md` |
| Code Excellence Reviewer | `deep-review-excellence` | opus | `-excellence.md` |

**Run all 7 in the background** so they execute concurrently. You will be notified as each completes.

**CRITICAL — Do not respond between agent completions.** Each background agent fires a notification when it completes, which unavoidably consumes input tokens (platform limitation, no batch/defer option exists). To minimise waste: do NOT output any text to the user when an agent completes (no "X complete, waiting for Y..."). Produce zero output tokens. Simply wait until ALL 7 agents have completed, then proceed to Phase 3. The only acceptable output between launch and all-complete is if an agent fails and you need to report the failure.

**Important**: Each agent writes its own sub-report to the output directory. Do NOT pass the diff in-line if it's very large (>500 lines) — instead tell the agent the diff command to run and let it gather the diff itself.

---

## Phase 3 — Launch Synthesiser

Once all 7 agents have completed (or you've been notified they're done), launch the synthesiser agent in the **foreground**:

```
Agent(subagent_type="deep-review-synthesiser", prompt=<synthesiser brief>)
```

The synthesiser brief:

```markdown
## Review Identifier
<IDENTIFIER>

## Output Path
<OUTPUT_DIR>/<IDENTIFIER>-deep.md

## Sub-reports Directory
<OUTPUT_DIR>/

## Changed Files
<list of changed file paths>

## Lines Changed
+<added> / -<removed>

## Ticket
<TICKET>: <summary>

## Acceptance Criteria / Goals
- <AC 1>
- <AC 2>

## Sub-reports to read
- <OUTPUT_DIR>/<IDENTIFIER>-architecture.md
- <OUTPUT_DIR>/<IDENTIFIER>-correctness.md
- <OUTPUT_DIR>/<IDENTIFIER>-dry-structure.md
- <OUTPUT_DIR>/<IDENTIFIER>-production.md
- <OUTPUT_DIR>/<IDENTIFIER>-tests.md
- <OUTPUT_DIR>/<IDENTIFIER>-best-practices.md
- <OUTPUT_DIR>/<IDENTIFIER>-excellence.md
```

The synthesiser will:
1. Read all sub-reports
2. De-duplicate and merge findings
3. Calibrate severity
4. Write the final review to `<OUTPUT_DIR>/<IDENTIFIER>-deep.md`

---

## Phase 4 — Clean up and report

### 4a. Clean up sub-reports (optional)

Sub-reports live alongside the final review in `<OUTPUT_DIR>/`. They can be kept for reference or removed:

```bash
rm -f <OUTPUT_DIR>/<IDENTIFIER>-architecture.md <OUTPUT_DIR>/<IDENTIFIER>-correctness.md \
      <OUTPUT_DIR>/<IDENTIFIER>-dry-structure.md <OUTPUT_DIR>/<IDENTIFIER>-production.md \
      <OUTPUT_DIR>/<IDENTIFIER>-tests.md <OUTPUT_DIR>/<IDENTIFIER>-best-practices.md \
      <OUTPUT_DIR>/<IDENTIFIER>-excellence.md
```

By default, **keep them** — they contain useful detail beyond what the synthesis captures. Only delete if the user asks.

### 4b. Report to user

Present a concise summary (10 lines or fewer):

1. The path to the review document
2. A count of findings by severity (Blocking / Should Fix / Nit / Excellence)
3. Whether any auto-fixes were applied
4. The big-picture message from the review

Do NOT reproduce the full review — the user can read the file.

---

## Common Mistakes to Avoid

1. **Sequential agent launches** — all 7 specialists MUST launch in a single message with 7 parallel Agent tool calls
2. **Launching synthesiser too early** — wait for ALL 7 agents to complete before launching
3. **Responding between agent completions** — do NOT output text each time an agent completes ("Architecture done, 6 remaining..."). Each notification unavoidably costs input tokens (platform limitation), but you can avoid wasting output tokens by producing zero output. Stay silent until all 7 are done, then proceed to Phase 3
4. **Passing implementation bias** — the brief must not contain "the code does X because Y"
5. **Huge inline diffs** — if the diff is >500 lines, tell agents to run the diff command themselves
6. **Verbose reporting** — the user wants 10 lines, not a reproduction of the review
7. **Agents returning text instead of writing files** — agents MUST use the Write tool to write their report to the output path. If an agent returns its report as text output instead, the orchestrator must write it to disk before launching the synthesiser
