import prettier from 'eslint-config-prettier';
import path from 'node:path';
import js from '@eslint/js';
import boundaries from 'eslint-plugin-boundaries';
import svelte from 'eslint-plugin-svelte';
import { defineConfig, includeIgnoreFile } from 'eslint/config';
import globals from 'globals';
import ts from 'typescript-eslint';

const gitignorePath = path.resolve(import.meta.dirname, '.gitignore');

export default defineConfig(
	includeIgnoreFile(gitignorePath),
	js.configs.recommended,
	ts.configs.recommended,
	svelte.configs.recommended,
	prettier,
	svelte.configs.prettier,
	{
		languageOptions: { globals: { ...globals.browser, ...globals.node } },
		rules: {
			// typescript-eslint strongly recommend not using no-undef on TypeScript projects.
			'no-undef': 'off'
		}
	},
	{
		files: ['**/*.svelte', '**/*.svelte.ts', '**/*.svelte.js'],
		languageOptions: {
			parserOptions: {
				projectService: true,
				extraFileExtensions: ['.svelte'],
				parser: ts.parser
			}
		}
	},
	// Architecture boundaries — the frontend mirror of the backend's import-linter contract.
	// Dependencies point inward: routes → {domains, ui, api}, domains → {ui, api, utils},
	// ui → {utils}; utils and api are sinks. Paired with dependency-cruiser's no-circular rule.
	{
		plugins: { boundaries },
		settings: {
			'import/resolver': { typescript: { project: './tsconfig.json' } },
			'boundaries/elements': [
				{ type: 'routes', pattern: 'src/routes/**', mode: 'full' },
				{ type: 'domains', pattern: 'src/lib/domains/**', mode: 'full' },
				{ type: 'ui', pattern: 'src/lib/components/**', mode: 'full' },
				{ type: 'api', pattern: 'src/lib/api/**', mode: 'full' },
				{ type: 'utils', pattern: ['src/lib/utils/**', 'src/lib/utils.ts'], mode: 'full' }
			],
			'boundaries/ignore': ['**/*.test.ts', '**/*.spec.ts']
		},
		rules: {
			'boundaries/dependencies': [
				'error',
				{
					default: 'disallow',
					rules: [
						{
							from: { type: 'routes' },
							allow: [
								{ to: { type: 'routes' } },
								{ to: { type: 'domains' } },
								{ to: { type: 'ui' } },
								{ to: { type: 'api' } }
							]
						},
						{
							from: { type: 'domains' },
							allow: [
								{ to: { type: 'domains' } },
								{ to: { type: 'ui' } },
								{ to: { type: 'api' } },
								{ to: { type: 'utils' } }
							]
						},
						{ from: { type: 'ui' }, allow: [{ to: { type: 'ui' } }, { to: { type: 'utils' } }] },
						{ from: { type: 'api' }, allow: [{ to: { type: 'api' } }] },
						{ from: { type: 'utils' }, allow: [{ to: { type: 'utils' } }] }
					]
				}
			]
		}
	}
);
