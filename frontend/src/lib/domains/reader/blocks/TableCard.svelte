<script lang="ts">
	/**
	 * Static table card shown when the reader pauses on a markdown pipe table.
	 *
	 * Parses the raw markdown table in `block.content` (pipe-delimited rows; the second separator
	 * row is skipped). On wide viewports the table renders as a standard grid; on narrow (mobile)
	 * viewports it switches to a stacked "header: value" card layout. The `reshown` flag adds a
	 * subtle cue ring when the user replays the card. Binds no keys and registers no listeners.
	 */
	import type { BlockCardProps } from '$lib/domains/reader/types';

	let { block, reshown }: BlockCardProps = $props();

	/** Parse a pipe-table row into trimmed cell strings. */
	function parseCells(line: string): string[] {
		return line
			.split('|')
			.map((c) => c.trim())
			.filter((_, i, arr) => i > 0 && i < arr.length - 1);
	}

	/** Return true when a line is the separator row (all cells are `---` variants). */
	function isSeparator(line: string): boolean {
		const cells = parseCells(line);
		return cells.length > 0 && cells.every((c) => /^:?-+:?$/.test(c));
	}

	interface ParsedTable {
		headers: string[];
		rows: string[][];
	}

	const parsed = $derived.by((): ParsedTable => {
		const lines = block.content
			.split('\n')
			.map((l) => l.trim())
			.filter((l) => l.startsWith('|'));
		const headers: string[] = [];
		const rows: string[][] = [];
		let headerDone = false;
		for (const line of lines) {
			if (isSeparator(line)) {
				headerDone = true;
				continue;
			}
			const cells = parseCells(line);
			if (!headerDone) {
				headers.push(...cells);
			} else {
				rows.push(cells);
			}
		}
		return { headers, rows };
	});
</script>

<article
	aria-label="Table block"
	class="w-full rounded-lg border border-border bg-card text-card-foreground {reshown
		? 'ring-2 ring-cue'
		: ''}"
>
	<header class="flex items-center gap-2 border-b border-border px-4 py-2">
		<span class="font-ui text-xs font-medium uppercase tracking-wider text-muted-foreground"
			>table</span
		>
		{#if reshown}
			<span class="font-ui text-xs text-cue">reshown</span>
		{/if}
	</header>

	<div class="p-4">
		{#if parsed.headers.length > 0}
			<!-- Wide: grid table — hidden on narrow screens via sm: prefix -->
			<div class="hidden sm:block overflow-x-auto">
				<table class="w-full border-collapse font-ui text-sm">
					<thead>
						<tr>
							{#each parsed.headers as header, hi (hi)}
								<th
									class="border-b border-border px-3 py-2 text-left font-semibold text-card-foreground"
									>{header}</th
								>
							{/each}
						</tr>
					</thead>
					<tbody>
						{#each parsed.rows as row, ri (ri)}
							<tr class="border-b border-border last:border-0">
								{#each row as cell, ci (ci)}
									<td class="px-3 py-2 text-card-foreground">{cell}</td>
								{/each}
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<!-- Narrow: stacked header: value cards -->
			<div class="block sm:hidden space-y-3" aria-label="Stacked table view">
				{#each parsed.rows as row, ri (ri)}
					<dl class="rounded border border-border">
						{#each parsed.headers as header, i (i)}
							<div class="flex gap-2 border-b border-border px-3 py-2 last:border-0">
								<dt class="min-w-0 shrink-0 font-semibold text-muted-foreground">{header}:</dt>
								<dd class="min-w-0 flex-1 text-card-foreground">{row[i] ?? ''}</dd>
							</div>
						{/each}
					</dl>
				{/each}
			</div>
		{:else}
			<p class="font-ui text-sm text-muted-foreground">No table data</p>
		{/if}
	</div>
</article>
