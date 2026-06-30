// PREF store round-trip — jsdom `component` project (localStorage + the typed seam need a DOM).
// Drives `createPrefsStore` with an injected fake `fetch` (no server) and asserts: the
// synchronous localStorage mirror, the write-through full-object PUT (full-replace), the
// last-used-mode restore from the mirror, the server-as-source-of-truth reload, and the
// optimistic-keep on a failed PUT.
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
	createPrefsStore,
	DEFAULT_PREFERENCES,
	PREFS_STORAGE_KEY,
	type PreferencesView
} from './prefs.svelte';

/** A recorded request the fake `fetch` saw. */
interface RecordedCall {
	method: string;
	path: string;
	body: unknown;
}

/** Build an injected `fetch` that records calls and answers GET/PUT `/preferences`. */
function makeFetch(opts: { server?: PreferencesView; failPut?: boolean } = {}): {
	fetchImpl: typeof fetch;
	calls: RecordedCall[];
} {
	const calls: RecordedCall[] = [];
	const fetchImpl = (async (input: RequestInfo | URL): Promise<Response> => {
		const request = input as Request;
		const path = new URL(request.url).pathname;
		if (request.method === 'GET') {
			calls.push({ method: 'GET', path, body: undefined });
			return jsonResponse(opts.server ?? DEFAULT_PREFERENCES, 200);
		}
		const body = (await request.json()) as unknown;
		calls.push({ method: request.method, path, body });
		return opts.failPut ? jsonResponse({ detail: 'boom' }, 500) : jsonResponse(body, 200);
	}) as typeof fetch;
	return { fetchImpl, calls };
}

/** A JSON `Response` the typed client parses as `{ data }` (2xx) or `{ error }` (non-2xx). */
function jsonResponse(body: unknown, status: number): Response {
	return new Response(JSON.stringify(body), {
		status,
		headers: { 'content-type': 'application/json' }
	});
}

beforeEach(() => {
	localStorage.clear();
});

afterEach(() => {
	vi.restoreAllMocks();
});

describe('createPrefsStore', () => {
	it('starts from the defaults when no mirror or seed is present', () => {
		const { fetchImpl } = makeFetch();
		const store = createPrefsStore({ fetch: fetchImpl });
		expect(store.current).toEqual(DEFAULT_PREFERENCES);
		expect(store.current.mode).toBe('guided');
	});

	it('mirrors the change to localStorage synchronously, before the network settles', () => {
		const { fetchImpl } = makeFetch();
		const store = createPrefsStore({ fetch: fetchImpl });

		const pending = store.set({ mode: 'rsvp' });

		// The mirror is written before the first await — readable without awaiting `pending`.
		const mirror = JSON.parse(localStorage.getItem(PREFS_STORAGE_KEY) ?? '{}') as PreferencesView;
		expect(mirror.mode).toBe('rsvp');
		expect(store.current.mode).toBe('rsvp');
		return pending;
	});

	it('writes through the COMPLETE object to PUT /preferences (full-replace)', async () => {
		const { fetchImpl, calls } = makeFetch();
		const store = createPrefsStore({ fetch: fetchImpl });

		await store.set({ mode: 'rsvp' });

		const put = calls.find((c) => c.method === 'PUT');
		expect(put).toBeDefined();
		expect(put?.path).toBe('/api/preferences');
		// The body carries every field (a full PreferencesView), not just the patched one.
		expect(put?.body).toEqual({ ...DEFAULT_PREFERENCES, mode: 'rsvp' });
		expect(Object.keys(put?.body as object).sort()).toEqual(
			Object.keys(DEFAULT_PREFERENCES).sort()
		);
	});

	it('restores the last-used mode from the localStorage mirror on a fresh store', async () => {
		const first = createPrefsStore({ fetch: makeFetch().fetchImpl });
		await first.set({ mode: 'rsvp' });

		// A brand-new store (e.g. next page open) reads the mirror synchronously at construction.
		const second = createPrefsStore({ fetch: makeFetch().fetchImpl });
		expect(second.current.mode).toBe('rsvp');
	});

	it('reconciles to the server value on reload (server is source of truth)', async () => {
		const server: PreferencesView = { ...DEFAULT_PREFERENCES, mode: 'fading', wpm: 420 };
		const { fetchImpl, calls } = makeFetch({ server });
		const store = createPrefsStore({ fetch: fetchImpl });

		await store.reload();

		expect(calls.some((c) => c.method === 'GET' && c.path === '/api/preferences')).toBe(true);
		expect(store.current.mode).toBe('fading');
		expect(store.current.wpm).toBe(420);
		// The mirror is reconciled to the server too.
		const mirror = JSON.parse(localStorage.getItem(PREFS_STORAGE_KEY) ?? '{}') as PreferencesView;
		expect(mirror.mode).toBe('fading');
	});

	it('prefers an injected initial seed over the mirror and defaults', () => {
		localStorage.setItem(
			PREFS_STORAGE_KEY,
			JSON.stringify({ ...DEFAULT_PREFERENCES, mode: 'rsvp' })
		);
		const initial: PreferencesView = { ...DEFAULT_PREFERENCES, mode: 'fading' };
		const store = createPrefsStore({ fetch: makeFetch().fetchImpl, initial });
		expect(store.current.mode).toBe('fading');
	});

	it('keeps the optimistic value when the PUT fails (no rollback)', async () => {
		const warn = vi.spyOn(console, 'warn').mockImplementation(() => {});
		const { fetchImpl } = makeFetch({ failPut: true });
		const store = createPrefsStore({ fetch: fetchImpl });

		await store.set({ mode: 'rsvp' });

		expect(store.current.mode).toBe('rsvp');
		const mirror = JSON.parse(localStorage.getItem(PREFS_STORAGE_KEY) ?? '{}') as PreferencesView;
		expect(mirror.mode).toBe('rsvp');
		expect(warn).toHaveBeenCalled(); // the error is surfaced, the value is not rolled back
	});
});
