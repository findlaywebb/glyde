# Docstring Review Rubric

The gradeable checklist for **review** and **refine** modes. Apply it against the
*actual code*, not the docstring text alone — the single highest-value check is
whether the docstring tells the truth about what the code does. Read
`conventions.md` for the full style definition; this file is the scoring grid.

## What ruff already enforces — do NOT re-flag

If the project runs ruff with the `D` rules (check `pyproject.toml`), these are
caught in CI. Reporting them is noise. Skip:

- Missing docstring on a covered object (`D1xx`).
- Summary not ending in a period (`D400`), blank-line placement (`D203`/`D205`),
  one-line-summary-fits (`D200`), closing-quote placement (`D209`/`D400`).
- Imperative-mood violations **where `D401` is active** (it checks the first
  word). If `D401` is in the ignore list, mood is back on you.
- Missing Args coverage where `D417` is active.

Confirm by reading the `select`/`ignore`/`per-file-ignores` and
`[tool.ruff.lint.pydocstyle]` blocks. **The rubric's value is everything ruff
can't see**: accuracy, completeness-of-meaning, filler, and the house rules ruff
isn't configured to check (e.g. summary length when `E501` is ignored).

## Severities

| Severity | Meaning |
|----------|---------|
| **Inaccurate** | Docstring contradicts the code: wrong behaviour, wrong/renamed arg, documents a `Raises`/`Returns` the code doesn't produce, or omits one it does. The worst failure — a confident lie is worse than silence. |
| **Incomplete** | Public/interface-relevant info missing: undocumented parameter that needs it, missing `Returns` semantics the type can't convey, an exception callers must handle left out. |
| **Filler** | Adds nothing over the signature — restates the name, "Gets the X.", or pads a trivial function with empty sections. |
| **Style** | Convention break ruff isn't catching: redundant type *annotations* in `Args`/`Returns` (`param (str):`, a `int:`/`ParsedFoo:` prefix — **not** a type word used meaningfully in prose, e.g. "Integer logging level …"), summary >80 chars on the physical line (Google §3.2; not lint-enforced — `E501` is a single file-wide max, often disabled, and no `D` rule checks summary length), mixed mood within a file, restates the signature, empty section present. |
| **Excellence** | A docstring that genuinely earns a callout — captures a non-obvious invariant, a sharp edge-case note, units/ordering a reader would otherwise miss. Use sparingly. |

## The checks (apply per docstring)

1. **Accuracy** — does the summary match what the function actually does? Do the
   `Args` names match the signature? Does every documented `Raises` actually get
   raised, and is every raised-and-caller-relevant exception documented? Does
   `Returns` match the real return (incl. None-conditions)?
2. **Completeness** — for non-trivial/public objects: is every meaningful param
   covered, return semantics stated, and caller-relevant exceptions listed?
3. **Value** — would deleting this docstring lose information? If it only
   restates the name/signature, it's Filler.
4. **Summary quality** — imperative (per consistency floor), ≤80 chars on the
   physical line (Google §3.2), doesn't restate the name, ends in a period.
5. **Section hygiene** — no redundant type *annotations* in `Args`/`Returns` (a
   type word that carries meaning in prose is fine); no empty sections; `Yields`
   for generators; class has `Attributes` and `__init__` documents params.
6. **Coverage** — every object the project's config requires a docstring for has
   one (respect `per-file-ignores`; tests/scripts are often exempt).

## Finding shape (for structured output in fan-out review)

Each finding is one object:

```json
{
  "file": "src/discoveries/services/discovery_service.py",
  "line": 142,
  "object": "DiscoveryService.create_run",
  "severity": "Inaccurate",
  "scope": "in-diff",
  "issue": "Docstring says 'raises ValueError on missing brand' but the code raises BrandNotFoundError.",
  "suggestion": "Update Raises to BrandNotFoundError, or document both."
}
```

`severity` ∈ `Inaccurate | Incomplete | Filler | Style | Excellence`. Keep
`issue` to one or two sentences; put the fix in `suggestion`. Prefer the
file:line of the `def`/`class`, so the reader lands on the object.

`scope` ∈ `in-diff | pre-existing` (PR/commit reviews only — see *Scope: review
the diff, not the file* in `SKILL.md`). `in-diff` = the docstring was newly
written/substantively reworded, **or** the code it documents changed
substantially (signature/behaviour/raises/return) even if the docstring text was
untouched. `pre-existing` = the defect predates the change — docstrings the diff
didn't touch whose code also didn't substantively change, **including** lines the
diff only mechanically brushed (a `"""` opener collapsed, a period added, a blank
line removed). Determine it from `git show <sha> -- <file>`: docstring text on
`+` lines → `in-diff`; unchanged docstring but the surrounding `def`/body has `+`
logic lines → `in-diff` (stale-risk); text only on context lines with untouched
code → `pre-existing`. For a whole-file review with no diff, omit `scope`.
