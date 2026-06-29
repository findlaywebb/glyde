import { error } from '@sveltejs/kit';
import { api } from '$lib/api/client';
import type { PageLoad } from './$types';

/**
 * Load the records list through the typed seam — the worked example of a `load`.
 *
 * Calls `GET /records` with SvelteKit's per-request `fetch` and an absolute same-origin
 * base (`${url.origin}/api`) so `event.fetch` re-enters the `hooks.server.ts` proxy with no
 * cross-origin read. A 200 is not success: a non-2xx is returned in `error`, so we branch and
 * abort the load rather than rendering a blind list.
 */
export const load: PageLoad = async ({ fetch, url }) => {
	const baseUrl = `${url.origin}/api`;
	const res = await api.GET('/records', { fetch, baseUrl });
	if (res.error) {
		error(502, 'Could not load records from the API.');
	}
	return { records: res.data ?? [] };
};
