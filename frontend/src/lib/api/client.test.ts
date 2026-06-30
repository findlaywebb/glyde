import { describe, expect, test } from 'vitest';
import { buildLanTokenMiddleware } from './client';
import { captureLanToken, readLanToken } from './token';
import type { TokenStore } from './token';
import type { MiddlewareCallbackParams } from 'openapi-fetch';

/** An in-memory `TokenStore` with no DOM dependency. */
function makeStore(): TokenStore {
	const map = new Map<string, string>();
	return {
		getItem: (key) => map.get(key) ?? null,
		setItem: (key, value) => {
			map.set(key, value);
		}
	};
}

/**
 * Drive the middleware's `onRequest` handler with a minimal fake params object.
 *
 * Only `request` is read by the middleware; the remaining `MiddlewareCallbackParams` fields
 * are cast away so tests stay concise.
 */
async function runOnRequest(
	mw: ReturnType<typeof buildLanTokenMiddleware>,
	request: Request
): Promise<Request | Response | void | undefined> {
	return mw.onRequest?.({ request } as MiddlewareCallbackParams);
}

describe('buildLanTokenMiddleware', () => {
	test('attaches Authorization header when a token is already stored', async () => {
		const store = makeStore();
		captureLanToken('?token=mytoken', store);
		const mw = buildLanTokenMiddleware(store);
		const req = new Request('http://localhost/api/test', { method: 'POST' });

		const result = await runOnRequest(mw, req);

		expect(result).toBeInstanceOf(Request);
		expect((result as Request).headers.get('Authorization')).toBe('Bearer mytoken');
	});

	test('returns undefined (no-op) when no token is stored and none in search', async () => {
		const store = makeStore();
		const mw = buildLanTokenMiddleware(store, () => '');
		const req = new Request('http://localhost/api/test', { method: 'POST' });

		const result = await runOnRequest(mw, req);

		expect(result).toBeUndefined();
	});

	test('lifts ?token=… from the search string into the store and attaches it', async () => {
		const store = makeStore();
		const mw = buildLanTokenMiddleware(store, () => '?token=lifted');
		const req = new Request('http://localhost/api/test', { method: 'GET' });

		const result = await runOnRequest(mw, req);

		// Token must be captured into the store so it persists across navigations
		expect(readLanToken(store)).toBe('lifted');

		// The request must carry the Authorization header
		expect(result).toBeInstanceOf(Request);
		expect((result as Request).headers.get('Authorization')).toBe('Bearer lifted');
	});

	test('search with no token keeps the previously stored token (survives navigation)', async () => {
		const store = makeStore();
		captureLanToken('?token=persistent', store);
		// Simulate a later navigation with no ?token= in the URL
		const mw = buildLanTokenMiddleware(store, () => '');
		const req = new Request('http://localhost/api/other', { method: 'PUT' });

		const result = await runOnRequest(mw, req);

		expect(result).toBeInstanceOf(Request);
		expect((result as Request).headers.get('Authorization')).toBe('Bearer persistent');
	});

	test('storage error (e.g. iOS private browsing) is swallowed; request proceeds without header', async () => {
		// Simulate a store where setItem throws (SecurityError in iOS private browsing).
		const throwingStore: TokenStore = {
			getItem: () => null, // nothing stored yet
			setItem: () => {
				throw new DOMException('QuotaExceededError', 'QuotaExceededError');
			}
		};
		const mw = buildLanTokenMiddleware(throwingStore, () => '?token=blocked');
		const req = new Request('http://localhost/api/test', { method: 'POST' });

		// Should not throw; returns undefined (no header) rather than crashing.
		await expect(runOnRequest(mw, req)).resolves.toBeUndefined();
	});

	test('original request headers are preserved alongside the Authorization header', async () => {
		const store = makeStore();
		captureLanToken('?token=hdr-test', store);
		const mw = buildLanTokenMiddleware(store);
		const req = new Request('http://localhost/api/test', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' }
		});

		const result = await runOnRequest(mw, req);

		expect(result).toBeInstanceOf(Request);
		const headers = (result as Request).headers;
		expect(headers.get('Content-Type')).toBe('application/json');
		expect(headers.get('Authorization')).toBe('Bearer hdr-test');
	});
});
