<script lang="ts">
	/**
	 * Static note card shown when the reader pauses on a `:::pause … :::` directive block.
	 *
	 * Renders `block.content` as a callout note — an arbitrary pause where the author wants the
	 * reader to stop and absorb something before continuing. The `reshown` flag adds a subtle cue
	 * ring. Binds no keys and registers no listeners.
	 */
	import type { BlockCardProps } from '$lib/domains/reader/types';

	let { block, reshown }: BlockCardProps = $props();
</script>

<article
	aria-label="Note block"
	class="w-full rounded-lg border border-border bg-card text-card-foreground {reshown
		? 'ring-2 ring-cue'
		: ''}"
>
	<header class="flex items-center gap-2 border-b border-border px-4 py-2">
		<span class="font-ui text-xs font-medium uppercase tracking-wider text-muted-foreground"
			>note</span
		>
		{#if reshown}
			<span class="font-ui text-xs text-cue">reshown</span>
		{/if}
	</header>

	<div class="p-4">
		<p class="font-reading text-base leading-relaxed text-card-foreground">{block.content}</p>
	</div>
</article>
