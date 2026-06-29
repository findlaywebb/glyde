# Glyde frontend

SvelteKit (Svelte 5 runes), TypeScript strict, Tailwind v4, shadcn-svelte. The stack is
decided; author components to a slick, modern, accessible bar by default — that is the spec,
not a nice-to-have.

## Confirmed stack

- **SvelteKit**, TypeScript strict (`noUncheckedIndexedAccess`), Node + Vite + official
  `adapter-node` for build/runtime.
- **Typed API seam**: `openapi-typescript` generates `src/lib/api/schema.d.ts` from FastAPI's
  OpenAPI document; all calls go through `openapi-fetch`. Commit the generated file;
  regenerate on schema change (`npm run gen:api` after the backend's `export-openapi`). No
  hand-written fetch types.
- **Serving model:** `hooks.server.ts` `handle()` is the single front door — it proxies
  `/api/*` to FastAPI (`GLYDE_API_ORIGIN`, server-only env, default
  `http://127.0.0.1:8000`), stripping `/api`. The browser client base is `/api` (relative);
  SSR `load`s use `${url.origin}/api` (absolute same-origin) with `event.fetch`, which
  re-enters `handle()` in-process — no cross-origin read, no CORS. Vite dev proxies `/api`
  the same way.
- shadcn-svelte + Tailwind v4 `@theme` tokens; eslint-plugin-svelte + Prettier.

## Patterns (Svelte 5 — the non-inferable taste)

- **Runes only.** `$state` / `$derived` / `$effect`; no `$:`, `export let`,
  `createEventDispatcher`, `on:`, `<slot>`, or a `writable` store for plain shared state
  (use a `$state` object in a `.svelte.ts` module). Any value that is a pure function of
  other state is a **`$derived`, never an `$effect`** — `$effect` is the escape hatch for
  genuine side effects (DOM, network, third-party libs). Never destructure `$state` (loses
  reactivity). Props flow down, callbacks up; `$bindable` only on genuine co-ownership.
- **Typed seam, used right.** Call the `api/` `openapi-fetch` client **inside `load`, with
  the per-request `fetch`** SvelteKit injects (not a module singleton, not native `fetch`);
  branch `{ data, error }` (a 200 is not success); components render `data` and never fetch.
  `schema.d.ts` is committed; CI runs `openapi-typescript --check`.
- **Tokens, not raw palette.** Components speak in semantic tokens (`bg-card`, not
  `bg-zinc-900`); light/dark via `:root`/`.dark` + **`@theme inline`** (omitting `inline`
  silently breaks dark mode). shadcn-svelte components are _owned source_ in
  `$lib/components/ui/` — review them as our code. A repeated arbitrary `[…]` value is a
  missing token.
- **Dark-mode-first.** The app default is dark: `<html class="dark">` in `app.html` +
  `color-scheme` on the cascade (`:root` light / `.dark` dark).
- **Accessibility is non-negotiable.** Zero compiler `a11y_*` warnings (CI-fatal); semantic
  HTML over div-soup; `:focus-visible` (never blanket `outline:none`).
- Run **both `svelte-check` (markup, a11y, CSS) and `tsc --noEmit`** — `tsc` does not check
  Svelte markup. Never `!` an indexed access to silence `noUncheckedIndexedAccess`.

## Architecture boundaries (the frontend mirror of the backend's import-linter)

`eslint-plugin-boundaries` (authoritative element-edge guard; resolves `$lib`) +
`dependency-cruiser` (cycle detection + relative-import backstop): elements
`{routes, domains, ui, api, utils}`; `routes→{domains,ui,api}`, `domains→{ui,api,utils}`,
`ui→{utils}`; no cycles.

## Gates

- `npm run lint` (prettier + eslint + boundaries), `npm run boundaries` (depcruise, no
  cycles), `npm run check` (svelte-check, zero a11y, CI-fatal) + `npm run typecheck`
  (`tsc --noEmit`), `npm run test` (vitest: node `unit` + jsdom `component` projects),
  `npm run knip` (dead code, warn-level), `npm run check:api-drift` (the typed-seam drift
  gate), `npm run build`.
- Commit hooks: prek workspace — root `.pre-commit-config.yaml` (Python) +
  `frontend/.pre-commit-config.yaml` (nested: `npm run lint` + `check`). The YAML root is
  required for prek to discover the nested config.

## Setup note

On a fresh scaffold `src/lib/api/schema.d.ts` does not exist yet (it is generated and
git-ignored). Run the backend's `export-openapi`, then `npm run gen:api`, before
type-checking or building. Once generated, commit it.
