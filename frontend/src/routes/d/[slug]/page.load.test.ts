import { describe, expect, it, vi, beforeEach } from 'vitest';
import type { components } from '$lib/api/schema';

// Mock the API module before importing the load function that uses it.
const mockGET = vi.fn();
vi.mock('$lib/api/client', () => ({ api: { GET: mockGET } }));

const { load } = await import('./+page');

type DigestView = components['schemas']['DigestView'];

/** A minimal but complete DigestView fixture. */
const sampleDigest: DigestView = {
	meta: {
		slug: 'brave-fox',
		name: 'Test digest',
		provenance: { source_kind: 'cli', producer: null, ingested_via: 'cli', enriched: false },
		created_at: '2024-01-15T10:00:00Z',
		est_reading_ms: 10_000,
		token_count: 3,
		id: 'id-1',
		content_sha: 'abc',
		ir_version: 1,
		owner_id: 'local',
		tags: [],
		reading_hint: null
	},
	segments: [
		{ type: 'prose', role: 'body', tokens: [{ text: 'hello', kind: 'word', emphasis: 'none' }] }
	]
};

/** Build a load event with the injected fetch, url, and slug param the function reads. */
function makeEvent(slug = 'brave-fox', origin = 'http://localhost') {
	return {
		fetch: globalThis.fetch,
		url: new URL(`${origin}/d/${slug}`),
		params: { slug }
	} as Parameters<typeof load>[0];
}

describe('/d/[slug] load', () => {
	beforeEach(() => mockGET.mockReset());

	it('returns the digest on a successful API response', async () => {
		mockGET.mockResolvedValueOnce({
			data: sampleDigest,
			error: undefined,
			response: { status: 200 }
		});
		const result = await load(makeEvent());
		expect((result as { digest: DigestView }).digest).toEqual(sampleDigest);
	});

	it('calls GET /digests/{slug} with the path param, per-request fetch and absolute base', async () => {
		mockGET.mockResolvedValueOnce({
			data: sampleDigest,
			error: undefined,
			response: { status: 200 }
		});
		await load(makeEvent('brave-fox', 'http://localhost:5173'));
		expect(mockGET).toHaveBeenCalledWith('/digests/{slug}', {
			params: { path: { slug: 'brave-fox' } },
			fetch: globalThis.fetch,
			baseUrl: 'http://localhost:5173/api'
		});
	});

	it('throws a 404 when the digest does not exist (not-found state)', async () => {
		mockGET.mockResolvedValueOnce({
			data: undefined,
			error: { detail: 'not found' },
			response: { status: 404 }
		});
		await expect(load(makeEvent('ghost-slug'))).rejects.toMatchObject({ status: 404 });
	});

	it('throws a 502 on any other API error', async () => {
		mockGET.mockResolvedValueOnce({
			data: undefined,
			error: { message: 'server down' },
			response: { status: 500 }
		});
		await expect(load(makeEvent())).rejects.toMatchObject({ status: 502 });
	});

	it('throws a 502 when data is undefined despite no error (malformed 2xx)', async () => {
		mockGET.mockResolvedValueOnce({ data: undefined, error: undefined, response: { status: 200 } });
		await expect(load(makeEvent())).rejects.toMatchObject({ status: 502 });
	});

	it('throws a 502 when the fetch itself rejects (offline / dead proxy)', async () => {
		mockGET.mockRejectedValueOnce(new Error('network down'));
		await expect(load(makeEvent())).rejects.toMatchObject({ status: 502 });
	});
});
