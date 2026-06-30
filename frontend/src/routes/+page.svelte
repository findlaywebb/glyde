<script lang="ts">
	/**
	 * Library home — the root route restored by LIB after F0 deleted the template page.
	 *
	 * Renders the newest-first digest feed. Each item is a `DigestCard` receiving primitive
	 * props flattened from the wire `DigestListItemView` — the card stays blind to the IR
	 * shape. An empty-state prompt is shown when no digests have been added yet.
	 */
	import type { PageProps } from './$types';
	import type { components } from '$lib/api/schema';
	import DigestCard from '$lib/domains/library/DigestCard.svelte';
	import type { DigestCardProps } from '$lib/domains/library/types';

	type DigestListItem = components['schemas']['DigestListItemView'];

	let { data }: PageProps = $props();

	/** Flatten a wire list item to primitive card props (insulates the card from IR churn). */
	function toCardProps(item: DigestListItem): DigestCardProps {
		return {
			slug: item.meta.slug,
			name: item.meta.name,
			sourceKind: item.meta.provenance.source_kind,
			producer: item.meta.provenance.producer ?? null,
			createdAt: item.meta.created_at,
			wordCount: item.counts.words,
			estReadingMs: item.meta.est_reading_ms,
			blocksByKind: item.counts.blocks_by_kind
		};
	}
</script>

<svelte:head>
	<title>Glyde — Library</title>
</svelte:head>

<main class="mx-auto max-w-lg px-4 py-6">
	<header class="mb-6">
		<h1 class="font-ui text-xl font-bold text-foreground">Library</h1>
		<p class="font-ui text-sm text-muted-foreground">Your digest collection, newest first.</p>
	</header>

	{#if data.digests.length === 0}
		<div class="rounded-xl border border-dashed border-border py-12 text-center">
			<p class="font-ui text-sm text-muted-foreground">No digests yet.</p>
			<p class="mt-1 font-mono text-xs text-muted-foreground">
				Run <code class="font-mono">glyde add</code> to create one.
			</p>
		</div>
	{:else}
		<ul class="flex flex-col gap-3" aria-label="Digest library">
			{#each data.digests as item (item.meta.slug)}
				<li>
					<DigestCard {...toCardProps(item)} />
				</li>
			{/each}
		</ul>
	{/if}
</main>
