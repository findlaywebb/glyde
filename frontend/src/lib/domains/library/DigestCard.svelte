<script lang="ts">
	/**
	 * A single digest card in the library feed.
	 *
	 * Shows the agent-given name as the primary heading (linked to the reader), the memorable
	 * slug in a distinct mono treatment (also linked to the reader), provenance metadata, and
	 * shape badges (word count, reading time, block mix). Takes primitive props only — the page
	 * load flattens the wire `DigestListItemView` before passing data down, keeping this card
	 * blind to IR changes.
	 */
	import { formatBlockMix, formatProvenance, formatReadingTime } from './format';
	import type { DigestCardProps } from './types';

	type Props = DigestCardProps;

	let {
		slug,
		name,
		sourceKind,
		producer,
		createdAt,
		wordCount,
		estReadingMs,
		blocksByKind
	}: Props = $props();

	// The reader route /d/[slug] is created by Wave-3 R-STAGE — it is a valid path the link
	// must produce, but svelte-kit sync does not know the route exists yet, so `resolve()` from
	// $app/paths rejects the template literal with a TS type error. The eslint-disable is
	// intentional and must be removed once R-STAGE lands and the route is registered.
	const readerPath = $derived(`/d/${slug}`);
	const cardId = $derived(`digest-card-${slug}`);
	const readingTime = $derived(formatReadingTime(estReadingMs));
	const blockMix = $derived(formatBlockMix(blocksByKind));
	const provenance = $derived(formatProvenance(sourceKind, producer, createdAt));
</script>

<article
	aria-labelledby={cardId}
	class="rounded-xl border border-border bg-card p-4 transition-colors hover:border-muted-foreground/40"
>
	<header class="mb-2">
		<h2 id={cardId} class="font-ui text-base font-semibold">
			<!-- eslint-disable svelte/no-navigation-without-resolve -->
			<a
				href={readerPath}
				class="text-card-foreground hover:text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
			>
				{name}
			</a>
			<!-- eslint-enable svelte/no-navigation-without-resolve -->
		</h2>
		<!-- eslint-disable svelte/no-navigation-without-resolve -->
		<a
			href={readerPath}
			class="font-mono text-xs text-muted-foreground hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
		>
			{slug}
		</a>
		<!-- eslint-enable svelte/no-navigation-without-resolve -->
	</header>

	<p class="mb-3 font-ui text-xs text-muted-foreground">{provenance}</p>

	<div class="flex flex-wrap items-center gap-2">
		<span class="rounded-full bg-muted px-2.5 py-0.5 font-ui text-xs text-muted-foreground">
			{wordCount} words
		</span>
		<span class="rounded-full bg-muted px-2.5 py-0.5 font-ui text-xs text-muted-foreground">
			{readingTime}
		</span>
		{#if blockMix}
			<span class="rounded-full bg-muted px-2.5 py-0.5 font-ui text-xs text-muted-foreground">
				{blockMix}
			</span>
		{/if}
	</div>
</article>
