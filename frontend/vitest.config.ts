import { sveltekit } from '@sveltejs/kit/vite';
import { svelteTesting } from '@testing-library/svelte/vite';
import { defineConfig } from 'vitest/config';

// Two test projects, one runner. The `unit` project keeps the `load`-function tests in a
// plain node env (no DOM); the `component` project runs Testing Library against real Svelte
// components under jsdom. Splitting by filename (`*.component.test.ts`) keeps each suite in
// the right environment — a load test must not pull in jsdom, and a component test must not
// run in node. `resolve.conditions: ['browser']` selects Svelte's browser build in both, so
// component internals (and `flushSync`) behave consistently.
export default defineConfig({
	plugins: [sveltekit()],
	resolve: process.env.VITEST ? { conditions: ['browser'] } : undefined,
	test: {
		projects: [
			{
				plugins: [sveltekit()],
				resolve: { conditions: ['browser'] },
				test: {
					name: 'unit',
					environment: 'node',
					include: ['src/**/*.{test,spec}.ts'],
					exclude: ['src/**/*.component.{test,spec}.ts']
				}
			},
			{
				plugins: [sveltekit(), svelteTesting()],
				resolve: { conditions: ['browser'] },
				test: {
					name: 'component',
					environment: 'jsdom',
					include: ['src/**/*.component.{test,spec}.ts'],
					setupFiles: ['./src/test-setup.ts']
				}
			}
		]
	}
});
