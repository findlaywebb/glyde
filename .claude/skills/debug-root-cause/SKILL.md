---
name: debug-root-cause
description: Use when a bug, failing test, build break, or unexpected behaviour appears and a fix is about to be proposed — especially under time pressure, when the fix seems obvious, or when a previous fix didn't work. Triggers include "this test is failing", "why is this broken", "just try changing X", "quick fix for now", a second fix attempt after the first failed, or an error somewhere in a multi-component pipeline. Embodies root-cause-before-fix: no fix until the cause is traced; three failed fixes means question the architecture, not attempt a fourth.
---

# debug-root-cause

Makes Claude investigate to the root cause before proposing any fix, instead of pattern-matching the symptom to a plausible patch — and makes repeated fix failure a signal about the architecture, not a prompt for fix #4.

## The one principle

**No fix without a root-cause investigation first.** A symptom fix is a failure even when it makes the error go away. Systematic debugging is *faster* than guess-and-check, especially in an emergency.

## When to use

- Any test failure, bug, build break, or behaviour you didn't predict.
- Especially when guessing is tempting: time pressure, an "obvious" one-liner, a fix already tried that didn't work, or only partial understanding of the issue.

## When NOT to use

- The error message *states* the fix (missing import, typo'd name) and one change verifiably resolves it — fix it; don't perform an investigation ritual.
- You're designing tests for new code, not chasing a defect → TDD / the repo's test conventions.

## The procedure

Four phases, in order. Don't propose a fix while still in phases 1–3.

1. **Find the root cause.**
   - Read the error completely — stack trace, line numbers, error codes. It often contains the answer.
   - Reproduce reliably. Not reproducible → gather more data; never guess from one occurrence.
   - Check what changed: `git diff`, recent commits, new deps, config, environment.
   - **Multi-component systems** (API → service → DB; CI → build → deploy): before any fix, instrument each boundary — log what enters and exits each component — run once, and let the evidence say *which* component fails. Then investigate that one.
   - **Error deep in a call stack**: trace the bad value backwards — what produced it, what called that — until you reach the origin. Fix at the source, not where it surfaced.
2. **Find the pattern.** Locate similar *working* code in the codebase; read the reference implementation completely (not skimmed); list every difference between working and broken, however small.
3. **One hypothesis, one test.** State it: "I think X is the root cause because Y." Test it with the smallest possible change — one variable at a time. Wrong → new hypothesis; don't stack a second change on top. If you don't understand something, say so and investigate it — don't pretend.
4. **Fix the cause.**
   - Write a failing test that reproduces the bug *before* fixing (a one-off script if there's no harness). The repro test is the proof the fix works and the permanent regression guard.
   - One fix, addressing the identified cause. No while-I'm-here refactors mixed in.
   - Verify: repro test passes, nothing else broke.

## The 3-fix rule

If a fix fails, return to phase 1 with the new information. **If 3+ fixes have failed, stop — the architecture is in question, not the hypothesis.** The telltale pattern: each fix reveals new coupling somewhere else, or needs "massive refactoring" to land. Surface this to Findlay before attempting more fixes; "one more attempt" past this point is the trap.

## Red flags — back to phase 1

"Quick fix for now, investigate later" · "just try X and see" · several changes at once, then run tests · "it's probably X" · proposing fixes before tracing the data flow · listing fixes for an error you haven't reproduced · "I don't fully understand but this might work". Also from the user: "stop guessing", "is that not happening?" — both mean the investigation was skipped.

## Gotchas

- **"Simple bug, skip the process."** Simple bugs have root causes too, and the process is fast on them — reading the full error is step one, not bureaucracy.
- **"Emergency, no time."** Thrash is slower than method. Systematic runs minutes; guess-and-check runs hours and seeds new bugs.
- **Flaky / timing-dependent failures**: replace any arbitrary sleep/timeout with waiting on the actual condition, and treat "passes on retry" as *unreproduced*, not fixed.
- **Genuinely environmental/external after full investigation**: that's a legitimate finding — document what was ruled out, add handling (retry/timeout/clear error) and logging. But ~95% of "no root cause" is incomplete investigation.

## Provenance

Forked from `superpowers:systematic-debugging` (plugin v5.1.0), amended to house style: rituals and rationalization theatre dropped, phases and the 3-fix architecture rule kept.
