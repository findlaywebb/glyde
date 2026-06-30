# Svelte MCP server — for Glyde's `.mcp.json`

Research date: 2026-06-30. Source codebase mined: `/Users/findlaywebb/assay`.

## TL;DR — the headline finding

**`assay` does NOT configure a Svelte MCP server.** There is nothing to "mirror" — the
premise that assay wires a Svelte docs/autofixer MCP into its agent loop is false. What
follows is therefore the **canonical official Svelte MCP server**, verified against
`svelte.dev/docs/ai/*` today (not training memory), packaged as the exact entry to drop
into Glyde's (currently non-existent) `.mcp.json`.

## Evidence that assay has no Svelte MCP server

Read-only sweep of `/Users/findlaywebb/assay`:

- No `.mcp.json` anywhere (repo root, `frontend/`, or nested) — `grep -rl "mcpServers"`
  over the whole tree (excluding `node_modules`/`.git`/`.svelte-kit`) returns nothing.
- No `.claude/settings.json` / `settings.local.json`. `assay/.claude/` contains only
  `skills/`, `worktrees/`, and a `scheduled_tasks.lock`.
- Global `~/.claude.json` records the assay project (`/Users/findlaywebb/assay`) with
  `mcpServers: []`. The only MCP server configured at all (top level) is **`context7`**.
- `frontend/package.json` has **no** `@sveltejs/mcp` (or any MCP) dependency.
- The only "MCP" strings in assay docs (`Platform_Vision.md`, `Agent_Development_Doctrine.md`,
  `Frontend_Architecture_Decision.md`) describe **Assay's own future product** exposing an
  MCP surface in v2+ — i.e. Assay-as-a-server, unrelated to a Svelte dev-time docs server.

### What assay uses *instead* (the nearest equivalent)

For Svelte 5 correctness, assay relies on **(a)** the `context7` MCP server for live library
docs, and **(b)** a dense hand-written rubric: `frontend/CLAUDE.md` (runes-only patterns,
typed-seam rules, a11y, tokens) plus a `review-frontend` skill (fresh-context reviewer
against `reference/rubric.md`). That is a *prose* substitute for what the Svelte MCP server's
`svelte-autofixer` tool now does mechanically — which is exactly the gap adopting the MCP
server closes for Glyde.

## The canonical Svelte MCP server (official)

- **Package:** `@sveltejs/mcp` (npm; official `sveltejs` org). Run via `npx -y` — the
  official docs pin **no** version (`npx -y @sveltejs/mcp` always pulls latest). Node-based;
  Glyde's frontend already runs on Node, so the stdio transport is available.
- **Hosted/remote alternative:** `https://mcp.svelte.dev/mcp` (HTTP transport) — no local
  process, but requires network egress to svelte.dev on every dev session.
- **Source of truth:** `svelte.dev/docs/ai/local-setup`, `/docs/ai/remote-setup`,
  `/docs/ai/tools`, and `github.com/sveltejs/ai-tools` `CLAUDE.md`.

### Tools it exposes (4)

| Tool (as docs name it) | Claude Code namespaced form | What it does |
|---|---|---|
| `list-sections` | `mcp__svelte__list_sections` | Returns every svelte.dev/SvelteKit doc section (title + path). **Call this first.** |
| `get-documentation` | `mcp__svelte__get_documentation` | Fetches full current doc content for one or more sections returned by `list-sections`. |
| `svelte-autofixer` | `mcp__svelte__svelte_autofixer` | Static-analyses Svelte code and returns issues + suggestions; designed to be looped until clean. |
| `playground-link` | `mcp__svelte__playground_link` | Generates an ephemeral Svelte Playground link for generated code (no files written). |

(The official `tools` page uses hyphens; the `ai-tools` `CLAUDE.md` prose writes
`get_documentation`. In Claude Code they surface under the `mcp__svelte__*` prefix.)

## The exact entry to install into Glyde

Glyde has **no `.mcp.json` yet**, so this is a *create*, not a merge. Recommended:
**stdio/local** (the official default; what `claude mcp add` writes). Create
`/Users/findlaywebb/glyde/.mcp.json` with exactly:

```json
{
  "mcpServers": {
    "svelte": {
      "command": "npx",
      "args": ["-y", "@sveltejs/mcp"]
    }
  }
}
```

No env vars are required. That object is also the precise fragment to **merge** under
`mcpServers` if a `.mcp.json` already exists by the time this is applied.

Equivalent one-liner (writes the same project-scoped entry):

```bash
claude mcp add -t stdio -s project svelte -- npx -y @sveltejs/mcp
```

### Remote variant (only if you prefer no local node process)

```json
{
  "mcpServers": {
    "svelte": {
      "url": "https://mcp.svelte.dev/mcp"
    }
  }
}
```

`claude mcp add -t http -s project svelte https://mcp.svelte.dev/mcp`. Prefer the stdio
entry above for Glyde: it keeps the dev loop local-first (consistent with the product's
own ethos) and has no per-call network dependency on svelte.dev beyond the doc fetches the
tools themselves make.

Note: `context7` is already configured globally in `~/.claude.json`, so it does **not** need
duplicating into Glyde's project `.mcp.json` — `svelte` is the only addition.

## How to use it

The official workflow (from svelte.dev `/docs/ai/tools` and the `sveltejs/ai-tools`
`CLAUDE.md`) — fold this into Glyde's `frontend/CLAUDE.md` so agents actually invoke it:

1. **Discovery first.** On any Svelte/SvelteKit question or before generating component
   code, call **`list-sections`** first to see the available doc sections.
2. **Targeted fetch.** Analyse the returned list and call **`get-documentation`** for *all*
   sections relevant to the task (it accepts multiple). This pulls the *current* runes /
   SvelteKit docs — the authority over training-data memory for Svelte 5 idioms.
3. **Autofix loop.** After generating or editing any Svelte code, run **`svelte-autofixer`**
   and iterate (agentic loop) until it reports no issues/suggestions — *before* showing the
   code to the user or committing. This is the mechanical backstop for the runes-only,
   no-`$:`, no-`export let`, derived-not-effect rules Glyde's rubric states in prose.
4. **Playground for demos.** Use **`playground-link`** to hand over a runnable example
   without writing throwaway files into the repo.

Sequence: **discover → fetch relevant docs → generate → autofix-until-clean**. The autofixer
step is the highest-value one for Glyde — it turns "the reviewer hopes the agent remembered
Svelte 5 idioms" into a checkable gate.

## Why adopt it in Glyde (vs assay's prose-only approach)

- assay holds the Svelte-5 bar with a hand-written `frontend/CLAUDE.md` + a `review-frontend`
  skill *after* the fact. `svelte-autofixer` moves that check **into the generation loop**,
  catching legacy-syntax/anti-pattern regressions before review.
- `get-documentation` returns **current** Svelte/SvelteKit docs on demand — the same
  defence against stale training data that Findlay's `external-integration` rule mandates,
  but Svelte-specific and richer than context7 for framework idioms.
- Dev-time only: the MCP server is an agent tool, not an app dependency, so it doesn't touch
  Glyde's local-first runtime or its boundary/budget gates.

---
*Verified sources (2026-06-30): [Local setup](https://svelte.dev/docs/ai/local-setup),
[Remote setup](https://svelte.dev/docs/ai/remote-setup), [Tools](https://svelte.dev/docs/ai/tools),
[sveltejs/ai-tools CLAUDE.md](https://github.com/sveltejs/ai-tools/blob/main/CLAUDE.md).*
