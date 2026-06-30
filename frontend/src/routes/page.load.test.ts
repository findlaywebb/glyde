import { describe, expect, it, vi, beforeEach } from 'vitest';
import type { components } from '$lib/api/schema';

// Mock the API module before any imports that use it.
const mockGET = vi.fn();
vi.mock('$lib/api/client', () => ({ api: { GET: mockGET } }));

// Import after mocking so the load function picks up the mock client.
const { load } = await import('./+page');

type DigestListItem = components['schemas']['DigestListItemView'];

/** Minimal fixture — the full wire shape with realistic defaults. */
const sampleDigest: DigestListItem = {
	meta: {
		slug: 'brave-fox',
		name: 'Test',
		provenance: { source_kind: 'cli', producer: null, ingested_via: 'cli', enriched: false },
		created_at: '2024-01-15T10:00:00Z',
		est_reading_ms: 10_000,
		token_count: 50,
		id: 'id-1',
		content_sha: 'abc',
		ir_version: 1,
		owner_id: 'local',
		tags: [],
		reading_hint: null
	},
	counts: { words: 50, blocks_by_kind: {} }
};

/** Build a minimal load event with the injected fetch and url the function reads. */
function makeEvent(origin = 'http://localhost') {
	return {
		fetch: globalThis.fetch,
		url: new URL(`${origin}/`)
	} as Parameters<typeof load>[0];
}

describe('+page load', () => {
	beforeEach(() => mockGET.mockReset());

	it('returns the digests list on a successful API response', async () => {
		// A 200 response with data propagates digests to the page.
		mockGET.mockResolvedValueOnce({ data: [sampleDigest], error: undefined });
		const result = await load(makeEvent());
		// The SvelteKit PageLoad return type is `void | data`; narrow to data for the assertion.
		expect((result as { digests: DigestListItem[] }).digests).toEqual([sampleDigest]);
	});

	it('calls GET /digests with the per-request fetch and absolute same-origin base', async () => {
		// SSR requires an absolute baseUrl; using the relative '/api' would fail in Node.
		mockGET.mockResolvedValueOnce({ data: [], error: undefined });
		await load(makeEvent('http://localhost:5173'));
		expect(mockGET).toHaveBeenCalledWith('/digests', {
			fetch: globalThis.fetch,
			baseUrl: 'http://localhost:5173/api'
		});
	});

	it('throws a 502 error when the API returns an error', async () => {
		// Any API error maps to a 502 so the nearest +error.svelte handles it.
		mockGET.mockResolvedValueOnce({ data: undefined, error: { message: 'server down' } });
		await expect(load(makeEvent())).rejects.toMatchObject({ status: 502 });
	});

	it('throws a 502 error when data is undefined despite no error object', async () => {
		// A malformed response (no data AND no error) is still treated as a failure.
		mockGET.mockResolvedValueOnce({ data: undefined, error: undefined });
		await expect(load(makeEvent())).rejects.toMatchObject({ status: 502 });
	});
});
