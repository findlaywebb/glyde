import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

// Adapter and compiler options live in svelte.config.js (the conventional location the
// SvelteKit ecosystem — knip, dependency-cruiser, editors — expects).
//
// Dev unification: `npm run dev` proxies `/api` → FastAPI, mirroring the prod
// `hooks.server.ts` front door, so the browser is same-origin in dev too (no CORS). This is
// dev-only — the prod path runs the built `node build` server (the hooks proxy), never the
// Vite dev server. Read from `process.env` (plain Node at config-eval, before any Kit
// runtime — `$env/dynamic/private` is unavailable here).
const apiOrigin = process.env.GLYDE_API_ORIGIN ?? 'http://127.0.0.1:8000';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		proxy: {
			// Anchored regex (matches `/api` and `/api/…`, not `/apiary`) to mirror the prod
			// `hooks.server.ts` boundary exactly; strip `/api` before forwarding.
			'^/api(/|$)': {
				target: apiOrigin,
				changeOrigin: true,
				rewrite: (path) => path.replace(/^\/api/, '')
			}
		}
	}
});
