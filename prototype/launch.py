#!/usr/bin/env python3
"""Launch the RSVP web reader on a markdown/text file.

Reads the source file, lightly strips markdown to readable prose, embeds the
text into a one-shot copy of ``reader.html``, and opens it in the browser. No
server is started, so there are no CORS issues — the text is baked into the
page.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
READER = HERE / "reader.html"
DEFAULT_STREAM = HERE / "stream.md"
INJECT_MARKER = "const INJECTED_TEXT = null; // __RSVP_INJECT__"


def strip_markdown(text: str) -> str:
    """Reduce markdown to skim-readable prose, preserving paragraph breaks."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Drop YAML frontmatter.
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.DOTALL)
    # Drop fenced code blocks entirely — they read terribly word-by-word.
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    out_lines: list[str] = []
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("|") and s.endswith("|"):
            continue  # skip table rows
        s = re.sub(r"^#{1,6}\s*", "", s)  # headings
        s = re.sub(r"^>\s*", "", s)  # blockquotes
        s = re.sub(r"^[-*+]\s+", "", s)  # bullet markers
        s = re.sub(r"^\d+\.\s+", "", s)  # numbered markers
        s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)  # images
        s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)  # links -> text
        s = re.sub(r"[*_`~]", "", s)  # emphasis / inline code marks
        out_lines.append(s)
    text = "\n".join(out_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)  # collapse blank runs
    return text.strip()


def build_page(text: str) -> str:
    """Inject ``text`` into the reader template and return the HTML."""
    html = READER.read_text(encoding="utf-8")
    if INJECT_MARKER not in html:
        raise RuntimeError(f"inject marker missing from {READER}")
    payload = f"const INJECTED_TEXT = {json.dumps(text)}; // __RSVP_INJECT__"
    return html.replace(INJECT_MARKER, payload)


def open_in_browser(path: Path) -> None:
    """Open the generated page, preferring macOS ``open``."""
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        webbrowser.open(path.as_uri())


def main(argv: list[str] | None = None) -> int:
    """Parse args, build the page, and launch the reader."""
    parser = argparse.ArgumentParser(description="Launch the RSVP reader on a file.")
    parser.add_argument(
        "file",
        nargs="?",
        default=str(DEFAULT_STREAM),
        help=f"Markdown/text file to read (default: {DEFAULT_STREAM}).",
    )
    args = parser.parse_args(argv)

    src = Path(args.file).expanduser()
    if not src.is_file():
        print(f"rsvp: no such file: {src}", file=sys.stderr)
        return 1

    text = strip_markdown(src.read_text(encoding="utf-8"))
    if not text:
        print(f"rsvp: {src} has no readable text", file=sys.stderr)
        return 1

    page = build_page(text)
    out = Path(tempfile.gettempdir()) / "rsvp_reader.html"
    out.write_text(page, encoding="utf-8")
    words = len(text.split())
    print(f"rsvp: {words} words from {src} → opening reader")
    open_in_browser(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
