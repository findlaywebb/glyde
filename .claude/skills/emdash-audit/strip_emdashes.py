#!/usr/bin/env python3
"""Strip em-dashes (—) and en-dashes (–) from prose files.

Findlay's writing convention is zero em-dashes and zero en-dashes. This script
applies the safe mechanical replacements that account for ~70% of typical
occurrences, then reports the remaining em-dashes for contextual rewriting.

Mechanical replacements (label-separator pattern → plain hyphen-minus):

    **bold** —          → **bold** -
    `code` —            → `code` -
    ### Step N —        → ### Step N -
    ### Phase N —       → ### Phase N -
    # Title — subtitle  → # Title: subtitle
    - [link](path) —    → - [link](path) -
    - **bold** (asides) — → - **bold** (asides) -
    | — |               → | - |        (empty table-cell placeholders)

All en-dashes are unconditionally converted to plain hyphen-minus.

Remaining em-dashes are prose uses (asides, parenthetical clauses, joined
clauses, etc.) that need contextual rewriting per Findlay's rule:
    aside              → comma (,)
    parenthetical      → parentheses (...)
    joined thought     → semicolon (;)
    definition         → colon (:)
    independent clause → period split (.)

Usage:
    python strip_emdashes.py FILE [FILE ...]
    python strip_emdashes.py --check FILE [FILE ...]   # exit non-zero if any remain

Exits non-zero if em-dashes remain in any input file after the mechanical pass.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# (pattern, replacement) - order-insensitive; applied per-line in sequence.
MECHANICAL_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # After closing **bold**, optionally followed by parens
    (re.compile(r"(\*\*[^*\n]+?\*\*)(\s*\([^)]*\))? — "), r"\1\2 - "),
    # After closing `inline code`
    (re.compile(r"(`[^`\n]+?`) — "), r"\1 - "),
    # Heading list-step / list-phase: "### Step N — " or "### Phase N — "
    (re.compile(r"^(#+\s+(?:Step|Phase)\s+\d+) — "), r"\1 - "),
    # Top-level heading with subtitle: "# Title — sub" → "# Title: sub"
    (re.compile(r"^(#\s+[^—\n]+?) — "), r"\1: "),
    # Bullet list with link label: "- [Link](url) — desc"
    (re.compile(r"^(\s*[-*]\s+\[[^\]]+\]\([^)]+\)) — "), r"\1 - "),
    # Empty table-cell placeholder: "| — |"
    (re.compile(r"\|\s*—\s*\|"), "| - |"),
    # Table cell ending with empty placeholder (final cell): "... | — |"
    # (already covered by above; placeholder for future patterns)
]


INLINE_CODE = re.compile(r"`[^`\n]+`")
FENCED_BLOCK = re.compile(r"^```", re.MULTILINE)


def _mask_code_spans(text: str) -> tuple[str, dict[str, str]]:
    """Replace inline code and fenced blocks with opaque placeholders.

    Em-dashes inside code are demonstrating the character, not using it as
    prose. Mask them out so the mechanical pass and the count both ignore them.
    """
    placeholders: dict[str, str] = {}

    # Mask fenced code blocks first
    lines = text.split("\n")
    in_fence = False
    masked_lines: list[str] = []
    for line in lines:
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            masked_lines.append(line)
            continue
        if in_fence:
            key = f"\x00FENCED{len(placeholders)}\x00"
            placeholders[key] = line
            masked_lines.append(key)
        else:
            masked_lines.append(line)
    masked = "\n".join(masked_lines)

    # Mask inline code spans
    def _sub(m: re.Match[str]) -> str:
        key = f"\x00INLINE{len(placeholders)}\x00"
        placeholders[key] = m.group(0)
        return key

    masked = INLINE_CODE.sub(_sub, masked)
    return masked, placeholders


def _unmask(text: str, placeholders: dict[str, str]) -> str:
    for key, value in placeholders.items():
        text = text.replace(key, value)
    return text


def strip_dashes(text: str) -> tuple[str, int]:
    """Apply mechanical replacements and unconditional en-dash conversion.

    Em-dashes inside inline code (`...`) and fenced code blocks (```...```) are
    left alone - they're examples, not prose.

    Returns (new_text, replacements_made).
    """
    masked, placeholders = _mask_code_spans(text)
    count_before = masked.count("—") + masked.count("–")

    # En-dashes are always replaced in prose. No legitimate use.
    masked = masked.replace("–", "-")

    # Apply line-by-line for patterns anchored at line start
    new_lines = []
    for line in masked.splitlines(keepends=True):
        for pat, repl in MECHANICAL_PATTERNS:
            line = pat.sub(repl, line)
        new_lines.append(line)
    new = _unmask("".join(new_lines), placeholders)

    # Count remaining in prose (re-mask to get accurate count)
    final_masked, _ = _mask_code_spans(new)
    count_after = final_masked.count("—") + final_masked.count("–")
    return new, count_before - count_after


def report_remaining(path: Path, text: str) -> list[tuple[int, str]]:
    """Return [(line_number, line_content)] for prose lines that still contain em-dashes.

    Em-dashes inside inline-code spans or fenced code blocks do not count.
    """
    masked, _ = _mask_code_spans(text)
    out: list[tuple[int, str]] = []
    for i, (raw_line, masked_line) in enumerate(
        zip(text.splitlines(), masked.splitlines(), strict=False), start=1
    ):
        if "—" in masked_line:
            out.append((i, raw_line.rstrip()))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="+", help="Files to process")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Do not write changes; exit non-zero if any em-dashes remain",
    )
    args = parser.parse_args()

    total_remaining = 0
    for path_str in args.files:
        path = Path(path_str)
        if not path.exists():
            print(f"WARN: {path} does not exist, skipping", file=sys.stderr)
            continue

        original = path.read_text()
        new_text, replaced = strip_dashes(original)

        if not args.check and new_text != original:
            path.write_text(new_text)

        remaining = report_remaining(path, new_text)
        total_remaining += len(remaining)

        # Per-file summary
        action = "would replace" if args.check else "replaced"
        print(f"{path}: {action} {replaced}, {len(remaining)} remaining")

        for lineno, line in remaining:
            # Highlight the em-dash visually with a marker for the reader
            print(f"  {lineno}: {line}")

    if total_remaining:
        print(
            f"\n{total_remaining} em-dash(es) remain. Rewrite contextually:\n"
            "  aside              → comma (,)\n"
            "  parenthetical      → parentheses (...)\n"
            "  joined thought     → semicolon (;)\n"
            "  definition         → colon (:)\n"
            "  independent clause → period split (.)",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
