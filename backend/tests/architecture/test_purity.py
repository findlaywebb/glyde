"""Purity gates — no clock reads, minted ids, or non-determinism at runtime.

The core layer is the pure domain kernel and the adapters layer is deterministic
by contract (the store ports are clock-free/id-free/synchronous): all timestamps
and generated ids arrive as arguments from the api layer; neither package mints
them. Randomness seeded via ``random.Random`` is permitted (algorithm bootstrap),
but unguarded calls on the module-level ``random`` object are not.

Matching scope
--------------
Clock calls caught:
  - ``datetime.now(...)`` / ``datetime.utcnow()`` / ``datetime.today()``.
  - ``date.today()``.
  - ``datetime.datetime.now(...)`` chained attribute forms.
  - ``time.time()`` / ``time.monotonic()`` / ``time.perf_counter()`` etc.
Non-determinism calls caught:
  - Any ``random.<attr>(...)`` call where ``attr`` is NOT ``Random``.
Id minting (both pure roots):
  - Any import of ``uuid`` — ids arrive as arguments, never minted. The api
    layer is the one place ids are born.
Adapters-only bans (stricter than core's):
  - Any ``async def`` — adapters are synchronous by design.
Scanning:
  Only production code under the parametrised roots is scanned (not tests).
"""

import ast

import pytest

from ._ast_checks import ADAPTERS_SRC, CORE_SRC, _violations

_CLOCK_ATTRS = {"now", "utcnow", "today"}
_TIME_ATTRS = {"time", "monotonic", "time_ns", "monotonic_ns", "perf_counter"}

# Reusable parametrize decorator: a test stamped with this runs once per pure
# package root, with readable ids (test_x[core], test_x[adapters]). Adding a
# package to the purity regime is one entry here.
_PURE_ROOTS = pytest.mark.parametrize("root", [CORE_SRC, ADAPTERS_SRC], ids=["core", "adapters"])


def _is_clock_name(node: ast.expr) -> bool:
    """Return True if node is a Name or chained Attribute ending in datetime/date."""
    match node:
        case ast.Name(id="datetime" | "date"):
            return True
        case ast.Attribute(value=inner, attr="datetime" | "date"):
            return _is_clock_name(inner)
        case _:
            return False


@_PURE_ROOTS
def test_reads_no_clock(root) -> None:
    """Pure packages never read the clock — timestamps arrive as arguments."""

    def is_clock_call(node: ast.AST) -> bool:
        match node:
            case ast.Call(func=ast.Attribute(value=inner, attr=attr)) if (
                attr in _CLOCK_ATTRS and _is_clock_name(inner)
            ):
                return True
            case _:
                return False

    assert not _violations(root, is_clock_call), (
        f"{root.parent.name} reads the clock — timestamps arrive as arguments"
    )


@_PURE_ROOTS
def test_reads_no_time_module(root) -> None:
    """Pure packages never call time.time/monotonic/perf_counter — timestamps arrive as arguments."""

    def is_time_call(node: ast.AST) -> bool:
        match node:
            case ast.Call(func=ast.Attribute(value=ast.Name(id="time"), attr=attr)) if (
                attr in _TIME_ATTRS
            ):
                return True
            case _:
                return False

    assert not _violations(root, is_time_call), (
        f"{root.parent.name} calls time module — elapsed / wall time must not originate here"
    )


@_PURE_ROOTS
def test_has_no_module_level_randomness(root) -> None:
    """Pure packages never call module-level random functions (seeded random.Random instances allowed)."""

    def is_random_call(node: ast.AST) -> bool:
        match node:
            case ast.Call(func=ast.Attribute(value=ast.Name(id="random"), attr=attr)) if (
                attr != "Random"
            ):
                return True
            case _:
                return False

    assert not _violations(root, is_random_call), (
        f"{root.parent.name} uses module-level randomness — use random.Random(seed) "
        "for seeded instances"
    )


@_PURE_ROOTS
def test_mints_no_ids(root) -> None:
    """Pure packages never import uuid — ids are minted by the api layer and arrive as arguments."""

    def is_uuid_import(node: ast.AST) -> bool:
        match node:
            case ast.Import(names=aliases):
                return any(a.name == "uuid" or a.name.startswith("uuid.") for a in aliases)
            case ast.ImportFrom(module=module):
                return module == "uuid" or (module or "").startswith("uuid.")
            case _:
                return False

    assert not _violations(root, is_uuid_import), (
        f"{root.parent.name} imports uuid — ids are minted by the api layer and arrive as arguments"
    )


def test_adapters_are_synchronous() -> None:
    """The adapters layer defines no coroutines — stores are synchronous by design."""

    def is_async_def(node: ast.AST) -> bool:
        return isinstance(node, ast.AsyncFunctionDef)

    assert not _violations(ADAPTERS_SRC, is_async_def), (
        "async def in the adapters layer — the store port is synchronous; FastAPI runs it "
        "in the threadpool"
    )
