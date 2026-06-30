# Assay → Glyde: serving to mobile over the LAN

Mined from `/Users/findlaywebb/assay` (read-only). Assay is the same shape as Glyde
(FastAPI + SvelteKit, hexagonal `api → adapters → core`, uv workspace under
`backend/packages/`), and it shipped a working "pick up your phone, scan a QR, label
over the home LAN" loop. That is almost exactly Glyde's "serve the reader over the LAN
to a phone" requirement, so the serving stack is reusable nearly verbatim.

The whole feature lives in Assay's spec `008-mobile-swipe-pwa-lan` plus two ADRs (0014
same-origin serving, 0015 dynamic-host origin assertion). The single most valuable
artifact is `specs/008-mobile-swipe-pwa-lan/integration-notes.md`: it is the running log
of what the *physical iPhone* found that CI could not, and it is where the real gotchas
are written down.

---

## 1. The serving model: one node front door, FastAPI on loopback

The load-bearing decision (ADR 0014): the **built SvelteKit `adapter-node` server is the
single public door on the LAN**. It serves the UI and reverse-proxies `/api/*` to FastAPI.
FastAPI itself binds **loopback only** (`127.0.0.1:8000`) and the phone never touches it
directly. Consequences: the browser is always same-origin, so **CORS is structurally
absent** (not suppressed by headers, just never needed), and only one process faces the
LAN.

```
phone ──http──> node adapter-node server (0.0.0.0:3000)  ──/api/*──> FastAPI (127.0.0.1:8000)
                 │  serves SvelteKit UI                    (loopback, never LAN-facing)
                 └  hooks.server.ts is the proxy + CSRF door
```

`frontend/svelte.config.js` — adapter-node is the front door:

```js
import adapter from '@sveltejs/adapter-node';
const config = {
	kit: { adapter: adapter() },
	compilerOptions: { runes: true }
};
```

`frontend/src/hooks.server.ts` — the proxy. `/api/*` requests return *before*
`resolve()`, strip the `/api` prefix, and forward to a server-only origin:

```ts
const API_ORIGIN = env.ASSAY_API_ORIGIN ?? 'http://127.0.0.1:8000';

export const handle: Handle = ({ event, resolve }) => {
	const { pathname, search } = event.url;
	if (pathname === '/api' || pathname.startsWith('/api/')) {
		// ... CSRF guard (see §4) ...
		const upstream = `${API_ORIGIN}${pathname.slice('/api'.length)}${search}`;
		return fetch(new Request(upstream, event.request));
	}
	return resolve(event, {
		// Forward only the two headers openapi-fetch reads off an SSR load fetch,
		// or a hydrating typed-seam read throws (SvelteKit strips replayed headers by default).
		filterSerializedResponseHeaders: (name) =>
			name === 'content-type' || name === 'content-length'
	});
};
```

The browser hits the relative `/api` base; SSR `load`s hit `${url.origin}/api` and
re-enter `handle()` in-process via SvelteKit's `respond()`. Loop-safe because
`ASSAY_API_ORIGIN` is a *different port*, so the upstream `fetch` cannot re-enter the node
server.

FastAPI is mounted under `/api` via `root_path="/api"` + explicit `servers=[{"url":
"/api"}]` in the `FastAPI(...)` constructor (ADR 0014 D2), which keeps internal route
declarations bare (`/sessions/…`, `/actions`) while the committed `openapi.json` advertises
the prefix. The explicit `servers=` is required because `root_path` only injects `servers`
at request time, so an in-process `create_app().openapi()` (the export CLI + drift test)
would otherwise carry none.

**Dev parity:** `frontend/vite.config.ts` proxies `/api` the same way so the browser is
same-origin in dev too (no CORS toggle anywhere):

```ts
const apiOrigin = process.env.ASSAY_API_ORIGIN ?? 'http://127.0.0.1:8000';
export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		proxy: {
			// Anchored regex: matches /api and /api/… but not /apiary.
			'^/api(/|$)': {
				target: apiOrigin,
				changeOrigin: true,
				rewrite: (path) => path.replace(/^\/api/, '')
			}
		}
	}
});
```

