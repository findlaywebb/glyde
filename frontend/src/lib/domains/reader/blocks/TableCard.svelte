<script lang="ts">
	/**
	 * Table card shown when the reader pauses on a markdown pipe table.
	 *
	 * Parses the raw markdown table in `block.content` (pipe-delimited rows; the second separator
	 * row is skipped). Renders with zebra striping and generous spacing. On wide viewports the
	 * table renders as a standard grid; on narrow (mobile) viewports it switches to a stacked
	 * "header: value" card layout. The `reshown` flag adds a subtle cue ring when the user
	 * replays the card. A click-to-expand toggle shows a fuller view — self-contained within the
	 * card (no Reader.svelte change). The expand affordance is keyboard-accessible: a real
	 * `<button>` with `aria-expanded`, Enter/Space activates natively, visible focus ring.
	 */
	import { ChevronDown, ChevronUp } from '@lucide/svelte';
	import Icon from '$lib/components/ui/Icon.svelte';
	import type { BlockCardProps } from '$lib/domains/reader/types';

	let { block, reshown }: BlockCardProps = $props();

	let expanded = $state(false);

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

	function toggleExpand(): void {
		expanded = !expanded;
	}
</script>

<article
	aria-label="Table block"
	class="w-full rounded-lg border border-border bg-card text-card-foreground transition-all duration-150 ease-out hover:shadow-md motion-safe:hover:scale-[1.01] {reshown
		? 'ring-2 ring-cue'
		: ''}"
>
	<header class="flex items-center justify-between border-b border-border px-4 py-2">
		<div class="flex items-center gap-2">
			<span class="font-ui text-xs font-medium uppercase tracking-wider text-muted-foreground"
				>table</span
			>
			{#if reshown}
				<span class="font-ui text-xs text-cue">reshown</span>
			{/if}
		</div>
		<button
			type="button"
			class="flex min-h-11 min-w-11 items-center justify-center rounded hover:bg-accent hover:text-accent-foreground focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring"
			aria-label={expanded ? 'Collapse table block' : 'Expand table block'}
			aria-expanded={expanded}
			onclick={toggleExpand}
		>
			<Icon icon={expanded ? ChevronUp : ChevronDown} size={16} />
		</button>
	</header>

	<div class="p-4 {expanded ? 'pb-6' : ''}">
		{#if parsed.headers.length > 0}
			<!-- Wide: grid table — zebra striping, generous column padding, overflow scroll -->
			<div class="{expanded ? 'block' : 'hidden sm:block'} overflow-x-auto">
				<table class="w-full border-collapse font-ui text-sm">
					<thead>
						<tr class="border-b-2 border-border">
							{#each parsed.headers as header, hi (hi)}
								<th class="px-4 py-3 text-left font-semibold text-card-foreground">{header}</th>
							{/each}
						</tr>
					</thead>
					<tbody>
						{#each parsed.rows as row, ri (ri)}
							<tr class="border-b border-border last:border-0 {ri % 2 === 1 ? 'bg-muted/40' : ''}">
								{#each row as cell, ci (ci)}
									<td class="px-4 py-3 text-card-foreground">{cell}</td>
								{/each}
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<!-- Narrow: stacked header: value cards — hidden in expanded mode (grid takes over) -->
			{#if !expanded}
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
			{/if}
		{:else}
			<p class="font-ui text-sm text-muted-foreground">No table data</p>
		{/if}
	</div>
</article>
