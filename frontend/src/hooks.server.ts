import type { Handle } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';

/**
 * The same-origin front door: proxy `/api/*` to FastAPI, serve the rest.
 *
 * The app ships same-origin — the browser never makes a cross-origin request, so it needs no
 * CORS. This `handle` is the single public door: requests under `/api` are reverse-proxied to
 * the FastAPI backend (its origin is the server-only `GLYDE_API_ORIGIN`, default
 * localhost) with the `/api` prefix stripped, since the backend's own paths are bare
 * (`/records`, `/healthz`); everything else is rendered by SvelteKit. The browser hits the
 * relative `/api` base and SSR `load`s hit `${url.origin}/api` — a same-origin `event.fetch`
 * re-enters this handler in-process through `respond()`, so both paths flow through here and
 * neither is a cross-origin read. Loop-safe by construction: `GLYDE_API_ORIGIN` is a
 * distinct origin (a different port) from the node server, so the upstream `fetch` can't re-enter.
 *
 * What this does NOT do:
 * - No CORS, no auth, no retry/translation of upstream failures — a backend that is down
 *   surfaces as the framework's 500, which is the honest signal for a transport layer.
 *
 * Invariants:
 * - `/api` requests are proxied and **return before `resolve()`** — they never touch routing.
 * - Non-`/api` requests pass to `resolve()` and forward only the two response headers
 *   `openapi-fetch` reads off a serialized SSR `load` fetch (`content-type`,
 *   `content-length`); by default SvelteKit strips replayed headers, which would make a
 *   hydrating typed-seam read throw.
 */
const API_ORIGIN = env.GLYDE_API_ORIGIN ?? 'http://127.0.0.1:8000';

export const handle: Handle = ({ event, resolve }) => {
	const { pathname, search } = event.url;
	if (pathname === '/api' || pathname.startsWith('/api/')) {
		// Strip the `/api` prefix; the backend serves bare paths behind it. Cloning the request
		// carries the method, headers, and a correctly-duplexed body unchanged.
		const upstream = `${API_ORIGIN}${pathname.slice('/api'.length)}${search}`;
		return fetch(new Request(upstream, event.request));
	}
	return resolve(event, {
		filterSerializedResponseHeaders: (name) =>
			name === 'content-type' || name === 'content-length'
	});
};
