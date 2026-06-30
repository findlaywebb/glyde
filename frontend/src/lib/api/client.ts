import createClient from 'openapi-fetch';
import type { Middleware } from 'openapi-fetch';
import type { paths } from './schema';
import { captureLanToken, readLanToken } from './token';
import type { TokenStore } from './token';

/**
 * The typed API client.
 *
 * `paths` is generated from the committed `docs/schemas/openapi.json` (run `npm run gen:api`
 * after the backend's `export-openapi`), so every call is checked against the FastAPI
 * contract — the frontend cannot drift from the API without a TypeScript error. Pass
 * SvelteKit's per-request `fetch` into each call from `load` so cookies and relative-URL
 * handling are preserved, and branch on `{ data, error }` (a 200 is not success; non-2xx is
 * returned, not thrown).
 *
 * Same-origin serving: the API is reached under `/api`, proxied to FastAPI by
 * `hooks.server.ts`. The module base is the relative `/api`, which is what the **browser**
 * uses. An **SSR `load`** can't use a relative base (openapi-fetch builds `new Request(base +
 * path)` before the provided `fetch` runs, and a relative URL has no origin in Node) — so
 * each `load` overrides the per-call `baseUrl` to an absolute, same-origin `${url.origin}/api`,
 * which `event.fetch` re-enters through the proxy.
 *
 * LAN token middleware: registered at module load in the browser only (skipped during SSR —
 * the node front door in `hooks.server.ts` handles server-side requests directly). On each
 * request the middleware (a) lifts any `?token=…` from the current URL search string into
 * `localStorage` via `captureLanToken` (idempotent — no-ops when the query carries none,
 * keeps the stored value across navigations), and (b) sets `Authorization: Bearer …` from
 * the stored token. Use `buildLanTokenMiddleware` with an injected store and search getter
 * in tests — no DOM needed.
 *
 * NOTE: `./schema` is generated and git-ignored on a fresh scaffold — run the backend's
 * `export-openapi` then `npm run gen:api` before this import resolves.
 */

/**
 * Build the openapi-fetch middleware that captures and attaches the LAN token.
 *
 * The `store` and `getSearch` parameters are injected so the middleware is constructible in
 * Node without a DOM. In the browser, pass `localStorage` and `() => window.location.search`.
 *
 * On each request: (a) `captureLanToken` lifts any `?token=…` from the search string into
 * the store (idempotent — no-ops when absent, preserves stored value), then (b) if a token
 * is present the returned `Request` carries `Authorization: Bearer …`. Storage failures
 * (e.g. iOS Safari private browsing `SecurityError`) are swallowed gracefully; the request
 * proceeds with whatever token was already stored.
 *
 * @param store The token store to capture into and read from.
 * @param getSearch Returns the URL query string to scan (e.g. `window.location.search`).
 *   Defaults to returning an empty string (no capture — useful in tests that seed the store
 *   directly).
 * @returns An openapi-fetch `Middleware`.
 */
export function buildLanTokenMiddleware(
	store: TokenStore,
	getSearch: () => string = () => ''
): Middleware {
	return {
		onRequest({ request }) {
			let token: string | null;
			try {
				token = captureLanToken(getSearch(), store);
			} catch {
				// Storage is blocked (e.g. iOS Safari private browsing). Fall back to whatever
				// token is already readable; if that also throws, proceed without a token.
				try {
					token = readLanToken(store);
				} catch {
					token = null;
				}
			}
			if (!token) return;
			const newHeaders = new Headers(request.headers);
			newHeaders.set('Authorization', `Bearer ${token}`);
			return new Request(request, { headers: newHeaders });
		}
	};
}

export const api = createClient<paths>({ baseUrl: '/api' });

// Browser-only: register the LAN token middleware.
// SSR requests never reach this block — the node front door handles them directly.
if (typeof window !== 'undefined') {
	api.use(buildLanTokenMiddleware(localStorage, () => window.location.search));
}
