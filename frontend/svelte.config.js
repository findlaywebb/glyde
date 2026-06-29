import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	// adapter-node: the Node server is the single public front door — it serves the UI and
	// reverse-proxies `/api/*` to FastAPI via `hooks.server.ts`.
	kit: { adapter: adapter() },
	// Runes mode project-wide (Svelte 5). Removable in Svelte 6, where it is the default.
	compilerOptions: { runes: true }
};

export default config;
