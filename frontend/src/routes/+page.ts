/**
 * Root page load — fetches the digest library feed.
 *
 * Uses the typed seam (`openapi-fetch` module client + committed `schema.d.ts`) with the
 * per-request `fetch` and an absolute same-origin base URL, as required for SSR `load`
 * functions. Branches `{ data, error }` — a 200 is not success — and maps any API failure
 * to a 502 so the nearest `+error.svelte` can render a user-visible message.
 *
 * Does NOT do: pagination, search, or tag filtering (Phase 2). Does NOT import any Svelte
 * stores or mutate server-side state.
 */
import { error } from '@sveltejs/kit';
import { api } from '$lib/api/client';
import type { PageLoad } from './$types';

export const load: PageLoad = async ({ fetch, url }) => {
	const { data, error: apiError } = await api.GET('/digests', {
		fetch,
		baseUrl: `${url.origin}/api`
	});

	if (apiError !== undefined || data === undefined) {
		error(502, 'Failed to load the digest library — is the Glyde server running?');
	}

	return { digests: data };
};
