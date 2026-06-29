/**
 * dependency-cruiser — the second half of the boundary contract (with
 * eslint-plugin-boundaries). It owns cycle detection and the inward-direction
 * forbids: dependencies point inward (routes → domains → {ui, api} → utils), so a
 * lower layer importing a higher one is an error. $lib aliases resolve via tsconfig.
 *
 * @type {import('dependency-cruiser').IConfiguration}
 */
module.exports = {
	forbidden: [
		{
			name: 'no-circular',
			comment: 'No import cycles.',
			severity: 'error',
			from: { pathNot: '^(node_modules|\\.svelte-kit)' },
			to: { circular: true }
		},
		{
			name: 'utils-is-a-sink',
			comment: 'utils imports nothing from other elements.',
			severity: 'error',
			from: { path: '^src/lib/utils(\\.ts$|/)' },
			to: { path: '^(src/routes/|src/lib/(api|components|domains)/)' }
		},
		{
			name: 'api-points-inward',
			comment: 'api may not import routes, ui, or domains.',
			severity: 'error',
			from: { path: '^src/lib/api/' },
			to: { path: '^(src/routes/|src/lib/(components|domains)/)' }
		},
		{
			name: 'ui-points-inward',
			comment: 'ui may import only utils (not routes, api, or domains).',
			severity: 'error',
			from: { path: '^src/lib/components/' },
			to: { path: '^(src/routes/|src/lib/(api|domains)/)' }
		},
		{
			name: 'ignore-svelte-internal',
			severity: 'ignore',
			from: {},
			to: { path: 'svelte/internal' }
		}
	],
	options: {
		tsConfig: { fileName: 'tsconfig.json' },
		enhancedResolveOptions: { extensions: ['.ts', '.js', '.svelte', '.json'] },
		doNotFollow: { path: 'node_modules' },
		exclude: { path: '^(\\.svelte-kit|node_modules)' }
	}
};
