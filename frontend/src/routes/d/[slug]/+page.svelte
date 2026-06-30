<script lang="ts">
	/**
	 * Reader route page — R-STAGE owns. Thin orchestration over the composing `Reader.svelte`.
	 *
	 * Owns the PREF store lifecycle (§5.10): it constructs `createPrefsStore` (whose first paint
	 * reads the localStorage mirror synchronously, restoring the last-used mode) and reconciles it
	 * from the server on mount. The store is injected into `Reader`, which constructs the engine and
	 * wires the modes/blocks/chrome. The reader is keyed on the slug so navigating to another digest
	 * remounts the engine cleanly (assay's `{#key}` remount discipline).
	 */
	import { browser } from '$app/environment';
	import { createPrefsStore } from '$lib/domains/preferences/prefs.svelte';
	import Reader from '$lib/domains/reader/Reader.svelte';
	import type { PageProps } from './$types';

	let { data }: PageProps = $props();

	const store = createPrefsStore();

	// Client-only reconcile from the server (source of truth). `reload()` reads no reactive state
	// in a tracked way (§5.10), so this runs once on mount, not on every `store.current` change.
	$effect(() => {
		if (browser) void store.reload();
	});
</script>

<svelte:head><title>{data.digest.meta.name} · Glyde</title></svelte:head>

{#key data.digest.meta.slug}
	<Reader segments={data.digest.segments} title={data.digest.meta.name} {store} />
{/key}
