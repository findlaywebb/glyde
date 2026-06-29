# 0003 — Same-origin serving via the SvelteKit node proxy

Status: accepted

## Context

A split-origin frontend/backend needs CORS, which is a recurring source of subtle bugs
(preflight, credentials, header allowlists). The app has one deployable front door anyway
(the SvelteKit node server), so it can carry the API too.

## Decision

The SvelteKit `adapter-node` server is the single public front door. `hooks.server.ts`
`handle()` reverse-proxies `/api/*` to FastAPI (origin from the server-only
`GLYDE_API_ORIGIN`, default `http://127.0.0.1:8000`), stripping the `/api` prefix so
the backend serves bare paths. Everything else is rendered by SvelteKit. The dev Vite server
proxies `/api` the same way.

FastAPI is constructed with `root_path="/api"` and `servers=[{"url": "/api"}]` so the
in-process `create_app().openapi()` (which the export CLI and drift test read) advertises the
prefix, while route paths stay bare.

Consequences: the app ships **no CORS**. The browser uses the relative `/api` base; an SSR
`load` uses an absolute same-origin `${url.origin}/api` so `event.fetch` re-enters the proxy
in-process. The only backend-origin knob is `GLYDE_API_ORIGIN`.

## Note for LAN / multi-device deployments

If the app is ever served on a LAN (a phone hitting it over the home network), add an
origin-assertion guard in `handle()` before forwarding mutations — SvelteKit's built-in CSRF
guard does not fire for JSON `/api/*` requests. That guard is intentionally omitted from the
template (localhost-only by default); add it as its own ADR when the deployment changes.
