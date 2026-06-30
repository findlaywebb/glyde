import type { Handle } from '@sveltejs/kit';
import { env } from '$env/dynamic/private';

/**
 * The same-origin LAN front door: proxy `/api/*` to FastAPI behind two guards, serve the rest.
 *
 * The app ships same-origin — the browser never makes a cross-origin request, so it needs no
 * CORS. This `handle` is the single public door: requests under `/api` are reverse-proxied to
 * the FastAPI backend (its origin is the server-only `GLYDE_API_ORIGIN`, default localhost)
 * with the `/api` prefix stripped, since the backend's own paths are bare (`/digests`,
 * `/healthz`); everything else is rendered by SvelteKit. The browser hits the relative `/api`
 * base and SSR `load`s hit `${url.origin}/api` — a same-origin `event.fetch` re-enters this
 * handler in-process through `respond()`, so both paths flow through here and neither is a
 * cross-origin read. Loop-safe by construction: `GLYDE_API_ORIGIN` is a distinct origin (a
 * different port) from the node server, so the upstream `fetch` can't re-enter.
 *
 * Over the LAN (`glyde serve --lan`) this door binds `0.0.0.0`, so before proxying a *mutation*
 * it runs two complementary guards (`guardApiMutation`): a CSRF origin assertion and a bearer
 * token. Reads (`GET`) are always open — the phone is read-only — so a digest fetch never needs
 * the token. The token is supplied to the node process as `GLYDE_LAN_TOKEN`; the CSRF compare
 * value is `event.url.origin`, which adapter-node derives from the same `ORIGIN` the QR encodes
 * (the assay "triad": adapter `ORIGIN` env = QR payload = CSRF compare).
 *
 * What this does NOT do:
 * - No CORS, no retry/translation of upstream failures — a backend that is down surfaces as the
 *   framework's 500, which is the honest signal for a transport layer.
 * - It is a *guard*, not authentication: the token gates LAN mutations; it is not a login.
 *
 * Invariants:
 * - `/api` requests are proxied and **return before `resolve()`** — they never touch routing.
 * - A mutation is rejected (no upstream call) when its present `Origin` is cross-origin (403)
 *   or, when a token is configured, its `Authorization` is not `Bearer <token>` (401). An
 *   absent `Origin` is allowed (trusted SSR re-entry / a local agent); the token still applies.
 * - Non-`/api` requests pass to `resolve()` and forward only the two response headers
 *   `openapi-fetch` reads off a serialized SSR `load` fetch (`content-type`, `content-length`);
 *   by default SvelteKit strips replayed headers, which would make a hydrating typed-seam read
 *   throw.
 */
const API_ORIGIN = env.GLYDE_API_ORIGIN ?? 'http://127.0.0.1:8000';

// The LAN bearer token. Empty (the default, e.g. plain localhost serve or dev) disables the
// token check; `serve --lan` always mints one and passes it as GLYDE_LAN_TOKEN, so the guard
// is active exactly when the door is on the LAN.
const LAN_TOKEN = env.GLYDE_LAN_TOKEN ?? '';

/** The per-request inputs the mutation guard compares against. */
export interface ApiGuardConfig {
	/** The origin a present `Origin` header must equal (strict same-origin CSRF). */
	expectedOrigin: string;
	/** The required bearer token; empty disables the token check. */
	lanToken: string;
}

/** Build a small JSON rejection with a machine-readable `code` (mirrors the API's shape). */
function guardRejection(status: number, code: string): Response {
	return new Response(JSON.stringify({ code }), {
		status,
		headers: { 'content-type': 'application/json' }
	});
}

/**
 * Decide whether an `/api` request may proceed, returning a rejection `Response` or `null`.
 *
 * Reads (`GET`) always pass. A mutation is rejected when its present `Origin` is cross-origin
 * (403 `forbidden_origin`) or, when a token is configured, its `Authorization` is not the
 * expected `Bearer <token>` (401 `missing_token`). An absent `Origin` is allowed (a
 * cross-origin browser POST always sends one per the Fetch spec, so absent means same-origin
 * SSR re-entry or a trusted local agent); the token check still applies.
 *
 * @param request The incoming request.
 * @param config The expected origin and token to compare against.
 * @returns A rejection `Response`, or `null` to allow the request through.
 */
export function guardApiMutation(request: Request, config: ApiGuardConfig): Response | null {
	if (request.method === 'GET') {
		return null;
	}
	const origin = request.headers.get('origin');
	if (origin !== null && origin !== config.expectedOrigin) {
		return guardRejection(403, 'forbidden_origin');
	}
	if (
		config.lanToken !== '' &&
		request.headers.get('authorization') !== `Bearer ${config.lanToken}`
	) {
		return guardRejection(401, 'missing_token');
	}
	return null;
}

export const handle: Handle = ({ event, resolve }) => {
	const { pathname, search } = event.url;
	if (pathname === '/api' || pathname.startsWith('/api/')) {
		// Guard mutations at the door (CSRF origin + bearer token) before any upstream call.
		const rejection = guardApiMutation(event.request, {
			expectedOrigin: event.url.origin,
			lanToken: LAN_TOKEN
		});
		if (rejection !== null) {
			return rejection;
		}
		// Strip the `/api` prefix; the backend serves bare paths behind it. Cloning the request
		// carries the method, headers, and a correctly-duplexed body unchanged.
		const upstream = `${API_ORIGIN}${pathname.slice('/api'.length)}${search}`;
		return fetch(new Request(upstream, event.request));
	}
	return resolve(event, {
		filterSerializedResponseHeaders: (name) => name === 'content-type' || name === 'content-length'
	});
};
