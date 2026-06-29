import createClient from 'openapi-fetch';
import type { paths } from './schema';

/**
 * The typed API client.
 *
 * `paths` is generated from the committed `docs/schemas/openapi.json` (run `npm run gen:api`
 * after the backend's `export-openapi`), so every call is checked against the FastAPI
 * contract — the frontend cannot drift from the API without a TypeScript error. A
 * module-level client is a stateless wrapper; pass SvelteKit's per-request `fetch` into each
 * call from `load` so cookies and relative-URL handling are preserved, and branch on
 * `{ data, error }` (a 200 is not success; non-2xx is returned, not thrown).
 *
 * Same-origin serving: the API is reached under `/api`, proxied to FastAPI by
 * `hooks.server.ts`. The module base is the relative `/api`, which is what the **browser**
 * uses. An **SSR `load`** can't use a relative base (openapi-fetch builds `new Request(base +
 * path)` before the provided `fetch` runs, and a relative URL has no origin in Node) — so
 * each `load` overrides the per-call `baseUrl` to an absolute, same-origin `${url.origin}/api`,
 * which `event.fetch` re-enters through the proxy.
 *
 * NOTE: `./schema` is generated and git-ignored on a fresh scaffold — run the backend's
 * `export-openapi` then `npm run gen:api` before this import resolves.
 */
export const api = createClient<paths>({ baseUrl: '/api' });
