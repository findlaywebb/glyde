<script lang="ts">
	/**
	 * Static image card shown when the reader pauses on an image block.
	 *
	 * Renders `block.content` as the `src` with `block.alt` as the accessible alt text. If the
	 * image fails to load, the card falls back to displaying the alt text as readable text. The
	 * `reshown` flag adds a subtle cue ring. Binds no keys and registers no listeners.
	 */
	import type { BlockCardProps } from '$lib/domains/reader/types';

	let { block, reshown }: BlockCardProps = $props();

	let imgFailed = $state(false);

	/** Accessible alt text: prefer the authored `block.alt`; never fall back to a raw URL. */
	const altText = $derived(block.alt ?? '');
</script>

<article
	aria-label={altText ? `Image: ${altText}` : 'Image block'}
	class="w-full rounded-lg border border-border bg-card text-card-foreground {reshown
		? 'ring-2 ring-cue'
		: ''}"
>
	<header class="flex items-center gap-2 border-b border-border px-4 py-2">
		<span class="font-ui text-xs font-medium uppercase tracking-wider text-muted-foreground"
			>image</span
		>
		{#if reshown}
			<span class="font-ui text-xs text-cue">reshown</span>
		{/if}
	</header>

	<div class="p-4">
		{#if imgFailed || !block.content}
			<!-- Fallback: show alt text when the image can't load -->
			<figure
				class="font-ui text-sm italic text-muted-foreground"
				role="img"
				aria-label={altText || 'Image unavailable'}
			>
				{altText || '(no image)'}
			</figure>
		{:else}
			<img
				src={block.content}
				alt={altText}
				class="max-h-96 w-full rounded object-contain"
				onerror={() => {
					imgFailed = true;
				}}
			/>
		{/if}
	</div>
</article>
