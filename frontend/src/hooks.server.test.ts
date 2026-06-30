import type { RequestEvent } from '@sveltejs/kit';
import { describe, expect, test, vi } from 'vitest';
import { authHeaders, captureLanToken, randomId, readLanToken } from '$lib/api/token';
import type { TokenStore } from '$lib/api/token';
import { guardApiMutation, handle } from './hooks.server';

const ORIGIN = 'http://10.0.0.5:3000';
const URL_UNDER_TEST = `${ORIGIN}/api/digests`;

/** Build a request to the LAN `/api` door with a method and optional headers. */
function apiRequest(method: string, headers: Record<string, string> = {}): Request {
	return new Request(URL_UNDER_TEST, { method, headers });
}

/** Assert a guard outcome is a rejection with the given status and machine-readable code. */
async function expectRejection(res: Response | null, status: number, code: string): Promise<void> {
	expect(res).not.toBeNull();
	if (res === null) {
		return; // narrows for the type-checker; the assertion above already failed
	}
	expect(res.status).toBe(status);
	expect(await res.json()).toEqual({ code });
}

describe('guardApiMutation', () => {
	test('a read (GET) is always open, even cross-origin with a token set', () => {
		const res = guardApiMutation(apiRequest('GET', { origin: 'http://evil.example' }), {
			expectedOrigin: ORIGIN,
			lanToken: 'secret'
		});
		expect(res).toBeNull();
	});

	test('a mutation with no token configured and no Origin proceeds', () => {
		const res = guardApiMutation(apiRequest('POST'), { expectedOrigin: ORIGIN, lanToken: '' });
		expect(res).toBeNull();
	});

	test('a cross-origin mutation is rejected 403 (CSRF), even with a valid token', async () => {
		const res = guardApiMutation(
			apiRequest('POST', { origin: 'http://evil.example:9', authorization: 'Bearer secret' }),
			{ expectedOrigin: ORIGIN, lanToken: 'secret' }
		);
		await expectRejection(res, 403, 'forbidden_origin');
	});

	test('a same-origin mutation with no token is rejected 401', async () => {
		const res = guardApiMutation(apiRequest('POST', { origin: ORIGIN }), {
			expectedOrigin: ORIGIN,
			lanToken: 'secret'
		});
		await expectRejection(res, 401, 'missing_token');
	});

	test('a same-origin mutation with the wrong token is rejected 401', async () => {
		const res = guardApiMutation(
			apiRequest('POST', { origin: ORIGIN, authorization: 'Bearer wrong' }),
			{ expectedOrigin: ORIGIN, lanToken: 'secret' }
		);
		await expectRejection(res, 401, 'missing_token');
	});

	test('a same-origin mutation with the right Bearer token proceeds', () => {
		const res = guardApiMutation(
			apiRequest('POST', { origin: ORIGIN, authorization: 'Bearer secret' }),
			{ expectedOrigin: ORIGIN, lanToken: 'secret' }
		);
		expect(res).toBeNull();
	});

	test('the Bearer scheme is matched case-insensitively (RFC 7235), the token exactly', async () => {
		const ok = guardApiMutation(apiRequest('POST', { authorization: 'bearer secret' }), {
			expectedOrigin: ORIGIN,
			lanToken: 'secret'
		});
		expect(ok).toBeNull();
		const wrongToken = guardApiMutation(apiRequest('POST', { authorization: 'BEARER Secret' }), {
			expectedOrigin: ORIGIN,
			lanToken: 'secret'
		});
		await expectRejection(wrongToken, 401, 'missing_token');
	});

	test('an absent Origin is allowed (SSR/local agent) but the token still applies', async () => {
		const ok = guardApiMutation(apiRequest('POST', { authorization: 'Bearer secret' }), {
			expectedOrigin: ORIGIN,
			lanToken: 'secret'
		});
		expect(ok).toBeNull();
		const missing = guardApiMutation(apiRequest('POST'), {
			expectedOrigin: ORIGIN,
			lanToken: 'secret'
		});
		await expectRejection(missing, 401, 'missing_token');
	});
});

describe('handle', () => {
	/** A minimal fake event carrying only the url + request `handle` reads. */
	function fakeEvent(url: string, request: Request): RequestEvent {
		return { url: new URL(url), request } as unknown as RequestEvent;
	}

	test('a bad-origin /api mutation is rejected 403 without reaching resolve()', async () => {
		const resolve = vi.fn(() => Promise.resolve(new Response('routed')));
		const request = apiRequest('POST', { origin: 'http://evil.example' });
		const res = await handle({ event: fakeEvent(URL_UNDER_TEST, request), resolve });
		expect(res.status).toBe(403);
		expect(resolve).not.toHaveBeenCalled();
	});

	test('a non-/api request is passed to resolve()', async () => {
		const routed = new Response('routed');
		const resolve = vi.fn(() => Promise.resolve(routed));
		const request = new Request(`${ORIGIN}/about`);
		const res = await handle({ event: fakeEvent(`${ORIGIN}/about`, request), resolve });
		expect(res).toBe(routed);
		expect(resolve).toHaveBeenCalledOnce();
	});
});

describe('lan token client lifecycle', () => {
	/** A `localStorage`-shaped fake backed by an in-memory map (no DOM needed). */
	function makeStore(): TokenStore {
		const map = new Map<string, string>();
		return {
			getItem: (key) => map.get(key) ?? null,
			setItem: (key, value) => {
				map.set(key, value);
			}
		};
	}

	test('captures a `?token=…` into storage and returns it', () => {
		const store = makeStore();
		expect(captureLanToken('?token=abc123', store)).toBe('abc123');
		expect(readLanToken(store)).toBe('abc123');
		expect(authHeaders(store)).toEqual({ Authorization: 'Bearer abc123' });
	});

	test('accepts a URLSearchParams as well as a query string', () => {
		expect(captureLanToken(new URLSearchParams({ token: 'p' }), makeStore())).toBe('p');
	});

	test('a query with no token keeps the previously stored token (survives navigation)', () => {
		const store = makeStore();
		captureLanToken('?token=keep', store);
		expect(captureLanToken('', store)).toBe('keep');
	});

	test('no token anywhere yields null and empty auth headers', () => {
		const store = makeStore();
		expect(captureLanToken('', store)).toBeNull();
		expect(authHeaders(store)).toEqual({});
	});

	test('randomId returns a unique v4 UUID', () => {
		const v4 = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
		expect(randomId()).toMatch(v4);
		expect(randomId()).not.toBe(randomId());
	});
});
