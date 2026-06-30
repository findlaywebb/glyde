/**
 * The LAN token client lifecycle: capture from the QR URL, persist, attach.
 *
 * When `glyde serve --lan` prints its QR, the encoded URL carries `?token=…`. A phone that
 * scans it lands on the app with that query; `captureLanToken` lifts the token into storage
 * (localStorage in the browser), and `authHeaders` turns the stored token into the
 * `Authorization: Bearer …` header the node front door (`hooks.server.ts`) asserts on `/api`
 * mutations. Reads are open, so a read-only phone never needs the token — but the mechanism
 * is here for any device that mutates over the LAN.
 *
 * Every function takes an injected `TokenStore` (not a hard reference to `localStorage`), so
 * the module is pure and node-testable, and imports nothing from other elements (the `api`
 * boundary is a sink).
 *
 * `randomId` is insecure-context insurance: `crypto.randomUUID` is `undefined` over a
 * plain-HTTP LAN origin (only `https`/`localhost` are secure contexts), which would silently
 * break any client-minted id. Glyde mints ids server-side today, so this has no live caller
 * yet; it is kept as the documented fallback the moment a client mints one over plain-HTTP LAN.
 */

/** The query parameter the QR-encoded LAN URL carries the token in. */
const TOKEN_PARAM = 'token';

/** The storage key the captured LAN token is persisted under. */
const STORAGE_KEY = 'glyde:lan-token';

/** The slice of the Web Storage surface this module needs (so a fake satisfies it in tests). */
export interface TokenStore {
	getItem(key: string): string | null;
	setItem(key: string, value: string): void;
}

/**
 * Capture a `?token=…` from a scanned LAN URL into storage; return the active token.
 *
 * A present, non-empty token is persisted and returned. When the query carries no token (a
 * normal navigation), the already-stored token is returned unchanged, so the token survives
 * later same-app navigations that drop the query.
 *
 * @param search The URL query string (e.g. `window.location.search`) or a `URLSearchParams`.
 * @param store The storage to persist into and read back from.
 * @returns The active LAN token, or `null` when none is present or stored.
 */
export function captureLanToken(
	search: string | URLSearchParams,
	store: TokenStore
): string | null {
	const params = typeof search === 'string' ? new URLSearchParams(search) : search;
	const token = params.get(TOKEN_PARAM);
	if (token === null || token === '') {
		return readLanToken(store);
	}
	store.setItem(STORAGE_KEY, token);
	return token;
}

/**
 * Read the persisted LAN token.
 *
 * @param store The storage to read from.
 * @returns The stored token, or `null` if none has been captured.
 */
export function readLanToken(store: TokenStore): string | null {
	return store.getItem(STORAGE_KEY);
}

/**
 * Build the `Authorization` header for the stored LAN token.
 *
 * @param store The storage holding a previously captured token.
 * @returns `{ Authorization: 'Bearer …' }` when a token is stored, else an empty object so it
 *   spreads cleanly into a request's headers when there is no token.
 */
export function authHeaders(store: TokenStore): Record<string, string> {
	const token = readLanToken(store);
	if (token === null || token === '') {
		return {};
	}
	return { Authorization: `Bearer ${token}` };
}

/**
 * Return a v4 UUID, falling back to `getRandomValues` outside a secure context.
 *
 * `crypto.randomUUID` is secure-context-only, so it is `undefined` over a plain-HTTP LAN
 * origin; `getRandomValues` has no such restriction. The fallback assembles the v4 bytes by
 * hand (version nibble `4`, variant bits `10xx`).
 *
 * @returns A canonical v4 UUID string.
 */
export function randomId(): string {
	if (typeof crypto.randomUUID === 'function') {
		return crypto.randomUUID();
	}
	const bytes = crypto.getRandomValues(new Uint8Array(16));
	let hex = '';
	bytes.forEach((value, index) => {
		let byte = value;
		if (index === 6) {
			byte = (byte & 0x0f) | 0x40; // version 4
		}
		if (index === 8) {
			byte = (byte & 0x3f) | 0x80; // variant 10xx
		}
		hex += byte.toString(16).padStart(2, '0');
	});
	return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}
