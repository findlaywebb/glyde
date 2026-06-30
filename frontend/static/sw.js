// Glyde service worker — a classic, shell-cache-only worker with one narrow read-cache.
//
// Served verbatim from /static (a classic worker, not the SvelteKit `src/service-worker`
// module, not TS), registered at `/sw.js` by the app shell. It runs only in a secure context
// (HTTPS-over-LAN or localhost); over a plain-HTTP LAN origin registration is skipped and this
// file never executes, which is correct.
//
// The load-bearing property: `/api/*` is a genuine passthrough whose check is FIRST, so a cache
// miss can never shadow a live API read or mutation. The single deliberate exception is a narrow
// read-through cache for `GET /api/digests/{slug}` (the Digest IR) — stale-while-revalidate under
// a versioned key, checked *before* the general `/api` passthrough — so a digest reads instantly
// offline while always revalidating against the network. The list, preferences, and every
// mutation stay passthrough. Beyond `/api`, only content-hashed immutable build assets are
// cached; HTML navigations never are (SSR must reflect live state).

const SHELL_CACHE = 'glyde-shell-v1';
const DIGEST_CACHE = 'glyde-digest-v1';
const IMMUTABLE_PREFIX = '/_app/immutable/';
// GET /api/digests/{slug} only — one path segment, so the `/api/digests` list never matches.
const DIGEST_READ = /^\/api\/digests\/[^/]+$/;

self.addEventListener('install', () => {
	self.skipWaiting();
});

self.addEventListener('activate', (event) => {
	event.waitUntil(
		(async () => {
			const keep = new Set([SHELL_CACHE, DIGEST_CACHE]);
			const names = await caches.keys();
			await Promise.all(names.filter((name) => !keep.has(name)).map((name) => caches.delete(name)));
			await self.clients.claim();
		})()
	);
});

self.addEventListener('fetch', (event) => {
	const response = route(event);
	if (response) {
		event.respondWith(response);
	}
});

// Return a Response promise to serve, or `undefined` to let the request pass through untouched.
function route(event) {
	const url = new URL(event.request.url);

	// FIRST: anything under /api is a passthrough — except the one cached digest read.
	if (url.pathname === '/api' || url.pathname.startsWith('/api/')) {
		if (event.request.method === 'GET' && DIGEST_READ.test(url.pathname)) {
			return staleWhileRevalidate(event);
		}
		return undefined;
	}

	if (event.request.method !== 'GET' || url.origin !== self.location.origin) {
		return undefined;
	}
	const accept = event.request.headers.get('accept') || '';
	if (event.request.mode === 'navigate' || accept.includes('text/html')) {
		return undefined; // never cache HTML navigations — SSR reflects live state
	}
	if (url.pathname.startsWith(IMMUTABLE_PREFIX)) {
		return cacheFirst(event.request);
	}
	return undefined;
}

// Content-hashed immutable assets: serve from cache, fall back to network and cache on first use.
async function cacheFirst(request) {
	const cache = await caches.open(SHELL_CACHE);
	const hit = await cache.match(request);
	if (hit) {
		return hit;
	}
	const response = await fetch(request);
	if (response.ok) {
		cache.put(request, response.clone());
	}
	return response;
}

// The Digest IR: serve the cached copy instantly when present, always revalidate in the
// background; on a cold cache, await the network.
async function staleWhileRevalidate(event) {
	const cache = await caches.open(DIGEST_CACHE);
	const cached = await cache.match(event.request);
	const network = fetch(event.request).then((response) => {
		if (response.ok) {
			cache.put(event.request, response.clone());
		}
		return response;
	});
	if (cached) {
		event.waitUntil(network.catch(() => undefined));
		return cached;
	}
	return network;
}