---

## 2. Server bind / host / port config

**Backend (FastAPI / uvicorn).** Bind is injected, never read in `core`. `pydantic-settings`
`BaseSettings` with an `ASSAY_` env prefix is the *only* place the environment is read
(`backend/packages/api/src/assay/api/settings.py`):

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ASSAY_", frozen=True)
    db_path: Path = Path("assay.db")
    host: str = "127.0.0.1"   # loopback default — the node proxy is the only client
    port: int = 8000
```

`serve` reads those and boots uvicorn (`backend/packages/api/src/assay/api/cli.py`):

```python
@app.command()
def serve() -> None:
    settings = get_settings()
    uvicorn.run("assay.api.app:create_app", factory=True, host=settings.host, port=settings.port)
```

Note: the default host is `127.0.0.1`, and the launch recipe **keeps it that way** even on
the LAN. The phone reaches FastAPI only through the node `/api` proxy. The LAN bind happens
at the node layer, not FastAPI.

**Frontend (adapter-node).** adapter-node reads `HOST`, `PORT`, and `ORIGIN` from the
runtime env (these are adapter-node's own built-in conventions, not custom code).
`HOST=0.0.0.0` is the single bind that makes it reachable from the phone.

---

## 3. The LAN launch recipe + QR + LAN-IP detection (the centrepiece)

Two files. `scripts/lan.sh` orchestrates; `scripts/lan.py` provides two pure helpers
(LAN-IP detection, QR rendering).

### LAN IP detection — the UDP-connect trick (`scripts/lan.py`)

No DNS, no packet sent. "Connect" a UDP socket to a public address and read back the source
IP the kernel *would* route through:

```python
import socket

def detect_lan_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))   # no packet is sent for a connected UDP socket
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"               # offline / no LAN → degrade to loopback
    finally:
        sock.close()
```

### QR rendering — `qrcode` printed as ASCII to the terminal (`scripts/lan.py`)

```python
import qrcode

def print_qr(origin: str) -> None:
    qr = qrcode.QRCode(border=2)
    qr.add_data(origin)
    qr.make(fit=True)
    qr.print_ascii(invert=True)   # invert=True so dark modules scan on a dark terminal
```

CLI surface: `python scripts/lan.py --ip` prints the IP for the shell to capture;
`python scripts/lan.py --qr <ORIGIN>` prints the URL then the QR. `qrcode>=8.2`.

### The launch script (`scripts/lan.sh`) — compute the origin ONCE

The key idea Assay calls **the origin triad**: the LAN origin string is computed once and
used for three things that must agree — the adapter-node `ORIGIN` env, the QR payload, and
(by construction, since adapter-node derives `event.url.origin` from `ORIGIN`) the CSRF
guard's comparison value. A mismatch means the phone loads an origin the guard rejects and
every mutation 403s silently.

```bash
set -euo pipefail
PORT="${1:-${PORT:-3000}}"
API_PORT=8000

# Compute the LAN origin ONCE — this single value is the triad.
LAN_IP="$(uv run python scripts/lan.py --ip)"
ORIGIN="http://${LAN_IP}:${PORT}"

(cd frontend && bun run build)     # adapter-node output in frontend/build

# FastAPI on loopback only — the phone reaches it solely via the node /api proxy.
ASSAY_HOST=127.0.0.1 ASSAY_PORT="${API_PORT}" uv run assay serve &
API_PID=$!
wait_for "FastAPI" "http://127.0.0.1:${API_PORT}/healthz" "${API_PID}"

# The built node front door, bound LAN-wide. HOST=0.0.0.0 is the load-bearing bind.
(cd frontend && HOST=0.0.0.0 PORT="${PORT}" \
	ASSAY_API_ORIGIN="http://127.0.0.1:${API_PORT}" ORIGIN="${ORIGIN}" \
	node build) &
