<script lang="ts">
	/**
	 * Static code card shown when the reader pauses on a fenced code block.
	 *
	 * Renders the raw `block.content` in monospace with a language label. On mobile the content
	 * scrolls horizontally by default; a wrap toggle switches to line-wrapping for accessibility.
	 * The `reshown` flag adds a subtle "reshown" affordance (ring + label) when the user replays
	 * the card via ArrowLeft. Binds no keys and registers no listeners.
	 */
	import type { BlockCardProps } from '$lib/domains/reader/types';

	let { block, reshown }: BlockCardProps = $props();

	let wrap = $state(false);
</script>

<article
	aria-label={block.lang ? `Code block: ${block.lang}` : 'Code block'}
	class="w-full rounded-lg border border-border bg-card text-card-foreground {reshown
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
		<div class="flex items-center gap-2">
			{#if reshown}
				<span class="font-ui text-xs text-cue">reshown</span>
			{/if}
			<button
				type="button"
				class="min-h-11 min-w-11 rounded px-2 py-1 font-ui text-xs text-muted-foreground hover:bg-accent hover:text-accent-foreground focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring"
				aria-pressed={wrap}
				onclick={() => {
					wrap = !wrap;
				}}
			>
				{wrap ? 'scroll' : 'wrap'}
			</button>
		</div>
	</header>
	<div class="overflow-x-auto">
		<pre
			class="p-4 font-mono text-sm leading-relaxed text-reading-foreground {wrap
				? 'whitespace-pre-wrap'
				: 'whitespace-pre'}">{block.content}</pre>
	</div>
</article>
