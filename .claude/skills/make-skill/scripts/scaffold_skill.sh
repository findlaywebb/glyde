#!/usr/bin/env bash
# scaffold_skill.sh — create a new skill folder with the standard layout.
#
# Usage:
#   scaffold_skill.sh <skill-name> [target-dir]
#
#   <skill-name>   kebab-case, becomes the folder name and the frontmatter `name`.
#   [target-dir]   override where to create it (e.g. ./.claude/skills for a
#                  repo-local skill). When omitted, the skill is created in the
#                  VERSION-CONTROLLED toolkit (~/.claude/toolkit/skills) and a
#                  symlink is added into ~/.claude/skills so Claude discovers it.
#                  This is the curated home — do NOT create skills directly in
#                  ~/.claude/skills (they'd be untracked by git).
#
# Creates:
#   <target>/<skill-name>/SKILL.md      pre-filled from the template
#   <target>/<skill-name>/reference/    (empty — progressive disclosure)
#   <target>/<skill-name>/scripts/      (empty — bundled helpers)
#   <target>/<skill-name>/templates/    (empty — produced artifacts)
#
# Delete the subdirs you don't use. The script refuses to overwrite an existing skill.
set -euo pipefail

name="${1:-}"
toolkit_skills="$HOME/.claude/toolkit/skills"

if [[ -z "$name" ]]; then
  echo "usage: scaffold_skill.sh <skill-name> [target-dir]" >&2
  exit 2
fi
if [[ ! "$name" =~ ^[a-z0-9]+(-[a-z0-9]+)*$ ]]; then
  echo "error: skill name must be kebab-case (got '$name')" >&2
  exit 2
fi

# Decide the home. Explicit target → use it, no symlink (repo-local skill).
# Default → the toolkit (version-controlled), with a symlink into ~/.claude/skills.
symlink_into=""
if [[ -n "${2:-}" ]]; then
  target="$2"
elif [[ -d "$toolkit_skills" ]]; then
  target="$toolkit_skills"
  symlink_into="$HOME/.claude/skills"
else
  # No toolkit checkout — fall back to the live dir (e.g. a fresh machine).
  target="$HOME/.claude/skills"
fi

dest="$target/$name"
if [[ -e "$dest" ]]; then
  echo "error: $dest already exists — use improve-skill to edit it" >&2
  exit 1
fi

mkdir -p "$dest/reference" "$dest/scripts" "$dest/templates"

cat > "$dest/SKILL.md" <<EOF
---
name: $name
description: Use when <concrete situation> — <the non-obvious detail>. Triggers include "<phrase>", "<phrase>", "<phrase>". <One-line stance the skill embodies.>
---

# $name

<One sentence: what this skill makes Claude do that it wouldn't do by default.>

## The one principle

**<The single bold sentence the rest hangs off.>**

## When to use

- <situation>
- <situation>

## When NOT to use

- <case> → <the right alternative: another skill / a hook / a workflow / an instructions doc>

## The procedure

1. <step — outcome and constraint, not micro-tactics>

## Gotchas

- <concrete trap> → <the fix>. (Grow this from real failures. Thin is honest; empty after real use is a smell.)

## Anti-patterns

- <named failure mode>
EOF

# Wire the toolkit skill into the live tree via a relative symlink (matches the
# existing convention, e.g. ~/.claude/skills/design-agent -> ../toolkit/skills/design-agent).
linked_note=""
if [[ -n "$symlink_into" ]]; then
  if [[ ! -e "$symlink_into/$name" ]]; then
    ln -s "../toolkit/skills/$name" "$symlink_into/$name"
    linked_note=" (symlinked into ~/.claude/skills/$name)"
  fi
fi

echo "Scaffolded skill at: $dest$linked_note"
echo "Next:"
echo "  1. Rewrite the description as a TRIGGER (see reference/description-examples.md)."
echo "  2. Fill the body with signal only — cut anything Claude does by default."
echo "  3. Delete the reference/ scripts/ templates/ subdirs you don't use."
echo "  4. Audit with the improve-skill rubric before declaring it done."
echo "  5. Commit the new skill in the toolkit repo (git -C ~/.claude/toolkit add skills/$name)."
