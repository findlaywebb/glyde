# 0006 — LAN serving: a bearer-token guard and an origin assertion in the proxy

Status: accepted

Records the design for serving Glyde to a phone on the home LAN. The decision is locked here;
the implementation is delivered by the parallel LAN unit (a relief valve — see Consequences for
the degradation path). Supersedes the "Note for LAN / multi-device deployments" in ADR-0003.

## Context

The primary user reads on mobile, so v1 wants to serve the whole app to a phone on the home LAN:
scan a QR, read a digest. That means binding a front door to `0.0.0.0`, which exposes the app to
every device on the network — a different threat model from the loopback-only default.

Two existing decisions constrain the design. ADR-0003 ships the app **same-origin with no CORS**
(the SvelteKit node server reverse-proxies `/api/*` to a loopback FastAPI) and explicitly deferred
the LAN guard: *"add an origin-assertion guard in `handle()` … add it as its own ADR when the
deployment changes."* This is that ADR. ADR-0005 **froze the OpenAPI seam**: the committed
`openapi.json` must equal the live app byte-for-byte, and a test enforces it — so LAN may not add,
remove, or alter any FastAPI path operation.

Two more facts shape it. SvelteKit's built-in CSRF guard does **not** fire for JSON `/api/*`
requests, so cross-site form posts to a mutation are not blocked for free. And the goal is a
low-friction **read-only** phone, not multi-user authentication — hosted, real auth is Later.

## Decision

**Serve through the node proxy and guard at that one door; add no server route.**

- **Process topology.** `serve_lan(settings)` runs FastAPI under uvicorn on **loopback**
  (`127.0.0.1:{port}`) and spawns the built `adapter-node` server on **`0.0.0.0:{lan_port}`**. The
  node server is the single front door; the phone never talks to FastAPI directly. `handle()`
  returns before `resolve()` for `/api/*`, strips `/api`, and proxies to `GLYDE_API_ORIGIN` (the
  loopback FastAPI).
- **Two complementary guards in `hooks.server.ts`** (the proxy layer, never a server route):
  1. **Origin assertion** — reject a non-GET whose *present* `Origin` header fails strict
     same-origin. An **absent** `Origin` is allowed (trusted SSR re-entry and local agents send
     none). This is the CSRF guard ADR-0003 deferred.
  2. **Bearer token on mutations only** — assert the token on `/api` writes; **reads stay open**
     (the phone is read-only). The token is read from `settings.lan_token` (minted when unset),
     carried in the QR as `?token=…`, persisted to `localStorage`, and replayed as
     `Authorization: Bearer …` by the frontend api client.
- **Compute `ORIGIN` once — the triad.** The adapter-node `ORIGIN` env, the QR payload, and the
  CSRF compare value are the **same** computed LAN origin. A mismatch silently 403s every mutation,
  so deriving it once removes the highest-risk drift. Reach the app via the printed LAN URL the QR
  encodes; `localhost` against a LAN `ORIGIN` 403s on mutations.
- **HTTPS-over-LAN for a secure context.** An installable/offline reader needs a secure context a
  plain-HTTP LAN origin is not, so `serve_lan` can front adapter-node with a `node:https` wrapper
  using an **mkcert** cert for the LAN IP / `glyde.local` (`settings.lan_https`, `lan_cert_path`,
  `lan_key_path`, all declared up front). Trust the mkcert root CA on the phone once.
- **No new path operation.** `glyde.api.routes.lan` stays the route-less router F0 registered, and
  the guard lives entirely in the proxy — so the ADR-0005 seam is untouched and its drift test stays
  green. A LAN feature that genuinely needed a server route would be an OpenAPI re-freeze (a future
  decision), not a LAN-unit edit.

## Consequences

- **The token is a guard, not authentication — and says so.** It is a deterrent against accidental
  or casual writes from another device on a trusted home LAN, keyed to a read-only phone. It is not
  multi-user auth, not a secret-management story, and not a substitute for the hosted model (Later).
- **Reads are deliberately open.** Anyone on the LAN can read any digest by URL; that is acceptable
  for the N=1 home-network dogfood and keeps the QR-to-read flow frictionless. Mutations require the
  token; the origin assertion blocks cross-site writes.
- **The seam stays frozen.** Because the guard is proxy-only and FastAPI is unchanged, the LAN work
  never touches `openapi.json` or `cli.py` (the `--lan` flag only delegates to `serve_lan`).
- **LAN is a relief valve; it degrades cleanly.** If cut, F0's `serve_lan` stub ships — uvicorn on
  loopback, no node spawn, no QR, no token guard — and the frontend still builds green. Within LAN,
  HTTPS degrades first (HTTPS → plain-HTTP LAN → localhost); over plain HTTP the service worker
  simply never registers, which is correct.
- F0 declared the full `lan_*` settings surface up front so the LAN unit fills the implementation
  without re-editing `settings.py`, a pyproject, or `uv.lock`.
