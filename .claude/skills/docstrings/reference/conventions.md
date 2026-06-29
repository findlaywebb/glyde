# Docstring Conventions (consolidated)

The single source of truth for *how a good docstring looks*. Distilled from PEP
257, PEP 8, the Google Python Style Guide, and Memento's team rules (agreed
2025-05-20). Where they diverge, the resolution is stated inline.

These conventions describe the **Google style** — the default for FMP repos and
Findlay's own code. For projects on a different style, see *Convention
detection* in `SKILL.md`; the universal mechanics below still apply, only the
section syntax changes.

---

## The non-negotiable mechanics (PEP 257)

- A docstring is the **first statement** in a module, function, class, or method.
- **Always triple-double-quotes** (`"""`), even for a one-liner. Use
  `r"""..."""` only if the body contains backslashes.
- No blank line *before* the docstring. For a function, no blank line after it
  either; for a **class**, leave one blank line after the docstring.
- Multi-line: closing `"""` goes **on its own line**. One-line: closing `"""` on
  the same line.
- Never repeat the function signature in the body — type hints and introspection
  already carry it.

## The summary line

- **≤80 characters on the physical line**, ending in a period (or `?`/`!`).
  Google Python Style Guide §3.2 — a single 80-char limit applied to *every* line,
  docstrings included. (Google declined PEP 8's tighter 72-char prose exception in
  favour of one uniform, lintable rule; we follow Google for both own code and
  review.) Measure the whole physical line — indentation and the `"""` count, not
  just the prose. Not lint-enforced: `E501` is one file-wide max and is often
  disabled, and no `D` rule checks summary length.
- **Imperative mood by default** — "Fetch rows from Bigtable.", not "Fetches…"
  or "This function fetches…". (Findlay/FMP default.)
  - *Consistency floor*: within any one file, mood must be uniform. When
    reviewing a third-party codebase that is consistently descriptive, do not
    flag mood — only flag mixed mood.
- **Must not restate the function name.** `get_user` → not "Get the user." but
  "Resolve a user from the session token, falling back to anonymous." Complement
  the name; add the context the name can't carry.
- A trivial/obvious function gets a **summary line only** — do not pad it with
  empty `Args:`/`Returns:` sections. Force boilerplate only when it earns its
  place (public API, non-obvious logic, non-trivial size — Google's test).

## Sections (Google style)

Order: summary → blank line → (extended description) → `Args:` → `Returns:` (or
`Yields:`) → `Raises:`. **Omit any section that doesn't apply** — never an empty
`Raises:`.

### Args

- One entry per parameter, by exact name, then `: description`.
- **No type *annotations*.** Memento rule: type hints carry the type; the generic
  Google `param (type):` form is *not* used here. Write `workspace_id: The target
  workspace.`, not `workspace_id (str): The target workspace.` This bans the
  *redundant annotation*, not the *word* — naming a type in prose is fine when it
  carries meaning (e.g. `count: Number of rows, capped at 1000`).
- Document `*args`/`**kwargs` if their use is non-obvious. Don't document `self`
  or `cls`.
- Skip the obvious-and-fully-typed parameter only when the summary already makes
  it clear; otherwise describe it.

### Returns / Yields

- Describe the **semantics the type hint can't express** — ordering, units,
  None-conditions, ownership. Skip if the function returns `None`.
- Don't *prefix* the description with the return type (`int:`, `ParsedFoo:`) —
  that duplicates the hint. But the type *word* in prose is fine when it's the
  point: `log_level_int` returning "Integer logging level (e.g. `logging.INFO` =
  20)" is meaningful (the integer-ness disambiguates it from the string form),
  not a violation. Flag the redundant annotation, not the informative noun.
- Generators use `Yields:`, not `Returns:`.

### Raises

- List exceptions **relevant to the caller's contract**, each with the condition
  that triggers it. Don't enumerate every transitively-possible exception — only
  the ones a caller should handle.

## Modules, classes, packages

- **Module**: top-of-file docstring summarising the module's purpose and (if
  non-trivial) its exported surface.
- **Class**: one-line summary of *what an instance represents*, then an
  `Attributes:` section for public attributes (same no-types format as `Args`).
  Constructor parameters are documented in `__init__`, not the class docstring.
- **Package**: the `__init__.py` docstring lists the modules/subpackages it
  exports.

## Public vs non-public

- PEP 8: public modules/functions/classes/methods **must** have docstrings;
  non-public ones may use a post-`def` comment instead.
- **Project config overrides this.** If ruff's `D` rules apply to all of `src/**`
  (as in `discoveries`), then *every* function needs a docstring regardless of
  visibility — respect the stricter local bar. See `SKILL.md`.

## Pydantic BaseModel docstrings
- For `BaseModel` subclasses, the class docstring describes the model as a whole
  (what it represents, any non-obvious invariants, etc.). Do not repeat defining
  each field in the class docstring; these are already defined in the field 
  declarations and are visible to introspection. Update the field definitions
  with `description=...` to document individual fields, and use the class docstring for model-level notes.

---

## Good vs bad (worked examples)

**Bad — restates the name, types in Args, empty section, descriptive mood:**

```python
def get_records(workspace_id: str, limit: int = 100) -> list[Record]:
    """Gets records.

    Args:
        workspace_id (str): The workspace id.
        limit (int): The limit.

    Returns:
        list[Record]: The records.

    Raises:
    """
    ...
```

**Good — complements the name, no types, semantic Returns, section omitted:**

```python
def get_records(workspace_id: str, limit: int = 100) -> list[Record]:
    """Fetch a workspace's records, newest first.

    Args:
        workspace_id: Workspace whose records to load.
        limit: Maximum number of records to return.

    Returns:
        Records ordered by creation time, newest first; empty if none exist.
    """
    ...
```

**Good — trivial function, summary only:**

```python
def is_empty(self) -> bool:
    """Return whether the queue holds no items."""
    return not self._items
```

**Good — class with Attributes, __init__ documents params:**

```python
class DiscoveryRun:
    """A single execution of the discovery pipeline for one brand.

    Attributes:
        run_id: Stable identifier assigned at creation.
        brand: Brand the run was triggered for.
        status: Lifecycle state; see RunStatus.
    """

    def __init__(self, brand: str) -> None:
        """Start a pending run for a brand.

        Args:
            brand: Brand to discover against.
        """
        ...
```
