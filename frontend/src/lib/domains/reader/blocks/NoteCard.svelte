<script lang="ts">
	/**
	 * Note card shown when the reader pauses on a `:::pause … :::` directive block.
	 *
	 * Renders `block.content` as rich inline markdown (bold, em, inline-code, links, lists) via
	 * the `marked` library. The `reshown` flag adds a subtle cue ring. A click-to-expand toggle
	 * shows a fuller view with larger type — self-contained within the card (no Reader.svelte
	 * change). The expand affordance is keyboard-accessible: a real `<button>` with `aria-expanded`,
	 * Enter/Space activates natively, visible focus ring.
	 *
	 * Security: `marked` v18 ships no sanitizer, so its output is run through DOMPurify before
	 * `{@html}`. Digests are agent/CLI-authored and the reader is multi-user-hosted, so raw HTML
	 * in the content (`<script>`, `onerror=`, `javascript:` hrefs) is untrusted and must be
	 * stripped. The reader route is CSR-only (`ssr=false`), so DOMPurify's browser-DOM dependency
	 * is satisfied; the jsdom component tests also supply a DOM.
	 */
	import { ChevronDown, ChevronUp } from '@lucide/svelte';
	import Icon from '$lib/components/ui/Icon.svelte';
	import type { BlockCardProps } from '$lib/domains/reader/types';
	import DOMPurify from 'dompurify';
	import { marked } from 'marked';

	let { block, reshown }: BlockCardProps = $props();

	let expanded = $state(false);

	/**
	 * Sanitized markdown HTML. `marked.parse` is synchronous (no async extensions; `{ async: false }`
	 * narrows the return type to `string`), and DOMPurify strips dangerous markup before render.
	 */
	const parsedContent = $derived(DOMPurify.sanitize(marked.parse(block.content, { async: false })));

	function toggleExpand(): void {
		expanded = !expanded;
	}
</script>

<!-- eslint-disable svelte/no-at-html-tags -- content is sanitized with DOMPurify before render (see parsedContent) -->
<article
	aria-label="Note block"
	class="w-full rounded-lg border border-border bg-card text-card-foreground transition-all duration-150 ease-out hover:shadow-md motion-safe:hover:scale-[1.01] {reshown
		? 'ring-2 ring-cue'
		: ''}"
>
	<header class="flex items-center justify-between border-b border-border px-4 py-2">
		<div class="flex items-center gap-2">
			<span class="font-ui text-xs font-medium uppercase tracking-wider text-muted-foreground"
				>note</span
			>
			{#if reshown}
				<span class="font-ui text-xs text-cue">reshown</span>
			{/if}
		</div>
		<button
			type="button"
			class="flex min-h-11 min-w-11 items-center justify-center rounded hover:bg-accent hover:text-accent-foreground focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring"
			aria-label={expanded ? 'Collapse note block' : 'Expand note block'}
			aria-expanded={expanded}
			onclick={toggleExpand}
		>
			<Icon icon={expanded ? ChevronUp : ChevronDown} size={16} />
		</button>
	</header>

	<div
		class="p-4 font-reading leading-relaxed text-card-foreground prose-note {expanded
			? 'text-base'
			: 'text-sm'}"
	>
		{@html parsedContent}
	</div>
</article>

<style>
	/* Minimal prose styling for the note card's rendered markdown. Uses semantic tokens so all
	   three themes (dark / light / sepia) apply correctly. Only targets descendants of .prose-note
	   via :global so it does not leak to sibling components. */

	:global(.prose-note p) {
		margin-bottom: 0.75em;
	}

	:global(.prose-note p:last-child) {
		margin-bottom: 0;
	}

	:global(.prose-note strong) {
		font-weight: 700;
		color: var(--card-foreground);
	}

	:global(.prose-note em) {
		font-style: italic;
	}

	:global(.prose-note code) {
		font-family: var(--font-mono, ui-monospace, monospace);
		font-size: 0.875em;
		background: var(--muted);
		color: var(--card-foreground);
		padding: 0.15em 0.35em;
		border-radius: 0.25rem;
	}

	:global(.prose-note a) {
		color: var(--primary);
		text-decoration: underline;
		text-underline-offset: 2px;
	}

	:global(.prose-note a:hover) {
		opacity: 0.8;
	}

	:global(.prose-note ul),
	:global(.prose-note ol) {
		padding-left: 1.5em;
		margin-bottom: 0.75em;
	}

	:global(.prose-note ul) {
		list-style-type: disc;
	}

	:global(.prose-note ol) {
		list-style-type: decimal;
	}

	:global(.prose-note li) {
		margin-bottom: 0.25em;
	}
</style>
