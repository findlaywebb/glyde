<script lang="ts">
	/**
	 * Static quote card shown when the reader pauses on a blockquote block.
	 *
	 * Renders `block.content` as a styled blockquote. The `reshown` flag adds a subtle cue ring.
	 * Binds no keys and registers no listeners.
	 */
	import type { BlockCardProps } from '$lib/domains/reader/types';

	let { block, reshown }: BlockCardProps = $props();
</script>

<article
	aria-label="Quote block"
	class="w-full rounded-lg border border-border bg-card text-card-foreground {reshown
		? 'ring-2 ring-cue'
		: ''}"
>
	<header class="flex items-center gap-2 border-b border-border px-4 py-2">
		<span class="font-ui text-xs font-medium uppercase tracking-wider text-muted-foreground"
			>quote</span
		>
		{#if reshown}
			<span class="font-ui text-xs text-cue">reshown</span>
		{/if}
	</header>

	<div class="p-4">
		<blockquote
			class="border-l-4 border-primary pl-4 font-reading text-base italic leading-relaxed text-card-foreground"
		>
			{block.content}
		</blockquote>
	</div>
</article>
