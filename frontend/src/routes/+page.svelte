<script lang="ts">
	import type { PageData } from './$types';

	// Components render `data` from `load` and never fetch themselves. Props flow down.
	let { data }: { data: PageData } = $props();
</script>

<main class="mx-auto max-w-2xl p-8">
	<h1 class="text-2xl font-semibold">Glyde</h1>
	<p class="mt-2 text-muted-foreground">
		The typed-seam example: this list is loaded from <code>GET /records</code> through the generated client.
	</p>

	<ul class="mt-6 space-y-2">
		{#each data.records as record (record.id)}
			<li class="rounded-md border border-border bg-card p-3 text-card-foreground">
				<span class="font-medium">{record.name}</span>
				<span class="ml-2 text-sm text-muted-foreground">{record.created_at}</span>
			</li>
		{:else}
			<li class="text-muted-foreground">No records yet.</li>
		{/each}
	</ul>
</main>
