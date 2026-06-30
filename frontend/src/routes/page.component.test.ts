import { render, screen } from '@testing-library/svelte';
import { describe, expect, it } from 'vitest';
import type { components } from '$lib/api/schema';
import Page from './+page.svelte';

type DigestListItem = components['schemas']['DigestListItemView'];

/** Build a `DigestListItemView` with sensible defaults; any field can be overridden. */
function makeDigest(
	overrides: {
		meta?: Partial<DigestListItem['meta']>;
		counts?: Partial<DigestListItem['counts']>;
	} = {}
): DigestListItem {
	return {
		meta: {
			slug: 'brave-fox',
			name: 'Test Digest',
			provenance: {
				source_kind: 'cli',
				producer: null,
				ingested_via: 'cli',
				enriched: false
			},
			created_at: '2024-01-15T10:00:00Z',
			est_reading_ms: 50_000,
			token_count: 250,
			id: 'test-id',
			content_sha: 'abc123',
			ir_version: 1,
			owner_id: 'local',
			tags: [],
			reading_hint: null,
			...overrides.meta
		},
		counts: {
			words: 250,
			blocks_by_kind: { code: 2 },
			...overrides.counts
		}
	};
}

// The root route has no path parameters; `params` is typed as `Record<string, never>` in
// SvelteKit for parameter-free routes. Cast the props to bypass the strict auto-generated
// type while keeping the test realistic (the data shape IS the real DigestListItemView).
type PageInput = Parameters<typeof render<typeof Page>>[1];

function renderPage(digests: DigestListItem[]): ReturnType<typeof render<typeof Page>> {
	return render(Page, { data: { digests } } as PageInput);
}

describe('library home page', () => {
	it('renders the digest name as a heading linked to the reader', () => {
		// Name surfaces as a level-2 heading whose anchor leads to /d/{slug}.
		renderPage([makeDigest()]);
		const heading = screen.getByRole('heading', { name: 'Test Digest' });
		expect(heading).toBeInTheDocument();
		const link = heading.querySelector('a');
		expect(link).toHaveAttribute('href', '/d/brave-fox');
	});

	it('renders the slug in mono treatment as a second link to the reader', () => {
		// Slug is visible mono text that also links to the reader route.
		renderPage([makeDigest()]);
		const slugLink = screen.getByRole('link', { name: 'brave-fox' });
		expect(slugLink).toHaveAttribute('href', '/d/brave-fox');
	});

	it('renders digests in the order the server returns them (newest-first)', () => {
		// Card order matches the load data order (the server returns newest-first).
		const digests = [
			makeDigest({ meta: { slug: 'alpha-one', name: 'Alpha Digest' } }),
			makeDigest({ meta: { slug: 'beta-two', name: 'Beta Digest' } })
		];
		renderPage(digests);
		const headings = screen.getAllByRole('heading', { level: 2 });
		expect(headings[0]).toHaveTextContent('Alpha Digest');
		expect(headings[1]).toHaveTextContent('Beta Digest');
	});

	it('shows the empty-state prompt when there are no digests', () => {
		// Empty feed shows an actionable prompt to add a digest.
		renderPage([]);
		expect(screen.getByText(/no digests yet/i)).toBeInTheDocument();
	});

	it('shows word count and reading time shape badges', () => {
		// A 250-word, 50 s digest surfaces the expected badge text.
		renderPage([makeDigest()]);
		expect(screen.getByText('250 words')).toBeInTheDocument();
		expect(screen.getByText('~50s')).toBeInTheDocument();
	});

	it('shows the block-mix badge when the digest has blocks', () => {
		// A digest with 2 code blocks surfaces the "2 code" shape badge.
		renderPage([makeDigest()]);
		expect(screen.getByText('2 code')).toBeInTheDocument();
	});

	it('hides the block-mix badge when the digest has no blocks', () => {
		// Empty blocks_by_kind → the block-mix badge is absent.
		renderPage([makeDigest({ counts: { words: 250, blocks_by_kind: {} } })]);
		expect(screen.queryByText(/code/)).not.toBeInTheDocument();
	});

	it('renders provenance metadata for each card', () => {
		// The source kind surfaces in the provenance line.
		renderPage([makeDigest()]);
		// The formatted provenance contains the source kind "cli".
		expect(screen.getByText(/cli/)).toBeInTheDocument();
	});

	it('renders a producer in the provenance when present', () => {
		// When provenance.producer is set it appears in the card provenance text.
		renderPage([
			makeDigest({
				meta: {
					provenance: {
						source_kind: 'agent',
						producer: 'claude-3',
						ingested_via: 'api',
						enriched: false
					}
				}
			})
		]);
		expect(screen.getByText(/claude-3/)).toBeInTheDocument();
	});
});
