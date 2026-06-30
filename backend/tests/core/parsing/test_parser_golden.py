"""Golden-vector tests pinning the Glyde-Markdown parse contract.

Each vector is a pinned literal: a syntax string and the exact timeline shape it
must parse to. A wrong parser poisons every downstream surface, so the parse is
pinned here and extended whenever ``--cov`` reveals an uncovered branch.
"""

import pytest

from glyde.core import Block, Pause, ProseSegment, Segment
from glyde.core.parsing import parse_glyde_markdown


def _shape(segments: list[Segment]) -> list[tuple[object, ...]]:
    """Reduce parsed segments to compact comparable tuples for golden assertions."""
    shapes: list[tuple[object, ...]] = []
    for segment in segments:
        if isinstance(segment, ProseSegment):
            shapes.append(("prose", segment.role, [(t.text, t.emphasis) for t in segment.tokens]))
        elif isinstance(segment, Pause):
            shapes.append(("pause", segment.reason))
        else:
            block: Block = segment
            shapes.append(("block", block.kind, block.content, block.lang, block.lead, block.alt))
    return shapes


_VECTORS: list[tuple[str, str, list[tuple[object, ...]]]] = [
    (
        "heading_strong_eof",
        "## Ship it\nWe ==shipped== it.",
        [
            ("prose", "heading", [("Ship", "none"), ("it", "none")]),
            ("prose", "body", [("We", "none"), ("shipped", "strong"), ("it", "none")]),
        ],
    ),
    (
        "clause_sentence_paragraph",
        "Yes, it works. New idea.\n\nNext.",
        [
            ("prose", "body", [("Yes", "none")]),
            ("pause", "clause"),
            ("prose", "body", [("it", "none"), ("works", "none")]),
            ("pause", "sentence"),
            ("prose", "body", [("New", "none"), ("idea", "none")]),
            ("pause", "paragraph"),
            ("prose", "body", [("Next", "none")]),
        ],
    ),
    (
        "unordered_list",
        "- one\n- two\n- three",
        [
            ("prose", "list_item", [("one", "none")]),
            ("pause", "clause"),
            ("prose", "list_item", [("two", "none")]),
            ("pause", "clause"),
            ("prose", "list_item", [("three", "none")]),
        ],
    ),
    (
        "ordered_list_em_and_code",
        "1. run *fast* now\n2. use `grep`",
        [
            ("prose", "list_item", [("run", "none"), ("fast", "em"), ("now", "none")]),
            ("pause", "clause"),
            ("prose", "list_item", [("use", "none"), ("grep", "code")]),
        ],
    ),
    (
        "code_fence_with_lead",
        "Run this.\n\n```py\nx = 1\n```",
        [
            ("prose", "body", [("Run", "none"), ("this", "none")]),
            ("pause", "block_ahead"),
            ("block", "code", "x = 1", "py", "Run this", None),
        ],
    ),
    (
        "table_at_start_no_lead",
        "| a | b |\n| --- | --- |\n| 1 | 2 |",
        [
            ("pause", "block_ahead"),
            ("block", "table", "| a | b |\n| --- | --- |\n| 1 | 2 |", None, None, None),
        ],
    ),
    (
        "image_with_lead",
        "See below.\n\n![a cat](cat.png)",
        [
            ("prose", "body", [("See", "none"), ("below", "none")]),
            ("pause", "block_ahead"),
            ("block", "image", "cat.png", None, "See below", "a cat"),
        ],
    ),
    (
        "math_block",
        "$$E=mc^2$$",
        [("pause", "block_ahead"), ("block", "math", "E=mc^2", None, None, None)],
    ),
    (
        "quote_block",
        "> wisdom here",
        [("pause", "block_ahead"), ("block", "quote", "wisdom here", None, None, None)],
    ),
    (
        "note_block",
        ":::pause\nbreathe\n:::",
        [("pause", "block_ahead"), ("block", "note", "breathe", None, None, None)],
    ),
    (
        "em_underscore_no_terminator",
        "use _this_ thing",
        [("prose", "body", [("use", "none"), ("this", "em"), ("thing", "none")])],
    ),
    (
        "unmatched_delimiter_is_literal",
        "a ==b c",
        [("prose", "body", [("a", "none"), ("==b", "none"), ("c", "none")])],
    ),
    (
        "fence_without_lang",
        "```\nplain\n```",
        [("pause", "block_ahead"), ("block", "code", "plain", None, None, None)],
    ),
    (
        "unterminated_fence_runs_to_eof",
        "```py\nx=1",
        [("pause", "block_ahead"), ("block", "code", "x=1", "py", None, None)],
    ),
    (
        "unterminated_note_runs_to_eof",
        ":::note\nhi",
        [("pause", "block_ahead"), ("block", "note", "hi", None, None, None)],
    ),
    (
        "multiline_quote",
        "> line one\n> line two",
        [("pause", "block_ahead"), ("block", "quote", "line one\nline two", None, None, None)],
    ),
    (
        "decimal_is_not_a_terminator",
        "Pi is 3.14 here.",
        [
            (
                "prose",
                "body",
                [("Pi", "none"), ("is", "none"), ("3.14", "none"), ("here", "none")],
            )
        ],
    ),
    (
        "trailing_blank_lines_drop",
        "hi\n\n",
        [("prose", "body", [("hi", "none")])],
    ),
    ("empty_input", "", []),
    ("lone_terminator_yields_nothing", ".", []),
]


@pytest.mark.parametrize(
    ("text", "expected"), [(v[1], v[2]) for v in _VECTORS], ids=[v[0] for v in _VECTORS]
)
def test_parse_matches_golden_shape(text: str, expected: list[tuple[object, ...]]) -> None:
    """parse_glyde_markdown produces the pinned timeline shape for each vector."""
    assert _shape(parse_glyde_markdown(text)) == expected
