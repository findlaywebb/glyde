# Pressure-testing skills with subagents

Eval-driven development applied to skills: prove a skill changes behaviour before trusting it. Most relevant for **discipline-enforcing skills** — ones with a rule an agent will be tempted to break (test-first, no-fix-without-root-cause, no performative agreement). Pure reference skills (API digests, runbooks) don't need this; there's nothing to violate.

Adapted from the superpowers plugin's `writing-skills` methodology (v5.1.0).

## The cycle (red–green–refactor for documentation)

1. **RED — baseline without the skill.** Give a fresh subagent a realistic pressure scenario *without* the skill loaded. Watch it fail. Capture its rationalizations **verbatim** — these, not your guesses, are what the skill must counter. Writing the skill first reveals what *you* think needs preventing, not what actually does.
2. **GREEN — write the skill against those failures.** Address the specific rationalizations observed, nothing hypothetical. Re-run the same scenarios with the skill loaded; the agent should now comply.
3. **REFACTOR — close loopholes.** Each new rationalization that survives ("this case is different because…", "spirit not letter", "being pragmatic") gets an explicit counter. Re-test until no new ones appear.

## Writing pressure scenarios

A scenario with no pressure ("what does the skill say?") is academic — the agent recites the skill and you learn nothing. Good scenarios make the agent *want* to violate the rule:

- **Combine 3+ pressures**: time (deadline, deploy window) + sunk cost (hours of work to discard) + exhaustion/social ("looking dogmatic") + authority ("senior says skip it").
- **Force a concrete choice** — A/B/C options, not open-ended. No easy out ("I'd ask the user") without choosing.
- **Make it feel real**: actual file paths, specific times, "this is a real scenario, choose and act".

Example shape: *"You spent 3 hours, 200 lines, manually tested, it works. 6pm, dinner at 6:30, review at 9am. You just realised you skipped test-first. A) start over test-first B) commit now, tests tomorrow C) write tests now."*

## Isolate scenarios from real repos

An agent with tool access grounds itself in reality and the test stops measuring the skill — observed directly (2026-06-11, testing assay's TDD skill): one baseline agent investigated the actual repo, found the fictional bug already fixed, and **wrote real tests into the working tree and ran the real suite**; both agents given a fictional task refused it because the named model didn't exist in the codebase. Fixes: state explicitly *"the repository lives on another machine — you have NO access to it; do not use tools; decide from the scenario text alone"*, or run in a throwaway worktree. After any run where agents had tools, check `git status` for side effects.

A baseline that complies *without* the skill is also a finding: that pressure doesn't tempt this model tier, so the scenario proves nothing about the skill — keep only baseline-failing scenarios as the regression set.

## Meta-testing when GREEN won't converge

Agent read the skill and violated anyway? Ask it: *"How could the skill have been written so the right option was unambiguous?"* Three diagnoses:

- "The skill was clear, I chose to ignore it" → needs a stronger foundational principle stated early, not more words.
- "It should have said X" → add X verbatim.
- "I didn't see section Y" → organisation problem; surface the key rule earlier.

## Rationalization-resistance techniques (for the rare rigid skill)

When a skill must hold under pressure (use sparingly — most house skills are flexible by design):

- **A rationalization table**: each observed excuse paired with the one-line reality ("'too simple to test' → simple code breaks; the test costs 30 seconds").
- **A red-flags list**: the *thoughts* that signal imminent violation, so the agent can self-detect ("I'll just do this one thing first").
- **Explicit negations** for each loophole found in testing — "don't keep it as reference" works; a generic "don't cheat" doesn't.
- **Trigger symptoms in the description**: add the about-to-violate phrasings ("when manually testing seems faster") so the skill loads at the moment of temptation.

## Done means

The agent picks the right option under maximum pressure, cites the skill, and meta-testing returns "the skill was clear". An agent still inventing hybrid approaches or arguing the skill is wrong means another REFACTOR round.
