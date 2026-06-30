<script lang="ts">
	/**
	 * Reader route error boundary — R-STAGE owns. Renders the not-found / failure state for a
	 * `/d/{slug}` whose `load` threw (404 when the digest does not exist, 502 when the API is
	 * unreachable). Kept terse and skimmable for the dyslexia-first reader: a status line, the
	 * server-provided message, and a way back to the library.
	 */
	import { page } from '$app/state';
	import { resolve } from '$app/paths';

	const isMissing = $derived(page.status === 404);
</script>

<svelte:head><title>{isMissing ? 'Not found' : 'Error'} · Glyde</title></svelte:head>

<main
	class="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-4 px-6 text-center font-ui"
>
	<p class="text-5xl font-bold tabular-nums text-muted-foreground">{page.status}</p>
	<h1 class="text-lg font-semibold text-foreground">
		{isMissing ? 'Digest not found' : 'Could not open this digest'}
	</h1>
	<p class="text-sm text-muted-foreground">{page.error?.message}</p>
	<a
		href={resolve('/')}
		class="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition hover:opacity-90 focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none"
		>Back to library</a
	>
</main>