NODE_PID=$!
wait_for "node front door" "http://127.0.0.1:${PORT}/" "${NODE_PID}"

# Print the SAME origin string as URL + QR.
uv run python scripts/lan.py --qr "${ORIGIN}"
wait
```

Two robustness details worth keeping:

- A `cleanup()` trap on `EXIT INT TERM` kills both background PIDs on Ctrl-C.
- `wait_for name url pid` polls readiness (40 × 0.5s) **and** checks `kill -0 $pid` each
  loop, so a server that dies on startup (e.g. port already in use) fails loudly instead of
  printing a healthy-looking QR that hits `ECONNREFUSED` on scan. The QR is only printed
  once both servers actually answer.

**Tooling gotcha (from integration-notes.md):** invoking `node build` in a *non-interactive*
shell can hit a broken lazy-nvm wrapper (`_load_nvm: command not found`). In an interactive
shell nvm resolves fine, so `lan.sh` run by a human is OK; for headless probing call the real
binary path directly (`~/.nvm/versions/node/v22.19.0/bin/node`).

---

## 4. Shared-token / auth gating: there is none — a CSRF origin assertion instead

Assay is explicitly single-user, single-LAN, no internet (a locked constraint), so there is
**no token and no auth**. What it does add (ADR 0015) is a tiny CSRF guard at the node front
door, because once the door is on the LAN a webpage open in the user's browser could POST to
the LAN host cross-origin and the browser would deliver it.

In `hooks.server.ts`, inside the `/api/*` block, before the upstream `fetch`:

```ts
function isTrustedOrigin(origin: string, expected: string): boolean {
	return origin === expected;   // v1 policy: strict same-origin
}

// Reject a mutation only when ALL hold: non-GET, a *present* Origin, and the policy rejects it.
const origin = event.request.headers.get('origin');
if (
	event.request.method !== 'GET' &&
	origin !== null &&
	!isTrustedOrigin(origin, event.url.origin)
) {
	return new Response(JSON.stringify({ code: 'forbidden_origin' }), {
		status: 403,
		headers: { 'content-type': 'application/json' }
	});
}
```

Why this and not SvelteKit's built-in CSRF check: Assay verified against the installed
`@sveltejs/kit` source that the built-in check (a) lives inside `resolve()`, which the
`/api/*` early-return bypasses, and (b) is gated to form content-types, so a JSON POST is
exempt anyway. So the guard is hand-rolled, content-type-agnostic, and isolated in one
function. An **absent** `Origin` is *allowed* (a cross-origin browser POST always carries
`Origin` per the Fetch spec, so absent means same-origin SSR re-entry or a trusted local
agent). The documented future extension is an RFC-1918 private-range allowlist for
multi-device / DHCP churn, which is a one-function change.

**Caveat to inherit:** strict same-origin means the app must be reached via the *printed LAN
URL the QR encodes*. Hitting `http://localhost:PORT` while the server's `ORIGIN` is the LAN
IP will 403 on mutations. Use the printed IP, or `vite dev` for local work.

For Glyde, a read-mostly app, this matters less (GETs are never policed). If Glyde has *any*
mutation over the LAN (bookmarks, progress, settings), keep the guard; if it is truly
read-only, the guard costs nothing and is still correct.

---

## 5. HTTPS / secure-context — the biggest gotcha, and it matters MORE for Glyde

This is the single most important finding, discovered only on the physical iPhone
(integration-notes.md, "Device pass 2026-06-19"):

> **RELEASE-BLOCKER: `crypto.randomUUID()` is secure-context-only.** It is `undefined` over
> plain HTTP on a LAN IP (exactly the phone deployment). Every `loop.submit` threw before
> posting; no swipe or button could label, and no error surfaced. The whole test suite missed
> it because component tests inject ids and CI/e2e run on `localhost` (a secure context).

The fix (`frontend/src/lib/domains/labelling.svelte.ts`) — fall back to `getRandomValues`,
which has no secure-context restriction, and assemble the v4 UUID by hand:

```ts
function randomId(): string {
	if (typeof crypto.randomUUID === 'function') return crypto.randomUUID();
	const bytes = crypto.getRandomValues(new Uint8Array(16));
	let hex = '';
	bytes.forEach((byte, i) => {
		let b = byte;
		if (i === 6) b = (b & 0x0f) | 0x40; // version 4
		if (i === 8) b = (b & 0x3f) | 0x80; // variant 10xx
		hex += b.toString(16).padStart(2, '0');
	});
	return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}
```

The broader rule: **`http://<lan-ip>` is NOT a secure context.** Secure-context-only web
APIs that silently break over plain-HTTP LAN include `crypto.randomUUID`, `crypto.subtle`,
service worker registration, and PWA install. `localhost` *is* a secure context, which is
exactly why every automated gate missed it.

### What this means for Glyde specifically

Assay *deferred* HTTPS-over-LAN and PWA-on-phone because its labelling loop works fine over
HTTP. **Glyde should not defer it.** Glyde wants an installable, offline-capable reader on
the phone — that requires a service worker and `display: standalone`, which require a secure
context, which a plain-HTTP LAN origin is not. So for Glyde, HTTPS-over-LAN is on the
critical path, not a nice-to-have.

The documented (not-yet-built) path Assay recorded:

> HTTPS-over-LAN = a custom `node:https` server wrapping the adapter-node handler + an
> `mkcert`-generated cert whose local CA is trusted on the device.

Concretely for Glyde: generate a cert for the LAN IP with `mkcert <lan-ip>`, install the
mkcert root CA on the phone once (`mkcert -CAROOT` → AirDrop/email the `rootCA.pem`, trust it
in iOS Settings), and front adapter-node with `node:https` using that cert. Then `theme-color`,
the service worker, and Add-to-Home-Screen all work, and `crypto.randomUUID` is defined again
(though keep the fallback regardless — it is free insurance).

### mDNS / `.local` discovery

Assay considered `.local` a "nice-to-have" and **did not build it** (`docs/Assay_Full_Context.md`:
*"bind 0.0.0.0 on a fixed port, print the IP + a QR code on startup; mDNS `.local` is a
nice-to-have"*). Its discovery story is purely: detect the LAN IP, print URL + QR. For Glyde,
the QR is enough for a phone; an mDNS hostname (`glyde.local`) would mainly help if you want a
stable cert SAN that survives DHCP IP changes (mkcert a hostname instead of an IP).

---

## 6. PWA: manifest, service worker, install hint

All three exist in Assay and are valid on `localhost` / a future HTTPS origin (the SW
registration is gated so it never runs in dev or insecure contexts).

### Manifest (`frontend/static/manifest.json`)

```json
{
	"name": "Assay",
	"short_name": "Assay",
	"id": "/",
	"start_url": "/",
	"scope": "/",
	"display": "standalone",
	"orientation": "portrait",
	"background_color": "#0a0a0a",
	"theme_color": "#0a0a0a",
	"icons": [
		{ "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any" },
		{ "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any" },
		{ "src": "/icons/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
	]
}
```

Icon set actually shipped in `frontend/static/icons/`: `icon-192.png`, `icon-512.png`,
`icon-maskable-512.png`, `apple-touch-icon.png` (180px). `theme_color` is kept in sync with
the dark `--background` token.

### Linked + registered in `frontend/src/routes/+layout.svelte`

```svelte
<svelte:head>
	<link rel="icon" href={favicon} />
	<link rel="manifest" href="/manifest.json" />
	<meta name="theme-color" content="#0a0a0a" />
	<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png" />
</svelte:head>
```

```ts
// Gated: never during SSR, never in dev (Vite serves no immutable assets to cache and the
// SW can fight HMR), never without SW support. (Implicitly also a no-op over insecure HTTP.)
$effect(() => {
	if (browser && !dev && 'serviceWorker' in navigator) {
		navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch((err: unknown) => {
			console.debug('[assay] service worker registration skipped:', err);
		});
	}
});
```

### Service worker (`frontend/static/sw.js`) — a classic, shell-cache-only worker

Plain JS served as-is from `/static` (a classic worker, not a module, not TS). The
load-bearing property: **`/api/*` is a genuine passthrough** — the very first statement of
the fetch handler returns `undefined` (no `respondWith`), so a cache miss can never shadow a
live API read/mutation. It caches *only* content-hashed immutable build assets
(`/_app/immutable/**`), never HTML navigations (SSR must reflect live state), never
cross-origin, never non-GET.

```js
const CACHE = 'assay-shell-v1';          // manual version bump = the only cache-invalidation lever
const IMMUTABLE_PREFIX = '/_app/immutable/';

function handleFetch(event) {
	const url = new URL(event.request.url);
	if (url.pathname === '/api' || url.pathname.startsWith('/api/')) return undefined; // passthrough, FIRST
	if (event.request.method !== 'GET') return undefined;
	if (url.origin !== selfOrigin()) return undefined;
	const isNavigation = event.request.mode === 'navigate'
		|| (event.request.headers.get('accept') || '').includes('text/html');
	if (isNavigation) return undefined;    // never cache HTML — SSR reflects live state
	if (url.pathname.startsWith(IMMUTABLE_PREFIX)) return cacheFirst(event.request);
	return undefined;
}
```

For Glyde this is the right starting shape, but Glyde will likely want **more** caching: a
reading app benefits from caching the Digest IR JSON for offline reading. That is a
deliberate extension (cache reads under a versioned key, stale-while-revalidate), not the
conservative shell-only posture Assay needed for a blind-labelling correctness invariant.

### iOS install hint (`frontend/src/lib/components/InstallHint.svelte`)

iOS Safari has no `beforeinstallprompt`, so the only install path is the manual Share → Add
to Home Screen gesture, which the user must be told about. Assay shows a dismissible bottom
strip *only* when all hold: UA is iOS Safari proper (not CriOS/FxiOS/in-app webviews), not
already `standalone`, and not previously dismissed (`localStorage`). Detection helpers worth
copying:

```ts
function isIosSafari(ua: string): boolean {
	const isIos = /iphone|ipad|ipod/i.test(ua);
	if (!isIos) return false;
	const isOtherBrowser = /crios|fxios|edgios|opios|fban|fbav|instagram/i.test(ua);
	return !isOtherBrowser;
}
function isStandalone(): boolean {
	const nav = navigator as Navigator & { standalone?: boolean };
	return nav.standalone === true || window.matchMedia('(display-mode: standalone)').matches;
}
```

The strip is a `role="region"` with an accessible name and a real ≥44px (`min-h-11
min-w-11`) close button, positioned `fixed inset-x-0 bottom-0` so it never covers the content
(a noted caveat: on very short screens validate it does not overlap the action controls).

---

## 7. Mobile viewport, responsive layout, touch targets, iOS gotchas

### Viewport (`frontend/src/app.html`)

```html
<meta name="viewport"
	content="width=device-width, initial-scale=1, interactive-widget=resizes-content" />
```

`interactive-widget=resizes-content` is the #1 platform fix: it keeps the on-screen keyboard
from scrolling content off-screen during text entry. Directly relevant to Glyde if it has any
text input (notes, search, settings).

Dark-mode-first with no flash: the `dark` class is on the served `<html>` shell so the app
paints dark on first render with zero JS (`<html lang="en" class="dark">`), and
`color-scheme` follows the cascade so native UA surfaces (scrollbars, the iOS
overscroll/rubber-band area, the pre-paint background) match. Useful for Glyde, where a
dyslexia-friendly tinted/low-contrast background is a likely default and a white flash on load
would be jarring.

### The distilled iOS gotcha list (`frontend/CLAUDE.md`)

> `interactive-widget=resizes-content` viewport flag; `overscroll-behavior-y: contain` on
> the card; `preventDefault()` on arrow keys; swipe = velocity + distance threshold with
> snap-back and a separate evidence scroll zone; test on a physical iPhone before shipping.

Plus, from the device pass:

- **Textarea / input font-size must be ≥16px** or iOS auto-zooms the page on focus. Assay's
  fix was `text-sm → text-base` on the note textarea. For a reading app this is doubly
  important — large legible text is the product.
- **`overscroll-behavior-y: contain`** on a scroll container stops Safari pull-to-refresh
  from firing on a downward drag.
- **`overflow-x-clip` on `<main>`** so a swipe/transform can never shift the body or create a
  horizontal scrollbar.
- Hide keyboard-hint affordances on coarse pointers (touch) — e.g. a `<p>` with the keyboard
  shortcut legend is `hidden` on coarse-pointer devices.

### Touch targets

≥44px everywhere, expressed in Tailwind as `min-h-11 min-w-11` (44px) on every interactive
control, with `focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none` for
keyboard parity.

---

## 8. Swipe / touch gesture pattern (directly reusable for a reader's page nav)

Assay's swipe is built as a *clean two-layer split* that Glyde can lift for
page/section/chapter navigation (swipe left/right = next/previous), keeping vertical scroll
for reading:

- `frontend/src/lib/domains/swipe.ts` — a **pure, DOM-free classifier**. Takes a finished
  trajectory `{dx, dy, elapsedMs, width}` and returns an intent or `null` (snap-back). The
  commit rule is **distance OR velocity** (not both): `distance >= width * 0.45` (or a 90px
  floor) OR (`distance >= 40px` AND `velocity >= 0.3 px/ms`). Requiring both was the original
  jank — a slow deliberate drag never cleared the velocity gate. Node-testable in full.
- `frontend/src/lib/domains/swipe.svelte.ts` — the **DOM binding** via Pointer Events (one
  model for touch/pen/mouse). The core feel is **axis-lock on the first move past 8px**:
  horizontal locks to a swipe (the card follows the finger with a capped tilt, then commits
  or snaps back), vertical locks to scroll and the binding yields entirely (never transforms,
  never fires). This is what kills diagonal drift and the swipe-fighting-scroll problem.

Reusable specifics:

- `setPointerCapture` once a swipe locks (feature-detected — jsdom lacks it), released
  implicitly on pointerup/cancel.
- `prefers-reduced-motion` read **once at bind time**: a reduced-motion user gets no
  follow/transition (classify-on-release). The classifier is unaffected; the follow is pure
  presentation.
- A `[data-evidence-scroll]` marker on the inner scroll zone + `touch-action: pan-y` so a
  gesture begun while reading a long passage is ignored by the swipe binding (it `closest()`-
  checks the target on pointerdown). The CSS rule that *forces* this: you cannot put
  `touch-action: none` on an ancestor of a scrollable descendant, so the card uses
  `pan-y` and the binding does the horizontal/vertical discrimination in JS.
- Single-primary-pointer guard: a second finger landing mid-gesture is ignored.

For Glyde a reader rarely needs swipe-to-act, but swipe-to-paginate is a natural fit, and
this axis-lock binding is the right primitive: horizontal = page turn, vertical = scroll the
current page, no fighting.

---

## 9. Testing the mobile/LAN path (Playwright)

`frontend/playwright.config.ts` boots the **real two-server topology** (the same one
`lan.sh` uses) rather than mocking: a `webServer` array runs `uv run assay seed … && uv run
assay serve` (FastAPI on a temp SQLite DB) and `bun run build && node build` (the adapter-node
front door) with `ORIGIN` pinned so `event.url.origin` matches. This is how Glyde should e2e
the proxy + same-origin path. Note the lesson Assay learned the hard way: **e2e on `localhost`
is a secure context and will NOT catch the `crypto.randomUUID` / SW / install breakages** —
those need the physical-device pass (a `device-checklist.md` the owner runs over the LAN).
Assay ships such a checklist; Glyde should too.

---

## 10. Versions (from Assay's lockfiles, all current as of 2026-06)

| Component | Version |
|---|---|
| Python | 3.13 |
| Node | >=22.19 |
| `fastapi` | >=0.136 |
| `uvicorn[standard]` | >=0.48 |
| `pydantic-settings` | >=2.14 |
| `typer` | >=0.26 |
| `qrcode` (QR rendering) | >=8.2 (resolved 8.2) |
| `svelte` | ^5.56.1 (runes mode) |
| `@sveltejs/kit` | ^2.63.0 |
| `@sveltejs/adapter-node` | ^5.5.4 |
| `@sveltejs/vite-plugin-svelte` | ^7.1.2 |
| `vite` | ^8.0.16 |
| `tailwindcss` + `@tailwindcss/vite` | ^4.3.1 |
| `openapi-fetch` / `openapi-typescript` | 0.17.0 / 7.13.0 |

(Verify against current docs before pinning — per the external-integration rule — but this is
a known-good, recent combination of exactly Glyde's stack.)

---

## Adopt in Glyde

- **Same-origin node front door, FastAPI on loopback.** Lift `svelte.config.js`
  (adapter-node) + `hooks.server.ts` (`/api/*` reverse-proxy, prefix-strip, return before
  `resolve()`, `filterSerializedResponseHeaders` to content-type/length) + Vite dev proxy.
  FastAPI binds `127.0.0.1` always; only the node server gets `HOST=0.0.0.0`. Use FastAPI
  `root_path="/api"` + explicit `servers=[{"url":"/api"}]`. Result: zero CORS, one LAN-facing
  process. Rename the env prefix to `GLYDE_` and the proxy-target env to `GLYDE_API_ORIGIN`.

- **Copy `scripts/lan.sh` + `scripts/lan.py` almost verbatim.** The UDP-connect LAN-IP trick,
  the `qrcode` ASCII QR, the compute-`ORIGIN`-once "triad", and the `wait_for` liveness+
  readiness poll before printing the QR are all directly reusable. `pydantic-settings`
  `BaseSettings` (host/port/db injected, env read in one place) drops straight into Glyde's
  `api → adapters → core` layering.

- **Do HTTPS-over-LAN now, do not defer it (this is where Glyde diverges from Assay).** Glyde
  wants an installable, offline reader, which needs a service worker + `standalone`, which need
  a *secure context* that plain-HTTP LAN is not. Build the `node:https` + `mkcert` path Assay
  only documented: `mkcert <lan-ip-or-glyde.local>`, trust the mkcert root CA on the phone
  once, front adapter-node with `node:https`. Keep the `crypto.randomUUID → getRandomValues`
  fallback regardless — it is free insurance and the exact bug a phone-over-HTTP found.

- **Bake in the iOS/mobile gotchas day one:** viewport
  `interactive-widget=resizes-content`; dark-first no-flash shell (`<html class="dark">` +
  `color-scheme`); any text input ≥16px to stop focus-zoom (central for a reading app);
  `overscroll-behavior-y: contain` to kill pull-to-refresh; ≥44px (`min-h-11 min-w-11`) touch
  targets; PWA manifest + shell-cache SW (with `/api/*` passthrough first) + the dismissible
  iOS "Add to Home Screen" hint. For Glyde, extend the SW to cache the Digest IR for offline
  reading (a deliberate read-caching layer beyond Assay's shell-only posture).

- **Reuse the two-layer Pointer-Events swipe (pure classifier + axis-locking binding) for
  page navigation**, and reuse the testing posture: a Playwright `webServer` array that boots
  the real built node-server-over-FastAPI topology with `ORIGIN` pinned, plus an owner-run
  physical-iPhone `device-checklist.md` — because `localhost` e2e is a secure context and
  structurally cannot catch the LAN-over-HTTP class of bugs.
