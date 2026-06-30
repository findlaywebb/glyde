<script lang="ts">
	/**
	 * The "block ahead" accent chip — shown during the last prose words before a block pause.
	 *
	 * Pure presentational: renders a small labelled chip when `visible` is true, disappears when
	 * false. The chip label is "{kind} ahead" (e.g. "code ahead", "table ahead"). Uses the `cue`
	 * semantic token (§5.8) — a reserved reading colour for block-ahead signalling only. Binds no
	 * keys and registers no listeners; the engine's `blockAhead` state (§5.7) drives `visible`.
	 */
	import type { BlockAheadCueProps } from '$lib/domains/reader/types';

	let { kind, visible }: BlockAheadCueProps = $props();

	const label = $derived(`${kind} ahead`);
</script>

{#if visible}
	<span
		role="status"
		aria-live="polite"
		aria-label={label}
		class="inline-flex items-center gap-1 rounded-full border border-cue/30 bg-cue/10 px-2.5 py-0.5 font-ui text-xs font-medium text-cue"
	>
		{label}
	</span>
{/if}
