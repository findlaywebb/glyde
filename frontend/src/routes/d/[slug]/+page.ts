/**
 * Reader route load — fetches one digest by slug through the typed seam (R-STAGE owns).
 *
 * This `load` is what makes `/d/{slug}` resolve (LIB's deep links and the URL `glyde add` prints
 * both target it). It reads `GET /api/digests/{slug}` with the per-request `fetch` and an absolute
 * same-origin base (SSR `load`s have no origin for a relative URL), and branches `{ data, error }`
 * — a 200 is not success (assay typed-seam discipline, docs/research/assay-adoption.md §2). A 404
 * becomes a SvelteKit not-found error (the route's `+error.svelte` renders the not-found state);
 * any other failure maps to a 502 so the same error boundary surfaces it.
 *
 * SSR is off (`ssr = false`): the reader's first paint depends on the localStorage preferences
 * mirror (the last-used mode, §5.10) which only exists in the browser, so server-rendering would
 * paint the default mode and then mismatch on hydration — the same reason the Settings route opts
 * out. CSR keeps the mirror the single source of the first frame.
 *
 * Does NOT do: it fetches preferences (the store reads them client-side) and mutates no state.
 */
import { error } from '@sveltejs/kit';
import { api } from '$lib/api/client';
import type { PageLoad } from './$types';

export const ssr = false;

export const load: PageLoad = async ({ fetch, url, params }) => {
	const {
		data,
		error: apiError,
		response
	} = await api.GET('/digests/{slug}', {
		params: { path: { slug: params.slug } },
		fetch,
		baseUrl: `${url.origin}/api`
	});

	if (response.status === 404) {
		error(404, 'That digest does not exist — it may have been removed, or the link is wrong.');
	}
	if (apiError !== undefined || data === undefined) {
		error(502, 'Failed to load the digest — is the Glyde server running?');
	}

	return { digest: data };
};
