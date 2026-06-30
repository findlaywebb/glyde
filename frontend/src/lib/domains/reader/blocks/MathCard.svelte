<script lang="ts">
	/**
	 * Static math card shown when the reader pauses on a display math block.
	 *
	 * When `block.linear_form` is present it is shown as a plain-English aside — this is the v1
	 * relief valve: authored linearisation rather than auto-ClearSpeak. When absent the raw math
	 * source (`block.content`) is rendered in monospace. The `reshown` flag adds a subtle cue ring.
	 * Binds no keys and registers no listeners.
	 */
	import type { BlockCardProps } from '$lib/domains/reader/types';

	let { block, reshown }: BlockCardProps = $props();

	const hasLinear = $derived(!!block.linear_form);
</script>

<article
	aria-label="Math block"
	class="w-full rounded-lg border border-border bg-card text-card-foreground {reshown
		? 'ring-2 ring-cue'
		: ''}"
>
	<header class="flex items-center gap-2 border-b border-border px-4 py-2">
		<span class="font-ui text-xs font-medium uppercase tracking-wider text-muted-foreground"
			>math</span
		>
		{#if reshown}
			<span class="font-ui text-xs text-cue">reshown</span>
		{/if}
	</header>

	<div class="p-4">
		{#if hasLinear}
			<!-- Linear form: spoken/readable aside -->
			<p class="font-ui text-base leading-relaxed text-card-foreground">{block.linear_form}</p>
			<p class="mt-2 font-mono text-sm text-muted-foreground" aria-label="Raw math source">
				{block.content}
			</p>
		{:else}
			<!-- Raw math source in monospace -->
			<pre
				class="overflow-x-auto whitespace-pre font-mono text-sm leading-relaxed text-reading-foreground">{block.content}</pre>
		{/if}
	</div>
</article>
