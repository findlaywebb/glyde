<script lang="ts">
	/**
	 * Code card shown when the reader pauses on a fenced code block.
	 *
	 * Renders `block.content` with syntax highlighting keyed on `block.lang` (highlight.js, core
	 * bundle with a restricted language set for bundle efficiency). Falls back to plain monospace
	 * when the lang is absent or unrecognised. Supports a wrap/scroll toggle and a click-to-expand
	 * full view that is self-contained — no Reader.svelte change is required. The expand affordance
	 * is keyboard-accessible: a real `<button>` with `aria-expanded`, Enter/Space activates natively,
	 * visible focus ring.
	 *
	 * Theming: highlight.js token classes are styled in `hljs-theme.css` (imported as a Vite CSS
	 * module), mapped to Glyde semantic tokens so all three themes (dark / light / sepia) resolve
	 * correctly at runtime via CSS custom properties.
	 *
	 * Highlighter choice (shiki vs highlight.js): highlight.js core + 11 language files ≈ 30–40 KB
	 * gzipped vs shiki's 100 KB+ baseline. For this restricted set (py/js/ts/bash/json/html/css/md/
	 * sql/rust/go), highlight.js is the lighter option.
	 */
	import { ChevronDown, ChevronUp } from '@lucide/svelte';
	import Icon from '$lib/components/ui/Icon.svelte';
	import type { BlockCardProps } from '$lib/domains/reader/types';
	import './hljs-theme.css';
	import hljs from 'highlight.js/lib/core';
	import python from 'highlight.js/lib/languages/python';
	import javascript from 'highlight.js/lib/languages/javascript';
	import typescript from 'highlight.js/lib/languages/typescript';
	import bash from 'highlight.js/lib/languages/bash';
	import json from 'highlight.js/lib/languages/json';
	import xml from 'highlight.js/lib/languages/xml';
	import css from 'highlight.js/lib/languages/css';
	import markdown from 'highlight.js/lib/languages/markdown';
	import sql from 'highlight.js/lib/languages/sql';
	import rust from 'highlight.js/lib/languages/rust';
	import go from 'highlight.js/lib/languages/go';

	// Register once at module load — aliases (e.g. 'py', 'js', 'ts', 'sh', 'rs') are included
	// automatically from each language's aliases array.
	hljs.registerLanguage('python', python);
	hljs.registerLanguage('javascript', javascript);
	hljs.registerLanguage('typescript', typescript);
	hljs.registerLanguage('bash', bash);
	hljs.registerLanguage('json', json);
	hljs.registerLanguage('xml', xml);
	hljs.registerLanguage('css', css);
	hljs.registerLanguage('markdown', markdown);
	hljs.registerLanguage('sql', sql);
	hljs.registerLanguage('rust', rust);
	hljs.registerLanguage('go', go);

	let { block, reshown }: BlockCardProps = $props();

	let wrap = $state(false);
	let expanded = $state(false);

	/**
	 * Highlighted HTML string, or null when lang is absent or unrecognised.
	 * Falls back to plain text rendering in the template.
	 */
	const highlighted = $derived.by((): string | null => {
		if (!block.lang) return null;
		const lang = block.lang.toLowerCase();
		if (!hljs.getLanguage(lang)) return null;
		try {
			return hljs.highlight(block.content, { language: lang }).value;
		} catch (err) {
			console.warn('[CodeCard] highlight.js failed for lang', lang, err);
			return null;
		}
	});

	function toggleExpand(): void {
		expanded = !expanded;
	}
</script>

<!-- eslint-disable svelte/no-at-html-tags -- highlight.js escapes all HTML before injecting span elements; the at-html template tag is safe here -->
<article
	aria-label={block.lang ? `Code block: ${block.lang}` : 'Code block'}
	class="w-full rounded-lg border border-border bg-card text-card-foreground transition-all duration-150 ease-out hover:shadow-md motion-safe:hover:scale-[1.01] {reshown
		? 'ring-2 ring-cue'
		: ''}"
>
	<header class="flex items-center justify-between border-b border-border px-4 py-2">
		<div class="flex items-center gap-2">
			<span class="font-ui text-xs font-medium uppercase tracking-wider text-muted-foreground"
				>code</span
			>
			{#if block.lang}
				<span class="font-mono text-xs text-muted-foreground">{block.lang}</span>
			{/if}
		</div>
		<div class="flex items-center gap-1">
			{#if reshown}
				<span class="font-ui text-xs text-cue">reshown</span>
			{/if}
			<button
				type="button"
				class="min-h-11 min-w-11 rounded px-2 py-1 font-ui text-xs text-muted-foreground hover:bg-accent hover:text-accent-foreground focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring"
				aria-label="Word wrap"
				aria-pressed={wrap}
				onclick={() => {
					wrap = !wrap;
				}}
			>
				{wrap ? 'scroll' : 'wrap'}
			</button>
			<button
				type="button"
				class="flex min-h-11 min-w-11 items-center justify-center rounded hover:bg-accent hover:text-accent-foreground focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring"
				aria-label={expanded ? 'Collapse code block' : 'Expand code block'}
				aria-expanded={expanded}
				onclick={toggleExpand}
			>
				<Icon icon={expanded ? ChevronUp : ChevronDown} size={16} />
			</button>
		</div>
	</header>
	<div class="overflow-x-auto overflow-y-auto {expanded ? '' : 'max-h-64'}">
		<pre
			class="p-4 font-mono text-sm leading-relaxed text-reading-foreground {wrap
				? 'whitespace-pre-wrap'
				: 'whitespace-pre'}">{#if highlighted}<span class="sr-only">{block.content}</span><span
					aria-hidden="true">{@html highlighted}</span
				>{:else}{block.content}{/if}</pre>
	</div>
</article>
