# Assay adoption brief

The single entry point for Glyde's fan-out engineers. Three research files mined assay (same
shape as Glyde: FastAPI + SvelteKit, hexagonal `api → adapters → core`, uv workspace,
local-first, served to a phone over the home LAN). This brief is the skimmable index over
them: the concrete patterns to adopt across four workstreams, each a short directive pointing
back to the detailed file. Read the directive here, then open the referenced section before
you implement.

Much of this is **already scaffolded** into Glyde (see the bottom section) — reproduce the
mechanism exactly where it already exists, build net-new only where assay has a genuine gap
(the RSVP clock, HTTPS-over-LAN, Digest-IR caching). Each source file ends with its own fuller
"Adopt in Glyde" section if you need more than the directive.

Sources:

- `docs/research/assay-frontend.md` — reader, runes, typed seam, styling, a11y, tests.
- `docs/research/assay-mobile-lan.md` — serving, bind, QR, CSRF, HTTPS, PWA, gestures.
- `docs/research/svelte-mcp.md` — the official Svelte MCP server + the agent workflow.

---

## 1. SvelteKit reader + Svelte 5 runes

**Model the RSVP/sweep reader as a `.svelte.ts` state-machine factory; keep all logic out of
components and every `$effect` at the DOM boundary.**

- Factory returns `$state`-backed **getters + imperative methods** (assay's `createLabelLoop`).
  Never return a plain object — destructuring snapshots the value and breaks reactivity. DI the
  transport + a `newId`/clock source so the machine is DOM-free and unit-testable.
- A `playing`/`busy` **exclusive flag** (no overlapping advances); **optimistic → `await
  tick()` → persist**; a `halt = freeze` terminal state on a failed Digest fetch; a pure
  `keyToIntent(key)` switch (`Space`→toggle, `←/→`→word, `↑/↓`→speed).
- **`$derived` for anything that is a pure function of state — never `$effect`.** Reserve
  `$effect` for genuine side effects (listeners, focus, SW registration, the gesture bind),
  always returning teardown. The factory itself holds **zero `$effect`**.
- `$props()` with a typed `interface Props`, defaults destructured, `...rest` spread; snippets
  (`{#snippet}`/`{@render}`) not slots; props-down / callbacks-up, no `createEventDispatcher`.
- **Thin route → local orchestration component** (`reader/[doc_id]/+page.svelte` →
  `ReaderLoop.svelte`); `{#key segment_id}` remounts the word surface cleanly per advance.
- **Build the RSVP clock yourself** — assay has no timing loop at all. Use a
  `requestAnimationFrame` accumulator against `performance.now`, `cancelAnimationFrame` on
  pause/teardown. Keep cadence math (WPM→ms/word, ORP offset, pause-at-punctuation) in a
  **pure `.ts`**; keep only the rAF wiring in the `.svelte.ts` shell.
- Animate with **compositor-only `transform`/`opacity` + CSS transitions** for the moving
  marker / fade trail (never `left`/`width`/`top`); **gate ALL motion and the word-flash
  cadence on `prefers-reduced-motion`** read once at bind time — non-negotiable for a flashing
  reader (accessibility + seizure concern).
- Reuse `bindSwipe` for tap-to-pause / swipe-to-seek: Pointer Events, **axis-lock past 8px**
  (horizontal = seek, vertical = yield to native scroll), feature-detected `setPointerCapture`,
  an "ignore zone" on the reading body, **distance-OR-velocity** commit rule. Pure classifier
  in `.ts`, DOM binding in `.svelte.ts`.

See: `assay-frontend.md` §§3–7 (runes, factory, timing, gesture, components); §11 (a11y:
`aria-live` announcer, focus-scoped keydispatch with `preventDefault`, roving focus on advance,
a visible control for every gesture).

---

## 2. The typed seam

**Reproduce assay's typed API↔frontend seam verbatim (already scaffolded) — generated types, a
stateless module client, reads inside `load`.**

- `openapi-typescript` (pinned 7.13.0) generates the **committed** `src/lib/api/schema.d.ts`
  from `docs/schemas/openapi.json`. Keep the `--check` **drift gate** AND the backend
  openapi-matches-live gate — **neither alone proves freshness**.
- `openapi-fetch` (pinned 0.17.0) module client at `baseUrl:'/api'`. Consume
  `components['schemas'][...]`, never hand-write the wire types.
- In `load`: **per-request `fetch`, absolute `${url.origin}/api` base** (SSR has no origin for a
  relative URL), `Promise.all` independent reads, branch **`{ data, error }` — a 200 is not
  success**, `error(502, …)` on any failure.
- Client mutations go through an **injected gateway interface**, not a module singleton in the
  component — keeps the state machine transport-agnostic and trivially mockable.
- `ui/` components take **primitive props, never the wire/Digest type** (the boundary forbids
  `ui→api`); the route flattens `data` before passing down, so presentational components stay
  blind to the wire shape (good — the Digest IR will churn).

See: `assay-frontend.md` §2 (the seam, exactly). The serving half (the `/api` proxy,
`filterSerializedResponseHeaders`) lives in `assay-mobile-lan.md` §1.

---

## 3. Mobile-LAN serving (bind, QR, token, PWA)

**One node front door on the LAN, FastAPI on loopback; lift the launch recipe almost verbatim;
do HTTPS-over-LAN now.**

- **Same-origin model.** The built `adapter-node` server is the only LAN-facing process and
  reverse-proxies `/api/*` to FastAPI on `127.0.0.1` → CORS is structurally absent.
  `hooks.server.ts` returns before `resolve()`, strips `/api`, forwards;
  `filterSerializedResponseHeaders` must allow `content-type`+`content-length` or hydrating
  reads throw. FastAPI uses `root_path="/api"` + explicit `servers=[{"url":"/api"}]`. **Bind:**
  only the node server gets `HOST=0.0.0.0`; FastAPI stays loopback. Env prefix → `GLYDE_`,
  proxy target → `GLYDE_API_ORIGIN`.
- **Launch recipe** (`scripts/lan.sh` + `scripts/lan.py`, copy almost verbatim): the
  UDP-connect LAN-IP trick, `qrcode` ASCII **QR** to the terminal, compute `ORIGIN` **once**
  (the "triad" — adapter-node `ORIGIN` env = QR payload = CSRF compare value; a mismatch 403s
  every mutation silently), and the `wait_for` liveness+readiness poll **before** printing the
  QR. `pydantic-settings` reads env in exactly one place (host/port/db injected).
- **Token / auth: there is none** — single-user, single-LAN. Instead a tiny **CSRF origin
  assertion** at the node door: reject only when non-GET AND a *present* `Origin` fails strict
  same-origin (an absent `Origin` is allowed — SSR re-entry / trusted local agent). Keep it for
  any Glyde mutation (bookmarks, progress, settings); it costs nothing if read-only. Caveat: the
  app **must be reached via the printed LAN URL the QR encodes** — `localhost` against a LAN
  `ORIGIN` 403s on mutations.
- **HTTPS-over-LAN is on Glyde's critical path** (this is where Glyde diverges from assay): an
  installable, offline reader needs a service worker + `display:standalone`, which need a
  **secure context** that a plain-HTTP LAN origin is not. Build the `node:https` + `mkcert` path
  assay only documented (`mkcert <lan-ip-or-glyde.local>`, trust the root CA on the phone once,
  front adapter-node with `node:https`).
- **PWA + iOS gotchas, day one:** manifest (`standalone`, portrait, dark `theme_color`,
  192/512+maskable icons); shell-cache `sw.js` with **`/api/*` passthrough as the first
  statement** (a cache miss must never shadow a live read); the dismissible iOS "Add to Home
  Screen" `InstallHint` (no `beforeinstallprompt` on iOS); viewport
  `interactive-widget=resizes-content`; any text input **≥16px** (stops iOS focus-zoom — central
  for a reading app); `overscroll-behavior-y:contain`; `overflow-x-clip` on `<main>`; **≥44px**
  (`min-h-11 min-w-11`) touch targets.
- **`crypto.randomUUID` insecure-context fallback** — it is `undefined` over plain-HTTP LAN and
  silently kills every client-minted-id mutation; fall back to `getRandomValues` and assemble
  the v4 UUID by hand. Keep it even after HTTPS lands — free insurance, and the exact bug a
  physical iPhone found that every `localhost` gate missed.
- **Testing:** a Playwright `webServer` array booting the real built-node-over-FastAPI topology
  with `ORIGIN` pinned, plus an owner-run physical-iPhone `device-checklist.md` — `localhost`
  e2e is a secure context and structurally cannot catch the LAN-over-HTTP bug class.

See: `assay-mobile-lan.md` (all of it — §1 serving, §3 launch+QR, §4 CSRF, §5
HTTPS/secure-context, §6 PWA, §7 viewport/touch, §9 testing). PWA shell detail also in
`assay-frontend.md` §10.

---

## 4. The Svelte MCP workflow

**Add the official Svelte MCP server to a new `.mcp.json` and fold the
discover→fetch→generate→autofix loop into `frontend/CLAUDE.md`.** (Net-new: assay does **not**
configure this — it is an upgrade over assay's prose-only rubric, not a mirror.)

- Glyde has **no `.mcp.json`** — create `/Users/findlaywebb/glyde/.mcp.json` with the stdio
  entry (`npx -y @sveltejs/mcp`; no env vars, no version pin → always latest). `context7` is
  already configured globally, so do **not** duplicate it; `svelte` is the only addition. Exact
  JSON is in this brief's StructuredOutput and in `svelte-mcp.md`.
- **Workflow (put it in `frontend/CLAUDE.md` so agents actually invoke it):** `list-sections`
  first → `get-documentation` for all relevant sections (current Svelte 5 / SvelteKit docs, the
  authority over training memory) → generate → **`svelte-autofixer` looped until clean before
  showing or committing**. `playground-link` for a runnable demo without throwaway files.
- The **autofixer is the highest-value step**: it turns "hope the agent remembered runes idioms
  (no `$:`, no `export let`, derived-not-effect)" into a mechanical gate inside the generation
  loop, before review.

See: `svelte-mcp.md` (install entry, tool table, 4-step workflow, remote variant).

---

## Glyde-specific divergences (do NOT blind-copy assay)

- **HTTPS-over-LAN now, not deferred.** Assay skipped it (HTTP was fine for labelling); Glyde's
  installable/offline reader requires a secure context. `node:https` + `mkcert`.
- **Build the RSVP clock.** Assay has no `requestAnimationFrame`/timer loop — it gives the
  gesture/transition toolkit, not a word-flash cadence. That scheduler is net-new.
- **Extend the service worker to cache the Digest IR** for offline reading (versioned key,
  stale-while-revalidate) — a deliberate read-caching layer beyond assay's shell-only posture
  (assay needed shell-only for a blind-labelling correctness invariant Glyde does not have).
- **Add an in-app theme/contrast/font control** for the dyslexia audience — assay has none
  (Storybook toolbar only). The `@theme inline` oklch token cascade is the right substrate.

---

## Already scaffolded into Glyde (keep / reproduce, do not rebuild)

The typed seam, the five-element boundary config (`frontend/eslint.config.js`), dark-mode-first
`@theme inline` oklch tokens (`app.css` — keep `inline`; its omission silently breaks dark
mode), `ui/Button.svelte`, the `hooks.server.ts` front door, and the Vitest node-`unit` /
jsdom-`component` split. eslint-boundaries is the authoritative `$lib`-resolving edge guard;
dependency-cruiser is cycle + relative-import backstop only (it does not resolve `$lib`).

---

## Version pins (known-good as of 2026-06; verify before bumping per external-integration)

Python 3.13 · Node ≥22.19 · svelte ^5.56.1 · `@sveltejs/kit` ^2.63.0 · `adapter-node` ^5.5.4 ·
vite ^8.0.16 · tailwindcss ^4.3.1 · **openapi-fetch 0.17.0 / openapi-typescript 7.13.0 (both
pinned)** · fastapi ≥0.136 · uvicorn[standard] ≥0.48 · pydantic-settings ≥2.14 · qrcode ≥8.2.
